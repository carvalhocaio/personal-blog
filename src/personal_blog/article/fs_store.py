import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import anyio
from anyio import to_thread

from personal_blog.article.entity import Article, ArticleValidationError
from personal_blog.article.repository import (
    ArticleNotFoundError,
    ArticleStorageError,
    SlugAlreadyTakenError,
    sort_by_publication,
)

FILE_SUFFIX = ".json"

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class FileSystemArticleRepository:
    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)
        self._lock = anyio.Lock()

    async def create(self, article: Article) -> None:
        async with self._lock:
            await to_thread.run_sync(self._create, article)

    async def get(self, slug: str) -> Article:
        async with self._lock:
            return await to_thread.run_sync(self._get, slug)

    async def update(self, article: Article) -> None:
        async with self._lock:
            await to_thread.run_sync(self._update, article)

    async def delete(self, slug: str) -> None:
        async with self._lock:
            await to_thread.run_sync(self._delete, slug)

    async def list_all(self) -> list[Article]:
        async with self._lock:
            return await to_thread.run_sync(self._list_all)

    def _create(self, article: Article) -> None:
        path = self._path(article.slug)
        if path.exists():
            raise SlugAlreadyTakenError(article.slug)
        _write_atomically(path, article)

    def _get(self, slug: str) -> Article:
        return _read(self._path(slug))

    def _update(self, article: Article) -> None:
        path = self._path(article.slug)
        if not path.exists():
            raise ArticleNotFoundError(article.slug)
        _write_atomically(path, article)

    def _delete(self, slug: str) -> None:
        path = self._path(slug)
        try:
            path.unlink()
        except FileNotFoundError:
            raise ArticleNotFoundError(slug) from None
        except OSError as error:
            raise ArticleStorageError(f"could not delete article {slug!r}") from error

    def _list_all(self) -> list[Article]:
        try:
            entries = [
                entry
                for entry in self._directory.iterdir()
                if entry.is_file() and entry.suffix == FILE_SUFFIX
            ]
        except OSError as error:
            raise ArticleStorageError("could not read the content directory") from error

        return sort_by_publication(_read(entry) for entry in entries)

    def _path(self, slug: str) -> Path:
        if not _SLUG_PATTERN.match(slug):
            raise ArticleNotFoundError(slug)
        return self._directory / f"{slug}{FILE_SUFFIX}"


def _write_atomically(path: Path, article: Article) -> None:
    temporary = path.parent / f"{path.name}.tmp"
    payload = json.dumps(_to_document(article), indent=2, ensure_ascii=False)

    try:
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(path)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise ArticleStorageError(
            f"could not commit article {article.slug!r}"
        ) from error


def _read(path: Path) -> Article:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ArticleNotFoundError(path.stem) from None
    except OSError as error:
        raise ArticleStorageError(f"could not read {path.name}") from error

    try:
        return _from_document(json.loads(raw))
    except (ValueError, TypeError, KeyError, ArticleValidationError) as error:
        raise ArticleStorageError(f"could not decode {path.name}") from error


def _to_document(article: Article) -> dict[str, str]:
    return {
        "slug": article.slug,
        "title": article.title,
        "content": article.content,
        "published_at": article.published_at.isoformat(),
    }


def _from_document(document: dict[str, Any]) -> Article:
    return Article(
        slug=document["slug"],
        title=document["title"],
        content=document["content"],
        published_at=_parse_published_at(document["published_at"]),
    )


def _parse_published_at(raw: str) -> date:
    return datetime.fromisoformat(raw).date()
