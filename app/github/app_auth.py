from __future__ import annotations

import time
from pathlib import Path

import jwt
import requests

from app.core.config import Settings


def _get_private_key(settings: Settings) -> str:
    if settings.github_app_private_key:
        return settings.github_app_private_key

    if settings.github_app_private_key_path:
        return Path(settings.github_app_private_key_path).read_text(encoding="utf-8")

    raise RuntimeError("GitHub App private key is not configured")


def build_app_jwt(settings: Settings) -> str:
    if not settings.github_app_id:
        raise RuntimeError("GitHub App ID is not configured")

    private_key = _get_private_key(settings)
    now = int(time.time())

    payload = {
        "iat": now - 60,
        "exp": now + 600,
        "iss": settings.github_app_id,
    }

    return jwt.encode(payload, private_key, algorithm="RS256")


def build_installation_token(*, settings: Settings, installation_id: int) -> str:
    app_jwt = build_app_jwt(settings)

    response = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    token = data.get("token")
    if not token:
        raise RuntimeError("GitHub installation token was not returned by GitHub")

    return token