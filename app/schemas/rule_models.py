from pydantic import BaseModel, Field


class PathRule(BaseModel):
    name: str
    paths: list[str] = Field(default_factory=list)
    require_tests: bool = False
    minimum_severity: str = "medium"
    message: str


class PatternRule(BaseModel):
    name: str
    pattern: str
    paths: list[str] = Field(default_factory=list)
    severity: str = "high"
    message: str


class MergeGuardConfig(BaseModel):
    path_rules: list[PathRule] = Field(default_factory=list)
    pattern_rules: list[PatternRule] = Field(default_factory=list)