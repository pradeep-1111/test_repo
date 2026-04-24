from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from app.schemas.finding import Finding
from app.schemas.pr_models import PullRequestContext


RUFF_RULE_SEVERITY = {
    "E999": "high",
    "F821": "high",
    "F822": "high",
    "F823": "high",
}


def run_linting(pr: PullRequestContext, workspace_path: Path) -> tuple[list[Finding], list[str]]:
    if not shutil.which("ruff"):
        return [], ["ruff not installed; lint analysis skipped."]

    command = ["ruff", "check", str(workspace_path), "--output-format", "json"]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if proc.returncode not in {0, 1}:
        return [], [f"ruff failed: {proc.stderr.strip()[:500]}"]

    try:
        payload = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return [], ["ruff output could not be parsed as JSON."]

    findings: list[Finding] = []
    path_lookup = {item.path: item for item in pr.changed_files}
    for issue in payload:
        relative_path = _relative_path(issue.get("filename", ""), workspace_path)
        changed_file = path_lookup.get(relative_path)
        if not changed_file:
            continue
        row = int(issue.get("location", {}).get("row", 1))
        if changed_file.changed_lines and row not in set(changed_file.changed_lines):
            continue
        code = issue.get("code") or "ruff"
        message = issue.get("message") or "Lint issue detected"
        changed_file.linter_messages.append(f"{code}: {message}")
        findings.append(
            Finding(
                category="lint",
                title=f"Lint issue: {code}",
                severity=RUFF_RULE_SEVERITY.get(code, "medium"),
                file=relative_path,
                line_start=row,
                line_end=int(issue.get("end_location", {}).get("row", row)),
                explanation=message,
                confidence=0.8,
                source="ruff",
                evidence=[code],
            )
        )
    return findings, []


def _relative_path(path: str, workspace_path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(workspace_path.resolve()))
    except Exception:
        return str(Path(path))