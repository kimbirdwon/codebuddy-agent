import json
from typing import Any, Dict

from tools.complexity import analyze_complexity
from tools.github_pr import (
    get_pull_request,
    list_repositories,
    post_pr_comment,
    send_slack_message,
)
from tools.refactor import suggest_refactor
from tools.testgen import generate_unit_test


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        operation = resolve_operation_name(event)
        arguments = extract_arguments(event)
        result = dispatch_operation(operation, arguments)
        return action_group_response(event, 200, result)
    except Exception as exc:  # noqa: BLE001
        return action_group_response(
            event,
            500,
            {
                "error": type(exc).__name__,
                "message": str(exc),
            },
        )


def resolve_operation_name(event: Dict[str, Any]) -> str:
    return event.get("function") or event.get("action") or event.get("operation") or event.get("apiPath", "")


def extract_arguments(event: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for item in event.get("parameters", []):
        payload[item["name"]] = item.get("value")

    body = (
        event.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("properties", [])
    )
    for item in body:
        payload[item["name"]] = item.get("value")

    if not payload and "body" in event:
        if isinstance(event["body"], str):
            payload = json.loads(event["body"])
        elif isinstance(event["body"], dict):
            payload = dict(event["body"])
    return payload


def dispatch_operation(operation: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if operation in {"get_pull_request", "/pull-request"}:
        return get_pull_request(args["owner"], args["repo"], int(args["pull_number"]))

    if operation in {"list_repositories", "/repositories"}:
        return list_repositories(args["owner"])

    if operation in {"post_pr_comment", "/pull-request/comment"}:
        return post_pr_comment(args["owner"], args["repo"], int(args["pull_number"]), args["body"])

    if operation in {"send_slack_message", "/slack/message"}:
        return send_slack_message(args["text"])

    if operation in {"analyze_complexity", "/complexity/analyze"}:
        return analyze_complexity(args["code"])

    if operation in {"generate_unit_test", "/unit-test/generate"}:
        return generate_unit_test(args["code"], args.get("language", "python"))

    if operation in {"suggest_refactor", "/refactor/suggest"}:
        return suggest_refactor(args["code"], args.get("goals", ""))

    raise ValueError(f"Unsupported operation: {operation}")


def action_group_response(event: Dict[str, Any], status_code: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", "CodeBuddyTools"),
            "apiPath": event.get("apiPath", event.get("function", "/unknown")),
            "httpMethod": event.get("httpMethod", "POST"),
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(payload, ensure_ascii=False),
                }
            },
        },
    }
