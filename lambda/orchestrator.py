import json
import os
import time
import uuid
from typing import Any, Dict, Iterable

import boto3
from botocore.exceptions import ClientError, EventStreamError

from shared.review import build_review_prompt


bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=os.getenv("AWS_REGION"))


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    payload = extract_request_payload(event)
    pr_context = build_pr_context(payload)
    prompt = build_agent_prompt(pr_context)
    session_id = payload.get("session_id") or str(uuid.uuid4())

    max_retries = 3
    agent_text = ""
    last_error = None

    for attempt in range(max_retries):
        try:
            response = bedrock_agent_runtime.invoke_agent(
                agentId=os.environ["AGENT_ID"],
                agentAliasId=os.environ["AGENT_ALIAS_ID"],
                sessionId=session_id,
                inputText=prompt,
            )
            agent_text = extract_completion_text(response.get("completion", []))
            last_error = None
            break
        except (ClientError, EventStreamError) as exc:
            last_error = exc
            if attempt == max_retries - 1 or not should_retry_dependency_failure(exc):
                raise
            time.sleep(2 ** attempt)

    if last_error is not None:
        raise last_error

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "message": "Review completed",
                "session_id": session_id,
                "agent_response": agent_text,
                "pull_request": pr_context.get("pull_request", {}),
            },
            ensure_ascii=False,
        ),
    }


def extract_request_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    body = event.get("body")
    if isinstance(body, str) and body:
        return json.loads(body)
    if isinstance(body, dict):
        return body
    return event


def build_pr_context(payload: Dict[str, Any]) -> Dict[str, Any]:
    repository = payload.get("repository", {})
    pull_request = payload.get("pull_request", {})
    changed_files = payload.get("files", [])

    if not pull_request and payload.get("pr_url"):
        pull_request = {
            "html_url": payload["pr_url"],
            "title": payload.get("title", ""),
            "body": payload.get("description", ""),
            "number": payload.get("pull_number", "unknown"),
            "base": {"ref": payload.get("base_branch", "")},
            "head": {"ref": payload.get("head_branch", "")},
            "user": {"login": payload.get("author", "unknown")},
        }

    return {
        "repository": repository,
        "pull_request": pull_request,
        "changed_files": changed_files,
    }


def build_agent_prompt(pr_context: Dict[str, Any]) -> str:
    prefix = os.getenv(
        "AGENT_INSTRUCTION_PREFIX",
        "Use tools when needed to inspect pull request details, changed files, comments, complexity, test drafts, and refactoring suggestions.",
    )
    return f"{prefix}\n\n{build_review_prompt(pr_context)}"


def extract_completion_text(events: Iterable[Dict[str, Any]]) -> str:
    chunks = []
    for event in events:
        chunk = event.get("chunk")
        if not chunk:
            continue
        data = chunk.get("bytes", b"")
        if isinstance(data, (bytes, bytearray)):
            chunks.append(data.decode("utf-8"))
        elif isinstance(data, str):
            chunks.append(data)
    return "".join(chunks).strip()


def should_retry_dependency_failure(exc: Exception) -> bool:
    text = str(exc).lower()
    return "dependencyfailedexception" in text or "received failed response from api execution" in text
