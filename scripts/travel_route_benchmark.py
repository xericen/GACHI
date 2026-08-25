#!/usr/bin/env python3
"""Run reproducible production travel-route benchmarks against chat_send."""

import argparse
import copy
import json
import pathlib
import time
import urllib.parse
import urllib.request


DEFAULT_ENDPOINT = "https://travel.wizide.com/wiz/api/page.access/chat_send"
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL_ROOT = PROJECT_ROOT / "src" / "model"

CASES = [
    {
        "id": "jeju_3d_transit",
        "label": "제주 3일 / 대중교통 / 하루 7곳",
        "prompt": "제주 3일 혼자 대중교통으로 자연 맛집 카페 코스를 하루 7곳씩 만들어줘",
        "state": {
            "region": "제주", "destination": "제주", "days": 3,
            "start_location": "제주공항", "accommodation_area": "제주시청",
            "companions": ["혼자"], "transport": "대중교통",
            "preferences": ["자연", "맛집", "카페"], "schedule_pace": "알차게",
            "generation_requested": True,
        },
    },
    {
        "id": "jeju_3d_driving",
        "label": "제주 3일 / 자동차 / 하루 7곳",
        "prompt": "제주 3일 친구와 자동차로 자연 맛집 카페 코스를 하루 7곳씩 만들어줘",
        "state": {
            "region": "제주", "destination": "제주", "days": 3,
            "start_location": "제주공항", "accommodation_area": "제주시청",
            "companions": ["친구"], "transport": "자동차",
            "preferences": ["자연", "맛집", "카페"], "schedule_pace": "알차게",
            "generation_requested": True,
        },
    },
    {
        "id": "seoul_2d_transit",
        "label": "서울 2일 / 대중교통",
        "prompt": "서울 2일 친구와 대중교통으로 문화 맛집 카페 코스 만들어줘",
        "state": {
            "region": "서울", "destination": "서울", "days": 2,
            "start_location": "서울역", "accommodation_area": "명동역",
            "companions": ["친구"], "transport": "대중교통",
            "preferences": ["문화", "맛집", "카페"], "schedule_pace": "보통",
            "generation_requested": True,
        },
    },
    {
        "id": "must_visit_fixed_meal",
        "label": "필수 관광지 + 고정 식사시간",
        "prompt": "서울 1일 대중교통 코스를 만들고 충무공 이순신 동상을 꼭 넣어줘. 점심은 12시 20분으로 고정해줘",
        "state": {
            "region": "서울", "destination": "서울", "days": 1,
            "start_location": "서울역",
            "transport": "대중교통", "preferences": ["문화", "맛집", "카페"],
            "schedule_pace": "보통", "must_visit_places": ["충무공 이순신 동상"],
            "generation_requested": True,
        },
    },
    {
        "id": "insufficient_region",
        "label": "후보가 부족한 지역",
        "prompt": "가거도 3일 대중교통으로 자연 맛집 카페 코스를 하루 7곳씩 만들어줘",
        "state": {
            "region": "가거도", "destination": "가거도", "days": 3,
            "start_location": "가거도항", "accommodation_area": "가거도",
            "transport": "대중교통", "preferences": ["자연", "맛집", "카페"],
            "schedule_pace": "알차게", "generation_requested": True,
        },
    },
]


class _ProjectFs:
    def read(self, path):
        return (PROJECT_ROOT / path).read_text(encoding="utf-8")


class _Project:
    def fs(self):
        return _ProjectFs()


class _LocalModelLoader:
    project = _Project()

    def model(self, namespace):
        path = MODEL_ROOT / f"{namespace}.py"
        scope = {"__file__": str(path), "__name__": str(path), "wiz": self}
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), scope)
        return scope["Model"]


def request_case(endpoint, case, timeout):
    status, data, initial_response_ms = _post_chat(
        endpoint, case["prompt"], case["state"], timeout,
        f"benchmark-{case['id']}-conditions",
    )
    if data.get("stage") == "ready_to_generate":
        status, data, response_ms = _post_chat(
            endpoint, "이 조건으로 코스 만들기", data.get("travel_state") or case["state"],
            timeout, f"benchmark-{case['id']}-generate",
        )
    else:
        response_ms = initial_response_ms
    return summarize(case, status, data, response_ms)


