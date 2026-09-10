import base64
import hashlib
import hmac
from datetime import UTC, datetime, timedelta

import pytest

from personal_blog.auth.session import (
    InvalidSessionError,
    issue_session,
    verify_credentials,
    verify_session,
)

KEY = b"a" * 32
OTHER_KEY = b"b" * 32
TTL = timedelta(hours=24)
NOW = datetime(2026, 2, 14, 12, 0, tzinfo=UTC)


def forge(payload: str, key: bytes = KEY) -> str:
    signature = hmac.new(key, payload.encode(), hashlib.sha256).digest()
    return f"{payload}.{base64.urlsafe_b64encode(signature).decode().rstrip('=')}"


class TestIssueSession:
    def test_encodes_the_expiry_as_a_unix_timestamp(self) -> None:
        payload, _, _ = issue_session(KEY, TTL, now=NOW).partition(".")

        assert int(payload) == int((NOW + TTL).timestamp())

    def test_pins_the_wire_format(self) -> None:
        expected_expiry = str(int((NOW + TTL).timestamp()))

        assert issue_session(KEY, TTL, now=NOW) == forge(expected_expiry)

    def test_different_keys_produce_different_signatures(self) -> None:
        assert issue_session(KEY, TTL, now=NOW) != issue_session(
            OTHER_KEY, TTL, now=NOW
        )


class TestVerifySession:
    def test_accepts_a_freshly_issued_token(self) -> None:
        verify_session(KEY, issue_session(KEY, TTL, now=NOW), now=NOW)

    def test_accepts_a_token_one_second_before_expiry(self) -> None:
        token = issue_session(KEY, TTL, now=NOW)

        verify_session(KEY, token, now=NOW + TTL - timedelta(seconds=1))

    def test_rejects_an_expired_token(self) -> None:
        token = issue_session(KEY, TTL, now=NOW)

        with pytest.raises(InvalidSessionError):
            verify_session(KEY, token, now=NOW + TTL + timedelta(seconds=1))

    def test_rejects_a_token_signed_with_another_key(self) -> None:
        with pytest.raises(InvalidSessionError):
            verify_session(KEY, issue_session(OTHER_KEY, TTL, now=NOW), now=NOW)

    def test_rejects_a_tampered_expiry(self) -> None:
        _, _, signature = issue_session(KEY, TTL, now=NOW).partition(".")
        extended = int((NOW + timedelta(days=3650)).timestamp())

        with pytest.raises(InvalidSessionError):
            verify_session(KEY, f"{extended}.{signature}", now=NOW)

    def test_rejects_a_tampered_signature(self) -> None:
        payload, _, signature = issue_session(KEY, TTL, now=NOW).partition(".")

        with pytest.raises(InvalidSessionError):
            verify_session(KEY, f"{payload}.{signature[:-1]}x", now=NOW)

    def test_rejects_a_validly_signed_non_numeric_payload(self) -> None:
        with pytest.raises(InvalidSessionError):
            verify_session(KEY, forge("not-a-timestamp"), now=NOW)

    @pytest.mark.parametrize(
        "token",
        [
            "",
            ".",
            "no-separator",
            "1770000000",
            f"{int(NOW.timestamp())}.",
            ".signature",
        ],
    )
    def test_rejects_malformed_tokens(self, token: str) -> None:
        with pytest.raises(InvalidSessionError):
            verify_session(KEY, token, now=NOW)


class TestVerifyCredentials:
    def test_accepts_the_exact_pair(self) -> None:
        assert verify_credentials("clancy", "trench", "clancy", "trench")

    @pytest.mark.parametrize(
        ("username", "password"),
        [
            ("wrong", "trench"),
            ("clancy", "wrong"),
            ("wrong", "wrong"),
            ("", ""),
            ("clancy", ""),
            ("Clancy", "trench"),
            ("clancy ", "trench"),
        ],
    )
    def test_rejects_anything_else(self, username: str, password: str) -> None:
        assert not verify_credentials("clancy", "trench", username, password)

    def test_handles_non_ascii_without_crashing(self) -> None:
        assert verify_credentials("caio", "señá", "caio", "señá")
        assert not verify_credentials("caio", "señá", "caio", "sena")
