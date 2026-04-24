from collections import Counter

from app.core.config import Settings
from app.github.client import GitHubClient
from app.schemas.finding import Finding
from app.schemas.review_result import ReviewResult


class ReviewPoster:
    def __init__(self, github_client: GitHubClient, settings: Settings) -> None:
        self.github_client = github_client
        self.settings = settings

    def start_check_run(self, result: ReviewResult | None = None, *, owner: str, repo: str, head_sha: str) -> int | None:
        if not self.settings.post_check_run:
            return None
        output = {
            "title": "MergeGuard is reviewing this pull request",
            "summary": "Static analysis, policy checks, and AI reviewers are running.",
        }
        check_run = self.github_client.create_check_run(
            owner=owner,
            repo=repo,
            name="MergeGuard",
            head_sha=head_sha,
            status="in_progress",
            output=output,
        )
        return check_run.get("id")

    def publish(self, result: ReviewResult) -> ReviewResult:
        pr = result.pr

        if self.settings.post_inline_comments:
            try:
                self._post_inline_comments(result)
            except Exception as exc:
                result.tool_warnings.append(f"Failed to post inline comments: {exc}")

        if self.settings.post_summary_to_github:
            try:
                self.github_client.create_issue_comment(
                    owner=pr.owner,
                    repo=pr.repo,
                    issue_number=pr.number,
                    body=result.review_body,
                )
            except Exception as exc:
                result.tool_warnings.append(f"Failed to post summary comment: {exc}")

        if self.settings.post_check_run and result.check_run_id:
            self._complete_check_run(result)

        return result

    def fail_check_run(self, *, owner: str, repo: str, check_run_id: int, error_message: str) -> None:
        if not self.settings.post_check_run:
            return
        self.github_client.update_check_run(
            owner=owner,
            repo=repo,
            check_run_id=check_run_id,
            body={
                "status": "completed",
                "conclusion": "failure",
                "output": {
                    "title": "MergeGuard review failed",
                    "summary": error_message[:65000],
                },
            },
        )

    def _post_inline_comments(self, result: ReviewResult) -> None:
        pr = result.pr
        changed_lookup = {item.path: set(item.changed_lines) for item in pr.changed_files}
        comments: list[dict] = []
        for finding in result.findings:
            if len(comments) >= self.settings.max_inline_comments:
                break
            changed_lines = changed_lookup.get(finding.file)
            if not changed_lines or finding.line_start not in changed_lines:
                continue
            body = finding.review_comment_body or finding.explanation

            # GitHub suggested changes only work on changed diff lines.
            # If we do not have a generated suggestion, still post a normal inline comment.
            comments.append(
            {
                "path": finding.file,
                "line": finding.line_start,
                "side": "RIGHT",
                "body": body,
            }
        )

        if not comments:
            return

        self.github_client.create_pull_review(
            owner=pr.owner,
            repo=pr.repo,
            pull_number=pr.number,
            commit_id=pr.head_sha,
            body="MergeGuard left inline comments on the highest-signal changed lines.",
            comments=comments,
            event="COMMENT",
        )

    def determine_conclusion(self, findings: list[Finding]) -> str:
        severity_rank = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        block_rank = severity_rank.get(self.settings.merge_block_min_severity, 2)
        worst = max((severity_rank[item.severity] for item in findings), default=-1)
        if worst >= block_rank:
            return "failure"
        if findings:
            return "neutral"
        return "success"

    def _complete_check_run(self, result: ReviewResult) -> None:
        pr = result.pr
        conclusion = self.determine_conclusion(result.findings)
        result.conclusion = conclusion
        annotations = [self._annotation_for(finding) for finding in result.findings[: self.settings.max_check_annotations]]
        counts = Counter(item.severity for item in result.findings)
        summary_lines = [
            f"Findings: critical {counts.get('critical', 0)}, high {counts.get('high', 0)}, medium {counts.get('medium', 0)}, low {counts.get('low', 0)}",
            "",
            result.summary_markdown[:60000],
        ]
        if result.tool_warnings:
            summary_lines.extend(["", "Tool notes:"])
            summary_lines.extend(f"- {warning}" for warning in result.tool_warnings)
        output = {
            "title": f"MergeGuard concluded with {conclusion}",
            "summary": "\n".join(summary_lines)[:65000],
            "annotations": annotations,
        }
        self.github_client.update_check_run(
            owner=pr.owner,
            repo=pr.repo,
            check_run_id=result.check_run_id,
            body={
                "status": "completed",
                "conclusion": conclusion,
                "output": output,
            },
        )

    def _annotation_for(self, finding: Finding) -> dict:
        level = {
            "critical": "failure",
            "high": "failure",
            "medium": "warning",
            "low": "notice",
        }[finding.severity]
        details = finding.suggested_fix or finding.explanation
        return {
            "path": finding.file,
            "start_line": finding.line_start,
            "end_line": finding.line_end,
            "annotation_level": level,
            "title": finding.title[:255],
            "message": finding.explanation[:65535],
            "raw_details": details[:65535],
        }