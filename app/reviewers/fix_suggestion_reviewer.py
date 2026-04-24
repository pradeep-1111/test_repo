from __future__ import annotations

from app.schemas.finding import Finding
from app.schemas.pr_models import PullRequestContext


class FixSuggestionReviewer:
    """
    Adds GitHub one-click suggested changes to findings when the fix is
    deterministic and applies to a changed line in the PR diff.
    """

    def enhance(self, findings: list[Finding], pr: PullRequestContext) -> list[Finding]:
        enhanced: list[Finding] = []

        line_lookup: dict[tuple[str, int], str] = {}
        for changed_file in pr.changed_files:
            for added_line in changed_file.added_lines:
                line_lookup[(changed_file.path, added_line.line_number)] = added_line.content

        for finding in findings:
            original_line = line_lookup.get((finding.file, finding.line_start))
            suggestion = finding.suggested_fix
            suggested_code = finding.suggested_code

            if original_line:
                auto_fix = self._safe_fix_for_line(original_line)
                if auto_fix:
                    suggestion, suggested_code = auto_fix

            review_comment_body = self._build_comment_body(
                finding=finding,
                suggestion=suggestion,
                suggested_code=suggested_code,
            )

            enhanced.append(
                finding.model_copy(
                    update={
                        "suggested_fix": suggestion,
                        "suggested_code": suggested_code,
                        "review_comment_body": review_comment_body,
                    }
                )
            )

        return enhanced

    def _safe_fix_for_line(self, line: str) -> tuple[str, str] | None:
        stripped = line.strip()

        if "yaml.load(" in line and "safe_load" not in line:
            return (
                "Use yaml.safe_load instead of yaml.load.",
                line.replace("yaml.load(", "yaml.safe_load("),
            )

        if "verify=False" in line:
            return (
                "Do not disable TLS certificate verification.",
                line.replace("verify=False", "timeout=10"),
            )

        if "shell=True" in line:
            return (
                "Avoid shell=True unless it is strictly required.",
                line.replace("shell=True", "shell=False"),
            )

        if "hashlib.md5(" in line:
            return (
                "Use SHA-256 instead of MD5 for security-sensitive hashing.",
                line.replace("hashlib.md5(", "hashlib.sha256("),
            )

        if "hashlib.sha1(" in line:
            return (
                "Use SHA-256 instead of SHA-1 for security-sensitive hashing.",
                line.replace("hashlib.sha1(", "hashlib.sha256("),
            )

        if stripped.startswith("eval(") or " eval(" in line:
            return (
                "Avoid eval because it can execute arbitrary code.",
                line.replace("eval(", "ast.literal_eval("),
            )

        return None

    def _build_comment_body(
        self,
        *,
        finding: Finding,
        suggestion: str | None,
        suggested_code: str | None,
    ) -> str:
        parts = [f"**{finding.title}**", "", finding.explanation]

        if finding.evidence:
            parts.append("")
            parts.append("Evidence:")
            parts.extend(f"- {item}" for item in finding.evidence)

        if suggestion:
            parts.append("")
            parts.append(f"Suggested fix: {suggestion}")

        if suggested_code:
            parts.append("")
            parts.append("```suggestion")
            parts.append(suggested_code)
            parts.append("```")

        return "\n".join(parts)