from app.rules.loader import RulesLoader
from app.rules.matcher import added_lines_matching_pattern, path_matches_any
from app.schemas.finding import Finding
from app.schemas.pr_models import PullRequestContext


class PolicyEngine:
    def __init__(self) -> None:
        self.loader = RulesLoader()

    def evaluate(self, pr: PullRequestContext) -> list[Finding]:
        config = self.loader.load(pr.rules_config)
        findings: list[Finding] = []
        changed_paths = [item.path for item in pr.changed_files]
        has_tests = any(self._looks_like_test(path) for path in changed_paths)

        for rule in config.path_rules:
            matching_files = [item for item in pr.changed_files if path_matches_any(item.path, rule.paths)]
            if rule.require_tests and matching_files and not has_tests:
                target = matching_files[0]
                findings.append(
                    Finding(
                        category="policy",
                        title=rule.name,
                        severity=rule.minimum_severity,
                        file=target.path,
                        line_start=target.changed_lines[0] if target.changed_lines else 1,
                        line_end=target.changed_lines[0] if target.changed_lines else 1,
                        explanation=rule.message,
                        suggested_fix="Add or update tests covering this sensitive change before merging.",
                        source="rule",
                        evidence=[f"Matched path rule on {target.path}"],
                    )
                )

        for rule in config.pattern_rules:
            for changed_file in pr.changed_files:
                if rule.paths and not path_matches_any(changed_file.path, rule.paths):
                    continue
                matches = added_lines_matching_pattern(changed_file.added_lines, rule.pattern)
                if not matches:
                    continue
                first = matches[0]
                findings.append(
                    Finding(
                        category="policy",
                        title=rule.name,
                        severity=rule.severity,
                        file=changed_file.path,
                        line_start=first.line_number,
                        line_end=first.line_number,
                        explanation=rule.message,
                        suggested_fix="Update the changed code to satisfy the repository rule.",
                        source="rule",
                        evidence=[f"Pattern matched added line: {first.content.strip()[:120]}"],
                    )
                )

        return findings

    @staticmethod
    def _looks_like_test(path: str) -> bool:
        lowered = path.lower()
        return (
            "/test" in lowered
            or "/tests" in lowered
            or lowered.startswith("test")
            or lowered.endswith("_test.py")
            or lowered.endswith(".spec.ts")
            or lowered.endswith(".test.ts")
            or lowered.endswith(".spec.js")
            or lowered.endswith(".test.js")
        )