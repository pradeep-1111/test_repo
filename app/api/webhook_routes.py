from fastapi import APIRouter, Header, HTTPException, Request

from app.core.config import get_settings
from app.github.webhook_verifier import verify_webhook_signature
from app.workers.review_worker import get_review_worker

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str = Header(default=""),
) -> dict:
    settings = get_settings()
    payload = await request.body()

    if settings.github_webhook_secret:
        if not verify_webhook_signature(payload, x_hub_signature_256, settings.github_webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event = await request.json()

    if x_github_event != "pull_request":
        return {"ok": True, "ignored": True, "reason": "unsupported_event"}

    action = event.get("action")
    if action not in {"opened", "reopened", "synchronize"}:
        return {"ok": True, "ignored": True, "reason": f"unsupported_action:{action}"}

    pull_request = event.get("pull_request") or {}
    pr_url = pull_request.get("html_url")
    installation = event.get("installation") or {}
    installation_id = installation.get("id")

    if not pr_url:
        return {"ok": True, "ignored": True, "reason": "missing_pr_url"}

    job = get_review_worker().enqueue(pr_url=pr_url, installation_id=installation_id, source="webhook")
    return {"ok": True, "queued": True, "job_id": job.job_id}