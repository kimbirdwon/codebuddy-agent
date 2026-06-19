import ast
import json
import os
from typing import Any, Dict, List

DEFAULT_TOOL_MODEL_ID = os.getenv("TOOL_MODEL_ID", "global.anthropic.claude-sonnet-4-6")


def build_review_prompt(pr_context: Dict[str, Any]) -> str:
    repo = pr_context.get("repository", {})
    pull_request = pr_context.get("pull_request", {})
    changed_files = pr_context.get("changed_files", [])
    files_summary = "\n".join(
        f"- {item.get('filename')}: +{item.get('additions', 0)} / -{item.get('deletions', 0)}"
        for item in changed_files[:20]
    )
    return (
        "당신은 시니어 코드 리뷰어입니다.\n"
        "다음 Pull Request를 검토하고 아래 순서로 답변해주세요.\n"
        "1. 전체 요약\n"
        "2. 위험도가 높은 이슈\n"
        "3. 보안, 복잡도, 테스트 관점의 개선 제안\n"
        "4. 필요 시 Tool 호출 결과 요약\n\n"
        f"Repository: {repo.get('full_name', 'unknown')}\n"
        f"PR: #{pull_request.get('number', 'unknown')} {pull_request.get('title', '')}\n"
        f"Author: {pull_request.get('user', {}).get('login', 'unknown')}\n"
        f"URL: {pull_request.get('html_url', '')}\n"
        f"Base: {pull_request.get('base', {}).get('ref', '')}\n"
        f"Head: {pull_request.get('head', {}).get('ref', '')}\n"
        f"Body:\n{pull_request.get('body') or '(no description)'}\n\n"
        "Changed files:\n"
        f"{files_summary or '- no files found'}\n"
    )


def estimate_complexity(code: str) -> Dict[str, Any]:
    tree = ast.parse(code)
    functions: List[Dict[str, Any]] = []

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            score = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.BoolOp, ast.Match)):
                    score += 1
                if isinstance(child, ast.comprehension):
                    score += 1
            functions.append(
                {
                    "name": node.name,
                    "lineno": node.lineno,
                    "complexity": score,
                    "risk": classify_complexity(score),
                }
            )
            self.generic_visit(node)

    Visitor().visit(tree)
    max_score = max((item["complexity"] for item in functions), default=0)
    return {
        "summary": {
            "function_count": len(functions),
            "max_complexity": max_score,
            "risk": classify_complexity(max_score),
        },
        "functions": functions,
    }


def classify_complexity(score: int) -> str:
    if score >= 15:
        return "high"
    if score >= 8:
        return "medium"
    return "low"


def invoke_text_model(prompt: str, model_id: str = DEFAULT_TOOL_MODEL_ID) -> str:
    import boto3

    client = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION"))
    response = client.converse(
        modelId=model_id,
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
    )
    outputs = response.get("output", {}).get("message", {}).get("content", [])
    return "\n".join(item.get("text", "") for item in outputs if "text" in item).strip()


def generate_unit_test_prompt(code: str, language: str) -> str:
    return (
        f"Generate concise but useful {language} unit tests for the code below.\n"
        "Prefer realistic assertions and include edge cases.\n\n"
        f"{code}"
    )


def generate_refactor_prompt(code: str, goals: str) -> str:
    return (
        "Review the code and suggest a refactoring plan.\n"
        f"Goals: {goals or 'readability, maintainability, testability'}\n"
        "Return a short summary, then a revised code example if helpful.\n\n"
        f"{code}"
    )


def json_dumps(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False)
