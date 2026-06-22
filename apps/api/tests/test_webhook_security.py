import hashlib
import hmac

from app.webhooks.security import verify_github_signature


def test_accepts_valid_github_signature() -> None:
    payload = b'{"action":"completed"}'
    signature = "sha256=" + hmac.new(b"test-secret", payload, hashlib.sha256).hexdigest()

    assert verify_github_signature(payload, signature, "test-secret") is True


def test_rejects_missing_invalid_or_modified_signatures() -> None:
    assert verify_github_signature(b"payload", None, "secret") is False
    assert verify_github_signature(b"payload", "sha256=invalid", "secret") is False
    valid_for_other_payload = "sha256=" + hmac.new(
        b"secret", b"other", hashlib.sha256
    ).hexdigest()
    assert verify_github_signature(b"payload", valid_for_other_payload, "secret") is False
