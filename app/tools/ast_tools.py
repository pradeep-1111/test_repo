from __future__ import annotations

import ast
from dataclasses import dataclass

from app.schemas.finding import Finding
from app.schemas.pr_models import PullRequestContext


@dataclass
class AstIssue:
    title: str
    severity: str
    message: str
    line: int
    evidence: str


def run_ast_analysis(pr: PullRequestContext) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    warnings: list[str] = []

    for changed_file in pr.changed_files:
        if not changed_file.path.endswith(".py"):
            continue
        if not changed_file.head_content.strip():
            continue
        try:
            tree = ast.parse(changed_file.head_content)
        except SyntaxError as exc:
            line = exc.lineno or 1
            findings.append(
                Finding(
                    category="ast",
                    title="Python syntax error",
                    severity="high",
                    file=changed_file.path,
                    line_start=line,
                    line_end=line,
                    explanation=exc.msg,
                    confidence=0.95,
                    source="ast",
                    evidence=[f"Syntax error near line {line}"],
                )
            )
            warnings.append(f"AST parse failed for {changed_file.path}: {exc.msg}")
            continue

        changed_lines = set(changed_file.changed_lines)
        issues = _collect_ast_issues(tree, changed_file.head_content)
        for issue in issues:
            if changed_lines and issue.line not in changed_lines:
                continue
            changed_file.ast_context.append(
                {
                    "title": issue.title,
                    "line": issue.line,
                    "message": issue.message,
                    "evidence": issue.evidence,
                }
            )
            findings.append(
                Finding(
                    category="security",
                    title=issue.title,
                    severity=issue.severity,
                    file=changed_file.path,
                    line_start=issue.line,
                    line_end=issue.line,
                    explanation=issue.message,
                    confidence=0.9,
                    source="ast",
                    evidence=[issue.evidence],
                )
            )
    return findings, warnings


def _collect_ast_issues(tree: ast.AST, source: str) -> list[AstIssue]:
    issues: list[AstIssue] = []
    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            line = getattr(node, "lineno", 1)
            code = lines[line - 1].strip() if 0 < line <= len(lines) else name

            if name in {"eval", "builtins.eval"}:
                issues.append(AstIssue("Use of eval", "high", "Avoid eval on dynamic input.", line, code))
            elif name in {"exec", "builtins.exec"}:
                issues.append(AstIssue("Use of exec", "high", "Avoid exec on dynamic input.", line, code))
            elif name in {"pickle.load", "pickle.loads"}:
                issues.append(AstIssue("Unsafe pickle usage", "high", "pickle can execute arbitrary code during deserialization.", line, code))
            elif name == "yaml.load":
                issues.append(AstIssue("Unsafe yaml.load", "high", "Use yaml.safe_load unless the source is fully trusted.", line, code))

            if name.startswith("subprocess"):
                for keyword in node.keywords:
                    if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                        issues.append(AstIssue("subprocess with shell=True", "high", "shell=True expands command injection risk.", line, code))

            if name.startswith("requests"):
                for keyword in node.keywords:
                    if keyword.arg == "verify" and isinstance(keyword.value, ast.Constant) and keyword.value.value is False:
                        issues.append(AstIssue("TLS verification disabled", "high", "verify=False disables certificate validation.", line, code))

        if isinstance(node, ast.ExceptHandler) and node.type is None:
            line = getattr(node, "lineno", 1)
            code = lines[line - 1].strip() if 0 < line <= len(lines) else "except:"
            issues.append(AstIssue("Bare except", "medium", "Bare except may hide real failures and break rollback visibility.", line, code))

    return issues


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts: list[str] = []
        current = func
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return "unknown"