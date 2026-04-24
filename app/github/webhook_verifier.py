import hashlib
import hmac


def verify_webhook_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    if not secret:
        return True

    if not signature_header:
        return False

    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header) 