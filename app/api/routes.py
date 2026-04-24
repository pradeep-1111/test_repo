from html import escape
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.orchestration.review_orchestrator import ReviewOrchestrator
from app.services.review_history import ReviewHistoryService
from app.workers.review_worker import get_review_worker

router = APIRouter()


class ReviewRequest(BaseModel):
    pr_url: str = Field(..., description="GitHub pull request URL")
    installation_id: int | None = Field(default=None)


@router.get("/health")
def health() -> dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "env": settings.env,
        "github_app_configured": settings.github_app_configured,
        "llm_enabled": settings.llm_enabled,
    }


@router.post("/review-pr")
def review_pr(request: ReviewRequest) -> dict[str, Any]:
    orchestrator = ReviewOrchestrator(get_settings())
    result = orchestrator.review_pr(pr_url=request.pr_url, installation_id=request.installation_id, source="manual")
    return {
        "ok": True,
        "summary": result.summary_markdown,
        "findings": [item.model_dump() for item in result.findings],
        "conclusion": result.conclusion,
        "review_id": result.review_id,
    }


@router.post("/review-pr/async")
def review_pr_async(request: ReviewRequest) -> dict[str, Any]:
    worker = get_review_worker()
    job = worker.enqueue(pr_url=request.pr_url, installation_id=request.installation_id, source="manual")
    return {"ok": True, "job_id": job.job_id, "status": job.status}


@router.get("/jobs")
def list_jobs() -> dict[str, Any]:
    worker = get_review_worker()
    return {"jobs": [job.model_dump() for job in worker.list_jobs()]}


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    worker = get_review_worker()
    job = worker.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.model_dump()


@router.get("/history/reviews")
def list_reviews(limit: int = 25) -> dict[str, Any]:
    history = ReviewHistoryService(get_settings())
    return {"reviews": history.list_reviews(limit=limit)}


@router.get("/history/reviews/{review_id}")
def get_review(review_id: int) -> dict[str, Any]:
    history = ReviewHistoryService(get_settings())
    review = history.get_review(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.get("/dashboard", response_model=None)
def dashboard() -> str:
    history = ReviewHistoryService(get_settings())
    reviews = history.list_reviews(limit=50)
    rows = []
    for review in reviews:
        rows.append(
            "<tr>"
            f"<td>{review['review_id']}</td>"
            f"<td>{escape(review['repo_full_name'])}</td>"
            f"<td><a href='{escape(review['pr_url'])}' target='_blank'>#{review['pr_number']}</a></td>"
            f"<td>{escape(review['head_sha'][:12])}</td>"
            f"<td>{escape(review['conclusion'])}</td>"
            f"<td>{review['findings_count']}</td>"
            f"<td>{escape(review['source'])}</td>"
            f"<td>{escape(review['created_at'])}</td>"
            "</tr>"
        )
    html = f"""
    <html>
      <head>
        <title>MergeGuard Dashboard</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 24px; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
          th {{ background: #f5f5f5; }}
        </style>
      </head>
      <body>
        <h1>MergeGuard Review History</h1>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Repo</th>
              <th>PR</th>
              <th>SHA</th>
              <th>Conclusion</th>
              <th>Findings</th>
              <th>Source</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </body>
    </html>
    """
    return html