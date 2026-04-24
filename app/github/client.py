from __future__ import annotations

import base64
from urllib.parse import urlparse

import requests


class GitHubClient:
    def __init__(self, token: str) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    @classmethod
    def from_installation(cls, *, settings, installation_id: int | None):
        if installation_id and settings.github_app_configured:
            from app.github.app_auth import build_installation_token

            token = build_installation_token(settings=settings, installation_id=installation_id)
            return cls(token=token)
        if settings.github_token:
            return cls(token=settings.github_token)
        raise RuntimeError("GitHub authentication is not configured")

    @staticmethod
    def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
        parsed = urlparse(pr_url)
        parts = [item for item in parsed.path.split("/") if item]
        if len(parts) < 4 or parts[2] != "pull":
            raise ValueError(f"Unsupported pull request URL: {pr_url}")
        return parts[0], parts[1], int(parts[3])

    def get_pull_request(self, *, owner: str, repo: str, number: int) -> dict:
        response = self.session.get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}", timeout=30)
        response.raise_for_status()
        return response.json()

    def get_pull_request_files(self, *, owner: str, repo: str, number: int) -> list[dict]:
        files: list[dict] = []
        page = 1
        while True:
            response = self.session.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files",
                params={"per_page": 100, "page": page},
                timeout=30,
            )
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break
            files.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return files

    def get_file_content(self, *, owner: str, repo: str, path: str, ref: str) -> str:
        response = self.session.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
            timeout=30,
        )
        if response.status_code == 404:
            return ""
        response.raise_for_status()
        data = response.json()
        content = data.get("content", "")
        if not content:
            return ""
        return base64.b64decode(content).decode("utf-8", errors="ignore")

    def create_issue_comment(self, *, owner: str, repo: str, issue_number: int, body: str) -> dict:
        response = self.session.post(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments",
            json={"body": body},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def create_check_run(self, *, owner: str, repo: str, name: str, head_sha: str, status: str, output: dict) -> dict:
        response = self.session.post(
            f"https://api.github.com/repos/{owner}/{repo}/check-runs",
            json={"name": name, "head_sha": head_sha, "status": status, "output": output},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def update_check_run(self, *, owner: str, repo: str, check_run_id: int, body: dict) -> dict:
        response = self.session.patch(
            f"https://api.github.com/repos/{owner}/{repo}/check-runs/{check_run_id}",
            json=body,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def create_pull_review(
        self,
        *,
        owner: str,
        repo: str,
        pull_number: int,
        commit_id: str,
        body: str,
        comments: list[dict],
        event: str = "COMMENT",
    ) -> dict:
        payload = {
            "commit_id": commit_id,
            "body": body,
            "event": event,
            "comments": comments,
        }
        response = self.session.post(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()