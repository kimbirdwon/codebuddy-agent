import os
from typing import Dict

import requests

from shared.github_api import GitHubClient


def get_pull_request(owner: str, repo: str, pull_number: int) -> Dict:
    github = GitHubClient(token=os.getenv("GITHUB_TOKEN"))
    return github.get_pull_request(owner, repo, pull_number)


def list_repositories(owner: str) -> Dict:
    github = GitHubClient(token=os.getenv("GITHUB_TOKEN"))
    return github.list_repositories(owner)


def post_pr_comment(owner: str, repo: str, pull_number: int, body: str) -> Dict:
    github = GitHubClient(token=os.getenv("GITHUB_TOKEN"))
    return github.post_pull_request_comment(owner, repo, pull_number, body)


def send_slack_message(text: str) -> Dict:
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        raise ValueError("SLACK_WEBHOOK_URL is not configured")
    response = requests.post(webhook, json={"text": text}, timeout=15)
    response.raise_for_status()
    return {"ok": True, "status_code": response.status_code}
