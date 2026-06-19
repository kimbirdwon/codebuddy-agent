import os
from typing import Any, Dict, Optional

import requests


class GitHubClient:
    def __init__(self, token: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or os.getenv("GITHUB_API_URL", "https://api.github.com")).rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": "codebuddy-agent",
            }
        )
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        response = self.session.request(method, f"{self.base_url}{path}", timeout=30, **kwargs)
        response.raise_for_status()
        if response.content:
            return response.json()
        return {}

    def get_pull_request(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        pr = self._request("GET", f"/repos/{owner}/{repo}/pulls/{pull_number}")
        files = self._request("GET", f"/repos/{owner}/{repo}/pulls/{pull_number}/files")
        comments = self._request("GET", f"/repos/{owner}/{repo}/issues/{pull_number}/comments")
        return {
            "pull_request": pr,
            "files": files,
            "existing_comments": comments,
        }

    def list_repositories(self, owner: str) -> Dict[str, Any]:
        repos = self._request("GET", f"/users/{owner}/repos")
        return {
            "count": len(repos),
            "repositories": [
                {
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "private": repo["private"],
                    "default_branch": repo.get("default_branch"),
                }
                for repo in repos
            ],
        }

    def post_pull_request_comment(self, owner: str, repo: str, pull_number: int, body: str) -> Dict[str, Any]:
        comment = self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{pull_number}/comments",
            json={"body": body},
        )
        return {
            "id": comment["id"],
            "html_url": comment["html_url"],
            "created_at": comment["created_at"],
        }
