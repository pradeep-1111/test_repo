from app.rules.policy_engine import PolicyEngine
from app.schemas.pr_models import AddedLine, ChangedFile, PullRequestContext


ENGINE = PolicyEngine()


def test_pattern_rule_matches_added_lines_only() -> None:
    pr = PullRequestContext(
        owner="o",
        repo="r",
        number=1,
        title="t",
        body="",
        pr_url="https://github.com/o/r/pull/1",
        base_sha="a",
        head_sha="b",
        rules_config={
            "pattern_rules": [
                {
                    "name": "No execute",
                    "pattern": r"execute\(",
                    "message": "Avoid execute in changed code",
                    "severity": "high",
                }
            ]
        },
        changed_files=[
            ChangedFile(
                path="src/app.py",
                status="modified",
                patch="",
                head_content="existing = execute('old')\nnew = ok()\n",
                changed_lines=[2],
                added_lines=[AddedLine(line_number=2, content="new = ok()")],
            )
        ],
    )
    findings = ENGINE.evaluate(pr)
    assert findings == []


def test_pattern_rule_matches_newly_added_risky_line() -> None:
    pr = PullRequestContext(
        owner="o",
        repo="r",
        number=1,
        title="t",
        body="",
        pr_url="https://github.com/o/r/pull/1",
        base_sha="a",
        head_sha="b",
        rules_config={
            "pattern_rules": [
                {
                    "name": "No execute",
                    "pattern": r"execute\(",
                    "message": "Avoid execute in changed code",
                    "severity": "high",
                }
            ]
        },
        changed_files=[
            ChangedFile(
                path="src/app.py",
                status="modified",
                patch="",
                head_content="existing = ok()\nnew = execute('new')\n",
                changed_lines=[2],
                added_lines=[AddedLine(line_number=2, content="new = execute('new')")],
            )
        ],
    )
    findings = ENGINE.evaluate(pr)
    assert len(findings) == 1
    assert findings[0].line_start == 2