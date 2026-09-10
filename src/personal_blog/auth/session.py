import base64
import hashlib
import hmac
from datetime import UTC, datetime, timedelta

COOKIE_NAME = "clancy_session"
LOGIN_PATH = "/admin/login"

_SEPARATOR = "."


class InvalidSessionError(Exception):
    def __init__(self) -> None:
        super().__init__("invalid or expired session")


def issue_session(key: bytes, ttl: timedelta, now: datetime | None = None) -> str:
    expires_at = (now or _utc_now()) + ttl
    payload = str(int(expires_at.timestamp()))

    return f"{payload}{_SEPARATOR}{_sign(key, payload)}"


def verify_session(key: bytes, token: str, now: datetime | None = None) -> None:
    payload, separator, signature = token.partition(_SEPARATOR)
    if not separator or not payload or not signature:
        raise InvalidSessionError

    if not hmac.compare_digest(signature, _sign(key, payload)):
        raise InvalidSessionError

    try:
        expires_at = int(payload)
    except ValueError:
        raise InvalidSessionError from None

    if int((now or _utc_now()).timestamp()) > expires_at:
        raise InvalidSessionError


def verify_credentials(
    expected_username: str,
    expected_password: str,
    username: str,
    password: str,
) -> bool:
    username_matches = hmac.compare_digest(
        expected_username.encode(), username.encode()
    )
    password_matches = hmac.compare_digest(
        expected_password.encode(), password.encode()
    )

    return username_matches and password_matches


def _sign(key: bytes, payload: str) -> str:
    signature = hmac.new(key, payload.encode(), hashlib.sha256).digest()

    return base64.urlsafe_b64encode(signature).decode().rstrip("=")


def _utc_now() -> datetime:
    return datetime.now(UTC)
