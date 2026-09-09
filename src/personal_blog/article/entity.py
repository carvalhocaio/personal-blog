import re
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import date

MAX_TITLE_LENGTH = 200
MAX_CONTENT_LENGTH = 200_000

TITLE_REQUIRED = "title is required"
TITLE_TOO_LONG = f"title must be at most {MAX_TITLE_LENGTH} characters"
CONTENT_REQUIRED = "content is required"
CONTENT_TOO_LONG = f"content must be at most {MAX_CONTENT_LENGTH} characters"

_SLUG_SEPARATOR = re.compile(r"[^a-z0-9]+")


class ArticleValidationError(Exception):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def slugify(title: str) -> str:
    return _SLUG_SEPARATOR.sub("-", title.strip().lower()).strip("-")


@dataclass(frozen=True, slots=True)
class Article:
    slug: str
    title: str
    content: str
    published_at: date

    @classmethod
    def create(cls, title: str, content: str, published_at: date) -> "Article":
        return cls(
            slug=slugify(title),
            title=title,
            content=content,
            published_at=published_at,
        )

    def update(self, title: str, content: str, published_at: date) -> "Article":
        return replace(self, title=title, content=content, published_at=published_at)

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", self.title.strip())

        errors = [*self._title_errors(), *self._content_errors()]
        if errors:
            raise ArticleValidationError(errors)

    def _title_errors(self) -> list[str]:
        if not self.title:
            return [TITLE_REQUIRED]
        if len(self.title) > MAX_TITLE_LENGTH:
            return [TITLE_TOO_LONG]
        if not self.slug:
            return [TITLE_REQUIRED]
        return []

    def _content_errors(self) -> list[str]:
        content = self.content.strip()
        if not content:
            return [CONTENT_REQUIRED]
        if len(content) > MAX_CONTENT_LENGTH:
            return [CONTENT_TOO_LONG]
        return []
