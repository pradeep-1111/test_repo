from app.core.config import Settings
from app.rules.policy_engine import PolicyEngine
from app.schemas.finding import Finding
from app.schemas.pr_models import PullRequestContext


class RulesReviewer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.policy_engine = PolicyEngine()

    def review(self, pr: PullRequestContext) -> list[Finding]:
        return self.policy_engine.evaluate(pr)