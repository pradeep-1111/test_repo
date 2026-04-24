from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from app.schemas.finding import Finding
from app.schemas.pr_models import PullRequestContext


FALLBACK_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "Potential hardcoded AWS access key", "critical"),
    (re.compile(r"yaml\.load\("), "Unsafe yaml.load detected", "high"),
    (re.compile(r"shell\s*=\s*True"), "subprocess invoked with shell=True", "high"),
    (re.compile(r"verify\s*=\s*False"), "TLS verification disabled", "high"),
    (re.compile(r"\beval\("), "eval detected", "high"),
    (re.compile(r"\bexec\("), "exec detected", "high"),
]


def run_semgrep(pr: PullRequestContext, workspace_path: Path) -> tuple[list[Finding], list[str]]:
    if not shutil.which("semgrep"):
        return _fallback_scan(pr), ["Semgrep not installed; used fallback pattern scanner instead."]

    command = [
        "semgrep",
        "scan",
        "--config",
        "auto",
        "--json",
        str(workspace_path),
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if proc.returncode not in {0, 1}:
        return [], [f"Semgrep failed: {proc.stderr.strip()[:500]}"]

    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return [], ["Semgrep output could not be parsed as JSON."]

    findings: list[Finding] = []
    path_lookup = {item.path: item for item in pr.changed_files}
    for result in payload.get("results", []):
        path = result.get("path", "")
        relative_path = _relative_path(path, workspace_path)
        changed_file = path_lookup.get(relative_path)
        if not changed_file:
            continue
        start = int(result.get("start", {}).get("line", 1))
        if changed_file.changed_lines and start not in set(changed_file.changed_lines):
            continue
        message = result.get("extra", {}).get("message") or result.get("check_id") or "Semgrep finding"
        severity = _normalize_severity(result.get("extra", {}).get("severity", "WARNING"))
        findings.append(
            Finding(
                category="security",
                title="Semgrep detected a risky change",
                severity=severity,
                file=relative_path,
                line_start=start,
                line_end=int(result.get("end", {}).get("line", start)),
                explanation=message,
                confidence=0.9,
                source="semgrep",
                evidence=[result.get("check_id", "semgrep-auto")],
            )
        )
        changed_file.semgrep_messages.append(message)
    return findings, []


def _fallback_scan(pr: PullRequestContext) -> list[Finding]:
    findings: list[Finding] = []
    for changed_file in pr.changed_files:
        for added in changed_file.added_lines:
            for pattern, message, severity in FALLBACK_PATTERNS:
                if not pattern.search(added.content):
                    continue
                changed_file.semgrep_messages.append(message)
                findings.append(
                    Finding(
                        category="security",
                        title=message,
                        severity=severity,
                        file=changed_file.path,
                        line_start=added.line_number,
                        line_end=added.line_number,
                        explanation=message,
                        confidence=0.8,
                        source="fallback-static",
                        evidence=[added.content.strip()[:160]],
                    )
                )
    return findings


def _normalize_severity(severity: str) -> str:
    normalized = severity.lower()
    if normalized in {"error", "critical"}:
        return "critical"
    if normalized in {"warning", "high"}:
        return "high"
    if normalized in {"info", "medium"}:
        return "medium"
    return "low"


def _relative_path(path: str, workspace_path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(workspace_path.resolve()))
    except Exception:
        return str(Path(path))