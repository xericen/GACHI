import time

Types = wiz.model("ai_harness/types")
InputNormalizer = wiz.model("ai_harness/input")
ToolRegistry = wiz.model("ai_harness/tools/registry")


class AgentHarness:
    def __init__(self, config, retry_policy, logger, input_normalizer=None):
        self.config = config
        self.retry_policy = retry_policy
        self.logger = logger
        self.input_normalizer = input_normalizer or InputNormalizer()
        self.tools = ToolRegistry(config.tools)

    def run(self, prompt, history):
        run_id = self.logger.new_run_id()
        started = time.monotonic()
        normalized = self.input_normalizer.normalize(prompt, history, self.config)
        messages = self._build_messages(normalized)
        tool_logs = []
        model_calls = {"count": 0}
        self.logger.emit(
            "agent_run_started",
            run_id=run_id,
            history_count=len(normalized.history),
            model=str(getattr(self.config.model_provider, "model", "")),
        )
        try:
            response = self._generate_until_text(
                run_id, messages, tool_logs, model_calls,
                self.config.max_tool_iterations, "primary"
            )
            validation_retries = 0
            while True:
                outcome = self._validate(run_id, response.text, tool_logs, validation_retries)
                if outcome.ok:
                    result = Types.HarnessResult(
                        reply=response.text,
                        model=response.model,
                        interaction_id=response.interaction_id,
                        tool_logs=tool_logs,
                        iterations=model_calls["count"],
                        validation_retries=validation_retries,
                        normalized_input=normalized,
                        metadata={"run_id": run_id},
                    )
                    self.logger.emit(
                        "agent_run_finished",
                        run_id=run_id,
                        executor="harness",
                        status="ok",
                        fallback_reason="none",
                        total_ms=self._ms(started),
                        model_calls=model_calls["count"],
                        tool_calls=len(tool_logs),
                        validation_retries=validation_retries,
                    )
                    return result
                if validation_retries >= self.config.max_validation_retries:
                    raise Types.ValidationFailed(
                        "AI 응답 검증에 실패했습니다.",
                        validation_code=outcome.code,
                    )
                validation_retries += 1
                messages.append(Types.Message(role="system", content=outcome.correction_instruction))
                response = self._generate_until_text(
                    run_id, messages, tool_logs, model_calls,
                    self.config.max_validation_tool_iterations, "validation_repair"
                )
        except Exception as error:
            self.logger.emit(
                "agent_run_finished",
                run_id=run_id,
                executor="harness",
                status="error",
                error_code=str(getattr(error, "code", "unexpected_error")),
                fallback_reason=str(getattr(error, "code", "unexpected_error")),
                total_ms=self._ms(started),
                model_calls=model_calls["count"],
                tool_calls=len(tool_logs),
            )
            raise

    def _build_messages(self, normalized):
        builder = getattr(self.config, "message_builder", None)
        if builder is not None:
            return list(builder.build(normalized) or [])
        messages = [Types.Message(role=row.role, content=row.content) for row in normalized.history]
        messages.append(Types.Message(role="user", content=normalized.prompt))
        return messages

    def _generate_until_text(self, run_id, messages, tool_logs, model_calls, tool_budget, phase):
        tool_budget = max(0, int(tool_budget or 0))
        for tool_round in range(tool_budget + 1):
            response = self._generate_with_retry(run_id, messages, model_calls, phase)
            messages.extend(response.provider_messages())
            if not response.tool_calls:
                return response
            if tool_round >= tool_budget:
                raise Types.ToolBudgetExceeded(
                    "AI 도구 호출 한도를 초과했습니다.",
                    phase=phase,
                    budget=tool_budget,
                )
            for call in response.tool_calls:
                started = time.monotonic()
                try:
                    result = self.tools.execute(call)
                except Exception as error:
                    result = Types.ToolResult(
                        status="error",
                        data={"status": "error", "message": str(error)},
                        retryable=bool(getattr(error, "retryable", False)),
                    )
                duration_ms = self._ms(started)
                log = Types.ToolLog(
                    call=call,
                    result=result,
                    iteration=tool_round,
                    duration_ms=duration_ms,
                    phase=phase,
                )
                tool_logs.append(log)
                self.logger.emit(
                    "tool_execution",
                    run_id=run_id,
                    phase=phase,
                    iteration=tool_round,
                    tool=call.name,
                    status=result.status,
                    has_response=bool(result.data),
                    duration_ms=duration_ms,
                    retry_count=log.retry_count,
                )
                messages.append(Types.Message.function_result(call, result))
        raise Types.ToolBudgetExceeded("AI 도구 호출 한도를 초과했습니다.", phase=phase, budget=tool_budget)

    def _generate_with_retry(self, run_id, messages, model_calls, phase):
        model_calls["count"] += 1

        def operation(attempt):
            started = time.monotonic()
            try:
                response = self.config.model_provider.generate(
                    messages=messages,
                    tools=self.tools.specs(),
                    system_prompt=self.config.system_prompt,
                    stream=False,
                )
                self.logger.emit(
                    "provider_attempt",
                    run_id=run_id,
                    phase=phase,
                    attempt=attempt,
                    status="ok",
                    duration_ms=self._ms(started),
                    interaction_id=response.interaction_id,
                )
                return response
            except Exception as error:
                self.logger.emit(
                    "provider_attempt",
                    run_id=run_id,
                    phase=phase,
                    attempt=attempt,
                    status="error",
                    duration_ms=self._ms(started),
                    error_code=str(getattr(error, "code", "provider_error")),
                )
                raise

        def on_retry(error, attempt, delay):
            self.logger.emit(
                "provider_retry",
                run_id=run_id,
                phase=phase,
                attempt=attempt,
                delay_ms=int(delay * 1000),
                error_code=str(getattr(error, "code", "provider_error")),
            )

        return self.retry_policy.run(
            operation,
            should_retry=lambda error: bool(getattr(error, "retryable", False)),
            on_retry=on_retry,
        )

    def _validate(self, run_id, reply, tool_logs, retry_count):
        for validator in self.config.validators or []:
            outcome = validator.check(reply, tool_logs)
            self.logger.emit(
                "validation_checked",
                run_id=run_id,
                validator=validator.__class__.__name__,
                ok=bool(outcome.ok),
                code=outcome.code,
                retry_count=retry_count,
            )
            if not outcome.ok:
                return outcome
        return Types.ValidationResult(ok=True)

    def _ms(self, started):
        return max(0, int((time.monotonic() - started) * 1000))


Model = AgentHarness
