Types = wiz.model("ai_harness/types")


class ToolRegistry:
    def __init__(self, tools=None):
        self._tools = {}
        for tool in tools or []:
            name = str(getattr(tool, "name", "") or "").strip()
            if name:
                self._tools[name] = tool

    def specs(self):
        return [dict(tool.schema or {}) for tool in self._tools.values()]

    def execute(self, call):
        tool = self._tools.get(call.name)
        if tool is None:
            return Types.ToolResult(
                status="error",
                data={"status": "error", "message": f"지원하지 않는 함수입니다: {call.name}"},
            )
        result = tool.execute(dict(call.arguments or {}))
        if hasattr(result, "status") and hasattr(result, "data"):
            return result
        if isinstance(result, dict):
            return Types.ToolResult(status=str(result.get("status") or "ok"), data=result)
        return Types.ToolResult(status="ok", data={"result": result})


Model = ToolRegistry
