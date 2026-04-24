from pydantic import BaseModel, Field


class Finding(BaseModel):
    category: str
    title: str
    severity: str = Field(pattern="^(critical|high|medium|low)$")
    file: str
    line_start: int
    line_end: int
    explanation: str
    confidence: float = 0.5
    suggested_fix: str | None = None
    suggested_code: str | None = None
    review_comment_body: str | None = None
    evidence: list[str] = Field(default_factory=list)
    source: str = "ai"
    fingerprint: str | None = None