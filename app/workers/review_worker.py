from __future__ import annotations

import queue
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel

from app.core.config import get_settings
from app.orchestration.review_orchestrator import ReviewOrchestrator


class ReviewJob(BaseModel):
    job_id: str
    pr_url: str
    installation_id: int | None = None
    source: str = "webhook"
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    review_id: int | None = None
    error: str | None = None


class ReviewWorker:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._queue: queue.Queue[ReviewJob] = queue.Queue()
        self._jobs: dict[str, ReviewJob] = {}
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="mergeguard-review-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def enqueue(self, *, pr_url: str, installation_id: int | None, source: str) -> ReviewJob:
        job = ReviewJob(
            job_id=str(uuid.uuid4()),
            pr_url=pr_url,
            installation_id=installation_id,
            source=source,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._jobs[job.job_id] = job
        self._queue.put(job)
        return job

    def list_jobs(self) -> list[ReviewJob]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda item: item.created_at, reverse=True)

    def get_job(self, job_id: str) -> ReviewJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def _run(self) -> None:
        orchestrator = ReviewOrchestrator(self.settings)
        while not self._stop_event.is_set():
            try:
                job = self._queue.get(timeout=self.settings.queue_poll_interval_seconds)
            except queue.Empty:
                continue

            self._update_job(job.job_id, status="running", started_at=datetime.now(timezone.utc).isoformat())
            try:
                result = orchestrator.review_pr(
                    pr_url=job.pr_url,
                    installation_id=job.installation_id,
                    source=job.source,
                )
                self._update_job(
                    job.job_id,
                    status="completed",
                    finished_at=datetime.now(timezone.utc).isoformat(),
                    review_id=result.review_id,
                )
            except Exception as exc:  # pragma: no cover - operational path
                self._update_job(
                    job.job_id,
                    status="failed",
                    finished_at=datetime.now(timezone.utc).isoformat(),
                    error=str(exc),
                )
            finally:
                self._queue.task_done()
                time.sleep(0.01)

    def _update_job(self, job_id: str, **updates: object) -> None:
        with self._lock:
            current = self._jobs[job_id]
            self._jobs[job_id] = current.model_copy(update=updates)


_worker: ReviewWorker | None = None


def get_review_worker() -> ReviewWorker:
    global _worker
    if _worker is None:
        _worker = ReviewWorker()
    return _worker