from pydantic import BaseModel, Field


class AddedLine(BaseModel):
    line_number: int
    content: str


class DiffHunk(BaseModel):
    start_line: int
    end_line: int
    added_lines: list[AddedLine] = Field(default_factory=list)


class ChangedFile(BaseModel):
    path: str
    status: str
    patch: str = ""
    head_content: str = ""
    changed_lines: list[int] = Field(default_factory=list)
    added_lines: list[AddedLine] = Field(default_factory=list)
    diff_hunks: list[DiffHunk] = Field(default_factory=list)
    semgrep_messages: list[str] = Field(default_factory=list)
    linter_messages: list[str] = Field(default_factory=list)
    ast_context: list[dict] = Field(default_factory=list)


class PullRequestContext(BaseModel):
    owner: str
    repo: str
    number: int
    title: str
    body: str
    pr_url: str
    base_sha: str
    head_sha: str
    changed_files: list[ChangedFile] = Field(default_factory=list)
    rules_config: dict = Field(default_factory=dict)