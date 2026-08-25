import datetime
import json
import os
import threading


class TravelRouteObservability:
    """Persist route-generation health without storing prompts or place names."""

    DEFAULT_PATH = "/opt/app/data/observability/travel-route-metrics.jsonl"
    MAX_SUMMARY_ROWS = 500
    _lock = threading.Lock()

    def __init__(self, wiz_context=None, path=None):
        self.wiz = wiz_context
        self.path = str(
            path or os.environ.get("GACHI_ROUTE_METRICS_PATH") or self.DEFAULT_PATH
        ).strip()

    def record(self, result, state, request_id="", operation="generate"):
        result = result if isinstance(result, dict) else {}
        state = state if isinstance(state, dict) else {}
        metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
        draft = result.get("draft") if isinstance(result.get("draft"), dict) else {}
        if draft and isinstance(draft.get("metadata"), dict):
            metadata = draft["metadata"]
        api = metadata.get("api_metrics") if isinstance(metadata.get("api_metrics"), dict) else {}
        pipeline = metadata.get("candidate_pipeline") if isinstance(metadata.get("candidate_pipeline"), dict) else {}
        stages = pipeline.get("stages") if isinstance(pipeline.get("stages"), dict) else {}
        quality = draft.get("quality") if isinstance(draft.get("quality"), dict) else {}
        checks = quality.get("checks") if isinstance(quality.get("checks"), dict) else {}
        diagnostics = quality.get("route_diagnostics") if isinstance(quality.get("route_diagnostics"), dict) else {}
        failure = result.get("failure_reason") if isinstance(result.get("failure_reason"), dict) else {}
        raw_count = self._stage_count(stages, "raw_candidates")
        selected_count = int(
            pipeline.get("returned_final_selection_count")
            or pipeline.get("completed_day_selection_count")
            or 0
        )
        required_count = int(
            pipeline.get("required_places")
            or failure.get("required_places")
            or 0
        )
        row = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "request_id": str(request_id or "")[:96],
            "operation": str(operation or "generate")[:24],
            "region": str(state.get("region") or "")[:40],
            "transport": str(state.get("transport") or "")[:20],
            "days": int(state.get("days") or 0),
            "ok": bool(result.get("ok")),
            "failure_code": str(failure.get("code") or "")[:80],
            "generation_ms": int(metadata.get("elapsed_ms") or 0),
            "route_optimization_ms": int(api.get("route_optimization_ms") or 0),
            "simple_route_ok": checks.get("simple_route_ok") if draft else None,
            "route_quality_reasons": list(diagnostics.get("reasons") or [])[:8],
            "raw_candidates": raw_count,
            "selected_candidates": selected_count,
            "required_candidates": required_count,
            "candidate_retention": round(selected_count / max(1, raw_count), 4),
            "total_route_requests": int(api.get("total_route_requests") or 0),
            "route_cache_hits": int(api.get("route_cache_hits") or 0),
            "route_cache_misses": int(api.get("route_cache_misses") or 0),
            "successful_external_calls": int(api.get("successful_external_calls") or 0),
            "failed_external_calls": int(api.get("failed_external_calls") or 0),
            "retried_external_calls": int(api.get("retried_external_calls") or 0),
            "candidate_evaluations": int(api.get("candidate_evaluations") or 0),
            "route_evaluations": int(api.get("route_evaluations") or 0),
        }
        self._append(row)
        health = self.summary()
        if health.get("alerts"):
            print("[travel_route_alert] " + json.dumps({
                "alerts": health["alerts"],
                "window": health.get("window"),
                "latest_request_id": row["request_id"],
            }, ensure_ascii=False))
        return {"latest": row, "summary": health}

    def summary(self, limit=100):
        rows = self._read_rows(max(1, min(int(limit or 100), self.MAX_SUMMARY_ROWS)))
        total = len(rows)
        success_rows = [row for row in rows if row.get("ok")]
        generation = sorted(int(row.get("generation_ms") or 0) for row in rows)
        route_rows = [row for row in success_rows if row.get("simple_route_ok") is not None]
        false_count = sum(row.get("simple_route_ok") is False for row in route_rows)
        external_total = sum(
            int(row.get("successful_external_calls") or 0) + int(row.get("failed_external_calls") or 0)
            for row in rows
        )
        external_failed = sum(int(row.get("failed_external_calls") or 0) for row in rows)
        candidate_rows = [row for row in rows if int(row.get("raw_candidates") or 0) > 0]
        avg_retention = round(
            sum(float(row.get("candidate_retention") or 0) for row in candidate_rows)
            / max(1, len(candidate_rows)),
            4,
        )
        summary = {
            "storage_path": self.path,
            "window": total,
            "success_rate": round(len(success_rows) / max(1, total), 4),
            "generation_p95_ms": self._percentile(generation, 0.95),
            "simple_route_false_rate": round(false_count / max(1, len(route_rows)), 4),
            "candidate_retention_average": avg_retention,
            "external_failure_rate": round(external_failed / max(1, external_total), 4),
            "total_route_requests": sum(int(row.get("total_route_requests") or 0) for row in rows),
            "route_cache_hits": sum(int(row.get("route_cache_hits") or 0) for row in rows),
            "route_cache_misses": sum(int(row.get("route_cache_misses") or 0) for row in rows),
            "successful_external_calls": sum(int(row.get("successful_external_calls") or 0) for row in rows),
            "failed_external_calls": external_failed,
            "alerts": [],
        }
        if total >= 5 and summary["generation_p95_ms"] > 60000:
            summary["alerts"].append("generation_time_spike")
        if len(route_rows) >= 5 and summary["simple_route_false_rate"] > 0.2:
            summary["alerts"].append("simple_route_quality_drop")
        if len(candidate_rows) >= 5 and avg_retention < 0.1:
            summary["alerts"].append("candidate_retention_drop")
        if external_total >= 20 and summary["external_failure_rate"] > 0.1:
            summary["alerts"].append("external_route_failure_spike")
        return summary

    def _append(self, row):
        target = self.path
        try:
            directory = os.path.dirname(target)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with self._lock:
                with open(target, "a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        except OSError:
            fallback = "/tmp/gachi-travel-route-metrics.jsonl"
            self.path = fallback
            with self._lock:
                with open(fallback, "a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    def _read_rows(self, limit):
        try:
            with open(self.path, "r", encoding="utf-8") as stream:
                lines = stream.readlines()[-limit:]
        except OSError:
            return []
        rows = []
        for line in lines:
            try:
                value = json.loads(line)
            except Exception:
                continue
            if isinstance(value, dict):
                rows.append(value)
        return rows

    def _stage_count(self, stages, name):
        value = stages.get(name) if isinstance(stages, dict) else {}
        return int(value.get("count") or 0) if isinstance(value, dict) else 0

    def _percentile(self, values, ratio):
        if not values:
            return 0
        index = max(0, min(len(values) - 1, int(round((len(values) - 1) * ratio))))
        return int(values[index])


Model = TravelRouteObservability
