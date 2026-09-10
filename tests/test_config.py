from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from personal_blog.config import MIN_SESSION_KEY_LENGTH, Settings

VALID_ENVIRONMENT = {
    "BLOG_ADMIN_USER": "clancy",
    "BLOG_ADMIN_PASSWORD": "trench",
    "BLOG_SESSION_KEY": "k" * MIN_SESSION_KEY_LENGTH,
}


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in [
        "BLOG_HOST",
        "BLOG_PORT",
        "BLOG_CONTENT_DIR",
        "BLOG_TITLE",
        "BLOG_ADMIN_USER",
        "BLOG_ADMIN_PASSWORD",
        "BLOG_SESSION_KEY",
        "BLOG_SESSION_TTL",
    ]:
        monkeypatch.delenv(variable, raising=False)


def load(monkeypatch: pytest.MonkeyPatch, **overrides: str) -> Settings:
    for name, value in {**VALID_ENVIRONMENT, **overrides}.items():
        monkeypatch.setenv(name, value)

    return Settings()


class TestDefaults:
    def test_applies_defaults_for_optional_settings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        settings = load(monkeypatch)

        assert settings.host == "127.0.0.1"
        assert settings.port == 8080
        assert settings.title == "Personal Blog"
        assert settings.content_dir.name == "content"
        assert settings.session_ttl == timedelta(hours=24)

    def test_reads_overrides_from_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        settings = load(
            monkeypatch,
            BLOG_PORT="9000",
            BLOG_TITLE="Trench Dispatch",
            BLOG_CONTENT_DIR="/srv/articles",
        )

        assert settings.port == 9000
        assert settings.title == "Trench Dispatch"
        assert str(settings.content_dir) == "/srv/articles"

    def test_exposes_the_session_key_as_bytes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        settings = load(monkeypatch)

        assert settings.session_key_bytes == ("k" * MIN_SESSION_KEY_LENGTH).encode()


class TestValidation:
    @pytest.mark.parametrize(
        "variable", ["BLOG_ADMIN_USER", "BLOG_ADMIN_PASSWORD", "BLOG_SESSION_KEY"]
    )
    def test_requires_every_secret(
        self, monkeypatch: pytest.MonkeyPatch, variable: str
    ) -> None:
        environment = {
            name: value for name, value in VALID_ENVIRONMENT.items() if name != variable
        }
        for name, value in environment.items():
            monkeypatch.setenv(name, value)

        with pytest.raises(ValidationError):
            Settings()

    def test_rejects_a_short_session_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with pytest.raises(ValidationError):
            load(monkeypatch, BLOG_SESSION_KEY="k" * (MIN_SESSION_KEY_LENGTH - 1))

    def test_rejects_a_blank_title(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with pytest.raises(ValidationError):
            load(monkeypatch, BLOG_TITLE="   ")

    def test_rejects_a_blank_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with pytest.raises(ValidationError):
            load(monkeypatch, BLOG_HOST="   ")

    def test_rejects_a_content_dir_that_is_a_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        blocked = tmp_path / "content"
        blocked.write_text("not a directory")

        with pytest.raises(ValidationError):
            load(monkeypatch, BLOG_CONTENT_DIR=str(blocked))

    def test_rejects_unknown_environment_variables(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with pytest.raises(ValidationError):
            load(monkeypatch, BLOG_UNKNOWN_SETTING="whatever")

    @pytest.mark.parametrize("ttl", ["0", "-3600", "not-a-duration"])
    def test_rejects_a_non_positive_session_ttl(
        self, monkeypatch: pytest.MonkeyPatch, ttl: str
    ) -> None:
        with pytest.raises(ValidationError):
            load(monkeypatch, BLOG_SESSION_TTL=ttl)

    def test_accepts_a_session_ttl_in_seconds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        settings = load(monkeypatch, BLOG_SESSION_TTL="3600")

        assert settings.session_ttl == timedelta(hours=1)

    def test_reports_every_problem_at_once(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BLOG_SESSION_KEY", "short")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        reported = {error["loc"][0] for error in exc_info.value.errors()}
        assert reported == {"admin_user", "admin_password", "session_key"}
