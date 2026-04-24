from app.core.config import Settings
from app.schemas.finding import Finding
from app.schemas.pr_models import PullRequestContext
from app.services.llm_service import LLMService


class BugReviewer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm = LLMService(settings)

    def review(self, pr: PullRequestContext) -> list[Finding]:
        prompt = {
            "goal": "Find merge-risk and bug-risk issues in this pull request.",
            "pr_title": pr.title,
            "pr_body": pr.body,
            "files": [
                {
                    "path": item.path,
                    "patch": item.patch,
                    "changed_lines": item.changed_lines,
                    "ast_context": item.ast_context,
                    "linter_messages": item.linter_messages,
                }
                for item in pr.changed_files
            ],
        }
        return self.llm.review(category="bug", prompt_data=prompt)