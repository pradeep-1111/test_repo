from app.core.config import Settings
from app.schemas.finding import Finding
from app.schemas.pr_models import PullRequestContext
from app.services.llm_service import LLMService
from app.tools.test_detector import looks_like_test_file


class TestingReviewer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm = LLMService(settings)

    def review(self, pr: PullRequestContext) -> list[Finding]:
        prompt = {
            "goal": "Find missing test coverage risks in this pull request.",
            "pr_title": pr.title,
            "pr_body": pr.body,
            "files": [{"path": item.path, "patch": item.patch} for item in pr.changed_files],
        }
        findings = self.llm.review(category="testing", prompt_data=prompt)
        if findings:
            return findings

        changed_code_files = [
            item
            for item in pr.changed_files
            if not looks_like_test_file(item.path)
            and item.path.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".rb"))
        ]
        has_tests = any(looks_like_test_file(item.path) for item in pr.changed_files)
        if changed_code_files and not has_tests:
            target = changed_code_files[0]
            line_number = target.changed_lines[0] if target.changed_lines else 1
            return [
                Finding(
                    category="testing",
                    title="Code changed without corresponding tests",
                    severity="medium",
                    file=target.path,
                    line_start=line_number,
                    line_end=line_number,
                    explanation="Application code changed, but no test files were updated in this pull request.",
                    confidence=0.75,
                    suggested_fix="Add or update tests that cover the changed behavior before merging.",
                    source="heuristic",
                    evidence=[f"Changed code files: {', '.join(item.path for item in changed_code_files[:5])}"],
                )
            ]
        return []