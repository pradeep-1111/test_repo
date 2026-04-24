from __future__ import annotations

import tempfile
from pathlib import Path

from app.core.config import Settings
from app.github.client import GitHubClient
from app.github.pr_fetcher import PullRequestFetcher
from app.github.review_poster import ReviewPoster
from app.reviewers.bug_reviewer import BugReviewer
from app.reviewers.fix_suggestion_reviewer import FixSuggestionReviewer
from app.reviewers.rules_reviewer import RulesReviewer
from app.reviewers.security_reviewer import SecurityReviewer
from app.reviewers.synthesizer import ReviewSynthesizer
from app.reviewers.testing_reviewer import TestingReviewer
from app.schemas.review_result import ReviewResult
from app.services.review_history import ReviewHistoryService
from app.tools.ast_tools import run_ast_analysis
from app.tools.linter_runner import run_linting
from app.tools.semgrep_runner import run_semgrep


class ReviewOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def review_pr(self, *, pr_url: str, installation_id: int | None, source: str) -> ReviewResult:
        github_client = GitHubClient.from_installation(settings=self.settings, installation_id=installation_id)
        fetcher = PullRequestFetcher(github_client)
        pr = fetcher.fetch(pr_url)
        poster = ReviewPoster(github_client, self.settings)

        result = ReviewResult(pr=pr)
        result.check_run_id = poster.start_check_run(owner=pr.owner, repo=pr.repo, head_sha=pr.head_sha)

        try:
            with tempfile.TemporaryDirectory(prefix="mergeguard-") as workspace:
                workspace_path = Path(workspace)
                for changed_file in pr.changed_files:
                    destination = workspace_path / changed_file.path
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text(changed_file.head_content, encoding="utf-8", errors="ignore")

                findings: list = []

                if self.settings.enable_semgrep:
                    semgrep_findings, semgrep_warnings = run_semgrep(pr, workspace_path)
                    findings.extend(semgrep_findings)
                    result.tool_warnings.extend(semgrep_warnings)

                if self.settings.enable_linting:
                    lint_findings, lint_warnings = run_linting(pr, workspace_path)
                    findings.extend(lint_findings)
                    result.tool_warnings.extend(lint_warnings)

                if self.settings.enable_ast_analysis:
                    ast_findings, ast_warnings = run_ast_analysis(pr)
                    findings.extend(ast_findings)
                    result.tool_warnings.extend(ast_warnings)

                findings.extend(RulesReviewer(self.settings).review(pr))
                findings.extend(BugReviewer(self.settings).review(pr))
                findings.extend(SecurityReviewer(self.settings).review(pr))
                findings.extend(TestingReviewer(self.settings).review(pr))

                findings = ReviewSynthesizer(self.settings).deduplicate_findings(findings)
                findings = FixSuggestionReviewer().enhance(findings, pr)
                summary_markdown = ReviewSynthesizer(self.settings).build_summary(pr, findings)

                result.findings = findings
                result.summary_markdown = summary_markdown
                result.review_body = summary_markdown

            poster.publish(result)
            history = ReviewHistoryService(self.settings)
            result.review_id = history.save_review(result=result, source=source)
            return result
        except Exception as exc:
            if result.check_run_id:
                poster.fail_check_run(owner=pr.owner, repo=pr.repo, check_run_id=result.check_run_id, error_message=str(exc))
            raise