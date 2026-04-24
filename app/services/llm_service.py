import json

from openai import OpenAI

from app.core.config import Settings
from app.schemas.finding import Finding


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def review(self, *, category: str, prompt_data: dict) -> list[Finding]:
        if not self.client:
            return []

        system = (
            "You are a high-signal GitHub pull request reviewer. "
            "Return only a JSON array of findings. Each finding must include: "
            "category, title, severity, file, line_start, line_end, explanation, confidence, suggested_fix, evidence. "
            "Only report issues that are directly grounded in changed lines. "
            "Severity must be one of critical, high, medium, low."
        )
        user = json.dumps(prompt_data)
        response = self.client.responses.create(
            model=self.settings.openai_model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
        )
        text = getattr(response, "output_text", "") or "[]"
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return []
        findings: list[Finding] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            item.setdefault("category", category)
            item.setdefault("source", "ai")
            item.setdefault("confidence", 0.6)
            item.setdefault("evidence", [])
            try:
                findings.append(Finding.model_validate(item))
            except Exception:
                continue
        return findings