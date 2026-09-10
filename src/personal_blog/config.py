import re
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SESSION_KEY_LENGTH = 32

NonBlank = Annotated[str, Field(min_length=1)]

_WHOLE_SECONDS = re.compile(r"[+-]?\d+")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BLOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = Field(default=8080, ge=1, le=65535)
    title: NonBlank = "Personal Blog"
    content_dir: Path = Path("content")

    admin_user: NonBlank
    admin_password: NonBlank
    session_key: str = Field(min_length=MIN_SESSION_KEY_LENGTH)
    session_ttl: timedelta = timedelta(hours=24)

    @property
    def session_key_bytes(self) -> bytes:
        return self.session_key.encode()

    @field_validator("title", "admin_user", "admin_password", mode="after")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("session_ttl", mode="before")
    @classmethod
    def accept_whole_seconds(cls, value: Any) -> Any:
        if isinstance(value, str) and _WHOLE_SECONDS.fullmatch(value.strip()):
            return int(value)
        return value

    @field_validator("session_ttl", mode="after")
    @classmethod
    def reject_non_positive_ttl(cls, value: timedelta) -> timedelta:
        if value <= timedelta(0):
            raise ValueError("must be positive")
        return value
