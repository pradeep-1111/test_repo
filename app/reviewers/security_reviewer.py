from app.core.config import Settings
from app.schemas.finding import Finding
from app.schemas.pr_models import PullRequestContext
from app.services.llm_service import LLMService


class SecurityReviewer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm = LLMService(settings)

    def review(self, pr: PullRequestContext) -> list[Finding]:
        prompt = {
            "goal": "Find security issues introduced by this pull request.",
            "pr_title": pr.title,
            "pr_body": pr.body,
            "files": [
                {
                    "path": item.path,
                    "patch": item.patch,
                    "changed_lines": item.changed_lines,
                    "semgrep_messages": item.semgrep_messages,
                    "ast_context": item.ast_context,
                }
                for item in pr.changed_files
            ],
        }
        return self.llm.review(category="security", prompt_data=prompt)