def _post_chat(endpoint, prompt, state, timeout, client_message_id):
    body = urllib.parse.urlencode({
        "prompt": prompt,
        "history": "[]",
        "thread_id": "",
        "client_message_id": client_message_id,
        "travel_state": json.dumps(state, ensure_ascii=False),
    }).encode("utf-8")
    request = urllib.request.Request(endpoint, data=body, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
        status = response.status
    response_ms = round((time.monotonic() - started) * 1000)
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    return status, data, response_ms


def run_local_case(case):
    loader = _LocalModelLoader()
    tools = loader.model("ai_tools")
    tools._direction_cache.clear()
    engine = loader.model("agents/travel_itinerary_engine")(tools)
    state = copy.deepcopy(case["state"])
    started = time.monotonic()
    result = engine.generate(state)
    response_ms = round((time.monotonic() - started) * 1000)
    data = {
        "stage": "draft_ready" if result.get("ok") else "error",
        "itinerary_draft": result.get("draft") or {},
        "failure_reason": result.get("failure_reason") or {},
        "metadata": result.get("metadata") or {},
    }
    summary = summarize(case, 200, data, response_ms)
    summary["measurement_mode"] = "local_engine_google_api"
    return summary


def summarize(case, http_status, data, response_ms):
    draft = data.get("itinerary_draft") or (data.get("travel_state") or {}).get("itinerary_draft") or {}
    metadata = draft.get("metadata") or data.get("metadata") or {}
    quality = draft.get("quality") or {}
    diagnostics = quality.get("route_diagnostics") or {}
    api = metadata.get("api_metrics") or {}
    candidate_pipeline = metadata.get("candidate_pipeline") or {}
    candidate_stages = candidate_pipeline.get("stages") or {}
    tool_logs = list(data.get("tool_logs") or [])
    tool_names = [
        str((log.get("call") or {}).get("name") or log.get("name") or "")
        for log in tool_logs if isinstance(log, dict)
    ]
    days = list(draft.get("days") or [])
    move_minutes = sum(int(day.get("total_move_minutes") or 0) for day in days)
    distance_meters = sum(int(day.get("total_distance_meters") or 0) for day in days)
    for day in days:
        connection = day.get("previous_day_connection") or {}
        if not day.get("start_connection"):
            move_minutes += int(connection.get("duration_minutes") or 0)
            distance_meters += int(connection.get("distance_meters") or 0)
    checks = quality.get("checks") or {}
    failure_reason = data.get("failure_reason") or {}
    places = [place for day in days for place in day.get("places") or []]
    required_names = list(case.get("state", {}).get("must_visit_places") or [])
    locked_places = [
        place for place in places if place.get("route_locked_reason") == "must_visit"
    ]
    must_visit_present = (
        all(
            any(
                _normalized_name(required) in _normalized_name(place.get("name"))
                for place in places
            )
            for required in required_names
        )
        if required_names and draft else None
    )
    lunch_places = [place for place in places if place.get("schedule_slot") == "lunch"]
    fixed_meal_time_ok = (
        all(str(place.get("target_time") or "") == "12:20" and str(place.get("time") or "") >= "12:20" for place in lunch_places)
        if lunch_places else None
    )
    return {
        "case": case["id"],
        "label": case["label"],
        "http_status": http_status,
        "stage": data.get("stage") or "",
        "ok": bool(draft),
        "days_created": len(days),
        "places_created": sum(len(day.get("places") or []) for day in days),
        "total_move_minutes": move_minutes if draft else None,
        "total_distance_meters": distance_meters if draft else None,
        "route_backtrack_count": quality.get("route_backtrack_count"),
        "tool_api_calls": api.get("tool_calls", len(tool_names) if tool_names else None),
        "place_search_calls": api.get("place_search_calls", tool_names.count("place_search") if tool_names else None),
        "directions_lookup_calls": api.get("directions_lookup_calls", tool_names.count("directions_lookup") if tool_names else None),
        "external_api_calls": api.get("external_api_calls"),
        "successful_external_calls": api.get("successful_external_calls"),
        "failed_external_calls": api.get("failed_external_calls"),
        "retried_external_calls": api.get("retried_external_calls"),
        "billing_external_calls": api.get("billing_external_calls"),
        "external_provider_requests": api.get("external_provider_requests") or {},
        "external_provider_failures": api.get("external_provider_failures") or {},
        "provider_skipped_route_calls": api.get("provider_skipped_route_calls"),
        "total_route_requests": api.get("total_route_requests"),
        "route_cache_hits": api.get("route_cache_hits"),
        "route_cache_misses": api.get("route_cache_misses"),
        "candidate_evaluations": api.get("candidate_evaluations"),
        "route_evaluations": api.get("route_evaluations"),
        "route_optimization_ms": api.get("route_optimization_ms"),
        "engine_elapsed_ms": metadata.get("elapsed_ms"),
        "http_response_ms": response_ms,
        "simple_route_ok": checks.get("simple_route_ok"),
        "route_quality_reason": quality.get("route_quality_reason") or [],
        "detour_ratio": diagnostics.get("detour_ratio"),
        "region_change_count": diagnostics.get("region_change_count"),
        "cross_region_jump_count": diagnostics.get("cross_region_jump_count"),
        "avoidable_cross_region_jump_count": diagnostics.get("avoidable_cross_region_jump_count"),
        "constrained_cross_region_jump_count": diagnostics.get("constrained_cross_region_jump_count"),
        "largest_backtrack_segment": diagnostics.get("largest_backtrack_segment"),
        "day_connection_costs": diagnostics.get("day_connection_costs") or [],
        "schedule_complete": checks.get("schedule_complete"),
        "must_visit_present": must_visit_present,
        "must_visit_selected_names": [place.get("name") for place in locked_places],
        "fixed_meal_time_ok": fixed_meal_time_ok,
        "failure_code": failure_reason.get("code") or "",
        "failure_detail": failure_reason.get("failure_reason") or "",
        "requested_region": failure_reason.get("requested_region") or "",
        "candidate_count": failure_reason.get("candidate_count"),
        "eligible_candidate_count": failure_reason.get("eligible_candidate_count"),
        "route_reachable_candidate_count": failure_reason.get("route_reachable_candidate_count"),
        "region_mismatch_count": failure_reason.get("region_mismatch_count"),
        "missing_days": failure_reason.get("missing_days") or [],
        "missing_slots": failure_reason.get("missing_slots") or [],
        "shortage_categories": failure_reason.get("shortage_categories") or [],
        "candidate_pipeline": candidate_pipeline,
        "raw_candidates": _pipeline_count(candidate_stages, "raw_candidates"),
        "region_validation_passed": _pipeline_count(
            candidate_stages, "region_validation_passed",
        ),
        "coordinate_validation_passed": _pipeline_count(
            candidate_stages, "coordinate_validation_passed",
        ),
        "transport_reachable": _pipeline_count(
            candidate_stages, "transport_reachable",
        ),
        "category_validation_passed": _pipeline_count(
            candidate_stages, "category_validation_passed",
        ),
        "mandatory_condition_passed": _pipeline_count(
            candidate_stages, "mandatory_condition_passed",
        ),
        "route_candidates": _pipeline_count(candidate_stages, "route_candidates"),
        "final_selected": _pipeline_count(candidate_stages, "final_selected"),
    }


def _pipeline_count(stages, name):
    value = stages.get(name)
    if isinstance(value, dict):
        return value.get("count")
    return value


def _normalized_name(value):
    return "".join(character for character in str(value or "").lower() if character.isalnum())


def print_markdown(results):
    print("| 케이스 | 결과 | 이동시간(분) | 이동거리(m) | 역방향 | Route 요청 | 캐시 hit/miss | 외부 성공/실패 | 엔진(ms) | HTTP(ms) | simple_route_ok |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in results:
        print(
            f"| {row['label']} | {'성공' if row['ok'] else row['failure_code'] or '실패'} "
            f"| {display(row['total_move_minutes'])} | {display(row['total_distance_meters'])} "
            f"| {display(row['route_backtrack_count'])} | {display(row.get('total_route_requests'))} "
            f"| {display(row.get('route_cache_hits'))}/{display(row.get('route_cache_misses'))} "
            f"| {display(row.get('successful_external_calls'))}/{display(row.get('failed_external_calls'))} "
            f"| {display(row['engine_elapsed_ms'])} | {display(row['http_response_ms'])} "
            f"| {display(row['simple_route_ok'])} |"
        )
    print("\n| 케이스 | 원본 | 지역 통과 | 좌표 통과 | 교통 가능 | 카테고리 통과 | 필수조건 통과 | 동선 후보 | 최종 선택 | 부족 카테고리 | 부족 일/슬롯 |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
    for row in results:
        pipeline = row.get("candidate_pipeline") or {}
        print(
            f"| {row['label']} | {display(row.get('raw_candidates'))} "
            f"| {display(row.get('region_validation_passed'))} "
            f"| {display(row.get('coordinate_validation_passed'))} "
            f"| {display(row.get('transport_reachable'))} "
            f"| {display(row.get('category_validation_passed'))} "
            f"| {display(row.get('mandatory_condition_passed'))} "
            f"| {display(row.get('route_candidates'))} "
            f"| {display(row.get('final_selected'))} "
            f"| {', '.join(pipeline.get('missing_categories') or []) or '-'} "
            f"| {len(pipeline.get('missing_days') or [])}/{len(pipeline.get('missing_slots') or [])} |"
        )
    print("\n| 케이스 | 청구 HTTP | 제공자별 요청 | 제공자 실패 사유 | 권역 점프(회피/제약) | 필수 장소 |")
    print("|---|---:|---|---|---:|---|")
    for row in results:
        print(
            f"| {row['label']} | {display(row.get('billing_external_calls'))} "
            f"| {row.get('external_provider_requests') or {}} "
            f"| {row.get('external_provider_failures') or {}} "
            f"| {display(row.get('cross_region_jump_count'))}"
            f"({display(row.get('avoidable_cross_region_jump_count'))}/"
            f"{display(row.get('constrained_cross_region_jump_count'))}) "
            f"| {', '.join(row.get('must_visit_selected_names') or []) or '-'} |"
        )


def display(value):
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--local-engine", action="store_true",
        help="Run the current deterministic engine directly with real Google APIs.",
    )
    parser.add_argument("--case", choices=[case["id"] for case in CASES])
    args = parser.parse_args()
    cases = [case for case in CASES if not args.case or case["id"] == args.case]
    results = []
    for case in cases:
        try:
            results.append(
                run_local_case(case)
                if args.local_engine
                else request_case(args.endpoint, case, args.timeout)
            )
        except Exception as error:
            results.append({
                "case": case["id"], "label": case["label"], "ok": False,
                "failure_code": f"request_{type(error).__name__}",
                "http_response_ms": None,
            })
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_markdown(results)


if __name__ == "__main__":
    main()
