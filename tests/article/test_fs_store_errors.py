from datetime import date
from pathlib import Path

import pytest

from personal_blog.article.entity import Article
from personal_blog.article.fs_store import FileSystemArticleRepository
from personal_blog.article.repository import ArticleStorageError

pytestmark = pytest.mark.anyio


def make_article() -> Article:
    return Article.create(
        title="Why Clancy Matters",
        content="Every project needs a name.",
        published_at=date(2026, 1, 15),
    )


class TestStorageFailures:
    async def test_create_wraps_write_failures(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = FileSystemArticleRepository(tmp_path)

        def failing_write_text(self: Path, *args: object, **kwargs: object) -> int:
            raise OSError("disk full")

        monkeypatch.setattr(Path, "write_text", failing_write_text)

        with pytest.raises(ArticleStorageError):
            await repository.create(make_article())

    async def test_delete_wraps_unexpected_os_errors(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = FileSystemArticleRepository(tmp_path)
        await repository.create(make_article())

        def failing_unlink(self: Path, *args: object, **kwargs: object) -> None:
            raise OSError("permission denied")

        monkeypatch.setattr(Path, "unlink", failing_unlink)

        with pytest.raises(ArticleStorageError):
            await repository.delete("why-clancy-matters")

    async def test_list_all_wraps_directory_read_failures(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = FileSystemArticleRepository(tmp_path)

        def failing_iterdir(self: Path) -> None:
            raise OSError("not accessible")

        monkeypatch.setattr(Path, "iterdir", failing_iterdir)

        with pytest.raises(ArticleStorageError):
            await repository.list_all()

    async def test_get_wraps_unexpected_read_failures(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = FileSystemArticleRepository(tmp_path)
        await repository.create(make_article())

        def failing_read_text(self: Path, *args: object, **kwargs: object) -> str:
            raise OSError("permission denied")

        monkeypatch.setattr(Path, "read_text", failing_read_text)

        with pytest.raises(ArticleStorageError):
            await repository.get("why-clancy-matters")

    async def test_get_wraps_malformed_json(self, tmp_path: Path) -> None:
        repository = FileSystemArticleRepository(tmp_path)
        (tmp_path / "why-clancy-matters.json").write_text("not json", encoding="utf-8")

        with pytest.raises(ArticleStorageError):
            await repository.get("why-clancy-matters")
