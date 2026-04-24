import hashlib
from collections import defaultdict

from app.core.config import Settings
from app.schemas.finding import Finding
from app.schemas.pr_models import PullRequestContext


class ReviewSynthesizer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def deduplicate_findings(self, findings: list[Finding]) -> list[Finding]:
        buckets: dict[str, Finding] = {}
        for finding in findings:
            fingerprint = finding.fingerprint or self._fingerprint(finding)
            current = buckets.get(fingerprint)
            if not current or self._score(finding) > self._score(current):
                buckets[fingerprint] = finding.model_copy(update={"fingerprint": fingerprint})
        ordered = sorted(buckets.values(), key=self._sort_key, reverse=True)
        return ordered[: self.settings.max_summary_findings]

    def build_summary(self, pr: PullRequestContext, findings: list[Finding]) -> str:
        lines = [
            f"## MergeGuard review for {pr.owner}/{pr.repo}#{pr.number}",
            "",
            f"**PR:** {pr.title}",
            f"**Changed files:** {len(pr.changed_files)}",
            f"**Findings:** {len(findings)}",
            "",
        ]
        if not findings:
            lines.append("✅ No high-signal issues found. MergeGuard did not detect merge-blocking risk in the changed lines.")
            return "\n".join(lines)

        by_severity: dict[str, list[Finding]] = defaultdict(list)
        for finding in findings:
            by_severity[finding.severity].append(finding)

        for severity in ["critical", "high", "medium", "low"]:
            items = by_severity.get(severity)
            if not items:
                continue
            lines.append(f"### {severity.title()} ({len(items)})")
            for finding in items:
                lines.append(
                    f"- **{finding.title}** in `{finding.file}:{finding.line_start}` — {finding.explanation}"
                )
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _fingerprint(finding: Finding) -> str:
        key = f"{finding.category}|{finding.title}|{finding.file}|{finding.line_start}|{finding.explanation}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _score(finding: Finding) -> float:
        severity_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}[finding.severity]
        return severity_weight + finding.confidence

    @staticmethod
    def _sort_key(finding: Finding) -> tuple:
        severity_weight = {"critical": 4, "high": 3, "medium": 2, "low": 1}[finding.severity]
        return severity_weight, finding.confidence, -finding.line_start