from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.schemas.review_result import ReviewResult


class ReviewHistoryService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db_path = Path(settings.history_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_full_name TEXT NOT NULL,
                    pr_number INTEGER NOT NULL,
                    pr_url TEXT NOT NULL,
                    head_sha TEXT NOT NULL,
                    conclusion TEXT NOT NULL,
                    findings_count INTEGER NOT NULL,
                    summary_markdown TEXT NOT NULL,
                    source TEXT NOT NULL,
                    tool_warnings_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    review_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    file TEXT NOT NULL,
                    line_start INTEGER NOT NULL,
                    line_end INTEGER NOT NULL,
                    explanation TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    suggested_fix TEXT,
                    suggested_code TEXT,
                    source TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    fingerprint TEXT,
                    FOREIGN KEY(review_id) REFERENCES reviews(id)
                )
                """
            )
            conn.commit()

    def save_review(self, *, result: ReviewResult, source: str) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO reviews (repo_full_name, pr_number, pr_url, head_sha, conclusion, findings_count, summary_markdown, source, tool_warnings_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"{result.pr.owner}/{result.pr.repo}",
                    result.pr.number,
                    result.pr.pr_url,
                    result.pr.head_sha,
                    result.conclusion,
                    len(result.findings),
                    result.summary_markdown,
                    source,
                    json.dumps(result.tool_warnings),
                ),
            )
            review_id = int(cursor.lastrowid)
            for finding in result.findings:
                conn.execute(
                    """
                    INSERT INTO findings (
                        review_id, category, title, severity, file, line_start, line_end,
                        explanation, confidence, suggested_fix, suggested_code, source, evidence_json, fingerprint
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        review_id,
                        finding.category,
                        finding.title,
                        finding.severity,
                        finding.file,
                        finding.line_start,
                        finding.line_end,
                        finding.explanation,
                        finding.confidence,
                        finding.suggested_fix,
                        finding.suggested_code,
                        finding.source,
                        json.dumps(finding.evidence),
                        finding.fingerprint,
                    ),
                )
            conn.commit()
            return review_id

    def list_reviews(self, *, limit: int = 25) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, repo_full_name, pr_number, pr_url, head_sha, conclusion, findings_count, source, created_at
                FROM reviews
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [
                {
                    "review_id": row["id"],
                    "repo_full_name": row["repo_full_name"],
                    "pr_number": row["pr_number"],
                    "pr_url": row["pr_url"],
                    "head_sha": row["head_sha"],
                    "conclusion": row["conclusion"],
                    "findings_count": row["findings_count"],
                    "source": row["source"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]

    def get_review(self, review_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            review = conn.execute(
                """
                SELECT id, repo_full_name, pr_number, pr_url, head_sha, conclusion, findings_count, summary_markdown, source, tool_warnings_json, created_at
                FROM reviews
                WHERE id = ?
                """,
                (review_id,),
            ).fetchone()
            if not review:
                return None
            findings = conn.execute(
                """
                SELECT category, title, severity, file, line_start, line_end, explanation, confidence, suggested_fix, suggested_code, source, evidence_json, fingerprint
                FROM findings
                WHERE review_id = ?
                ORDER BY id ASC
                """,
                (review_id,),
            ).fetchall()
            return {
                "review_id": review["id"],
                "repo_full_name": review["repo_full_name"],
                "pr_number": review["pr_number"],
                "pr_url": review["pr_url"],
                "head_sha": review["head_sha"],
                "conclusion": review["conclusion"],
                "findings_count": review["findings_count"],
                "summary_markdown": review["summary_markdown"],
                "source": review["source"],
                "tool_warnings": json.loads(review["tool_warnings_json"]),
                "created_at": review["created_at"],
                "findings": [
                    {
                        "category": row["category"],
                        "title": row["title"],
                        "severity": row["severity"],
                        "file": row["file"],
                        "line_start": row["line_start"],
                        "line_end": row["line_end"],
                        "explanation": row["explanation"],
                        "confidence": row["confidence"],
                        "suggested_fix": row["suggested_fix"],
                        "suggested_code": row["suggested_code"],
                        "source": row["source"],
                        "evidence": json.loads(row["evidence_json"]),
                        "fingerprint": row["fingerprint"],
                    }
                    for row in findings
                ],
            }