from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = Field(default="development", alias="ENV")
    port: int = Field(default=8000, alias="PORT")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")

    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    github_app_id: str | None = Field(default=None, alias="GITHUB_APP_ID")
    github_app_private_key_path: str | None = Field(default=None, alias="GITHUB_APP_PRIVATE_KEY_PATH")
    github_app_private_key: str | None = Field(default=None, alias="GITHUB_APP_PRIVATE_KEY")
    github_webhook_secret: str | None = Field(default=None, alias="GITHUB_WEBHOOK_SECRET")

    post_summary_to_github: bool = Field(default=True, alias="POST_SUMMARY_TO_GITHUB")
    post_inline_comments: bool = Field(default=True, alias="POST_INLINE_COMMENTS")
    post_check_run: bool = Field(default=True, alias="POST_CHECK_RUN")
    enable_one_click_suggestions: bool = True
    min_fix_confidence: float = 0.85
    enable_semgrep: bool = Field(default=True, alias="ENABLE_SEMGREP")
    enable_linting: bool = Field(default=True, alias="ENABLE_LINTING")
    enable_ast_analysis: bool = Field(default=True, alias="ENABLE_AST_ANALYSIS")
    merge_block_min_severity: str = Field(default="high", alias="MERGE_BLOCK_MIN_SEVERITY")
    max_inline_comments: int = Field(default=10, alias="MAX_INLINE_COMMENTS")
    max_summary_findings: int = Field(default=12, alias="MAX_SUMMARY_FINDINGS")
    max_check_annotations: int = Field(default=20, alias="MAX_CHECK_ANNOTATIONS")
    history_db_path: Path = Field(default=Path(".cache/review_history.db"), alias="HISTORY_DB_PATH")
    queue_poll_interval_seconds: float = Field(default=0.25, alias="QUEUE_POLL_INTERVAL_SECONDS")

    @property
    def github_app_configured(self) -> bool:
        return bool(self.github_app_id and (self.github_app_private_key or self.github_app_private_key_path))

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings() 