from pydantic import BaseModel, Field

from app.schemas.finding import Finding
from app.schemas.pr_models import PullRequestContext


class ReviewResult(BaseModel):
    pr: PullRequestContext
    findings: list[Finding] = Field(default_factory=list)
    summary_markdown: str = ""
    review_body: str = ""
    check_run_id: int | None = None
    conclusion: str = "neutral"
    review_id: int | None = None
    tool_warnings: list[str] = Field(default_factory=list)