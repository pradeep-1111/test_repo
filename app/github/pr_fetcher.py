from __future__ import annotations

import yaml

from app.github.client import GitHubClient
from app.schemas.pr_models import ChangedFile, PullRequestContext
from app.tools.diff_parser import extract_added_lines, extract_changed_lines, parse_patch

RULE_PATHS = [
    ".merge-guard.yml",
    ".merge-guard.yaml",
    ".github/merge-guard.yml",
    ".github/merge-guard.yaml",
]


class PullRequestFetcher:
    def __init__(self, github_client: GitHubClient) -> None:
        self.github_client = github_client

    def fetch(self, pr_url: str) -> PullRequestContext:
        owner, repo, number = self.github_client.parse_pr_url(pr_url)
        pr = self.github_client.get_pull_request(owner=owner, repo=repo, number=number)
        pr_files = self.github_client.get_pull_request_files(owner=owner, repo=repo, number=number)
        head_sha = pr["head"]["sha"]

        changed_files: list[ChangedFile] = []
        for item in pr_files:
            path = item["filename"]
            patch = item.get("patch") or ""
            changed_files.append(
                ChangedFile(
                    path=path,
                    status=item.get("status", "modified"),
                    patch=patch,
                    head_content=self.github_client.get_file_content(owner=owner, repo=repo, path=path, ref=head_sha),
                    changed_lines=extract_changed_lines(patch),
                    added_lines=extract_added_lines(patch),
                    diff_hunks=parse_patch(patch),
                )
            )

        return PullRequestContext(
            owner=owner,
            repo=repo,
            number=number,
            title=pr.get("title") or "",
            body=pr.get("body") or "",
            pr_url=pr_url,
            base_sha=pr["base"]["sha"],
            head_sha=head_sha,
            changed_files=changed_files,
            rules_config=self._load_rules(owner=owner, repo=repo, ref=head_sha),
        )

    def _load_rules(self, *, owner: str, repo: str, ref: str) -> dict:
        for path in RULE_PATHS:
            content = self.github_client.get_file_content(owner=owner, repo=repo, path=path, ref=ref)
            if not content:
                continue
            try:
                loaded = yaml.safe_load(content) or {}
                if isinstance(loaded, dict):
                    return loaded
            except yaml.YAMLError:
                return {}
        return {}