import os
import re
from datetime import timedelta
from pathlib import Path
from typing import Annotated, Any

from dotenv import dotenv_values
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SESSION_KEY_LENGTH = 32

NonBlank = Annotated[str, Field(min_length=1)]

_WHOLE_SECONDS = re.compile(r"[+-]?\d+")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BLOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
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

    @field_validator("host", "title", "admin_user", "admin_password", mode="after")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @field_validator("content_dir", mode="after")
    @classmethod
    def reject_non_directory_content_dir(cls, value: Path) -> Path:
        if value.exists() and not value.is_dir():
            raise ValueError("must be a directory")
        return value

    @model_validator(mode="after")
    def reject_unknown_environment_variables(self) -> "Settings":
        prefix = self.model_config["env_prefix"]
        env_file = self.model_config["env_file"]
        dotenv_path = env_file if isinstance(env_file, (str, Path)) else None
        known = {f"{prefix}{name}".upper() for name in type(self).model_fields}

        # The env source silently drops unrecognised BLOG_*-prefixed keys
        # before they reach validation, so `extra="forbid"` alone can't
        # catch typos here — os.environ/.env must be inspected directly.
        candidates = {**dotenv_values(dotenv_path), **os.environ}
        unknown = sorted(
            key
            for key in candidates
            if key.upper().startswith(prefix) and key.upper() not in known
        )
        if unknown:
            raise ValueError(f"unknown settings: {', '.join(unknown)}")
        return self

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
