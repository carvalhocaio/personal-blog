from datetime import date
from pathlib import Path

import pytest

from personal_blog.article.entity import Article
from personal_blog.article.fs_store import FileSystemArticleRepository
from personal_blog.article.repository import (
    ArticleNotFoundError,
    ArticleRepository,
    SlugAlreadyTakenError,
)
from tests.fakes import InMemoryArticleRepository

pytestmark = pytest.mark.anyio

MALFORMED_SLUGS = [
    "",
    "..",
    "../secrets",
    "Not A Slug",
    "trench.json",
    "-trench",
    "trench-",
]


def make_article(
    title: str = "Why Clancy Matters",
    content: str = "Every project needs a name.",
    published_at: date = date(2026, 1, 15),
) -> Article:
    return Article.create(title=title, content=content, published_at=published_at)


class ArticleRepositoryContract:
    async def test_get_returns_what_create_stored(
        self, repository: ArticleRepository
    ) -> None:
        article = make_article()

        await repository.create(article)

        assert await repository.get(article.slug) == article

    async def test_roundtrips_content_verbatim(
        self, repository: ArticleRepository
    ) -> None:
        content = "## Heading\n\n`código` com acento — e uma linha vazia\n\n> quote"
        article = make_article(content=content)

        await repository.create(article)

        assert (await repository.get(article.slug)).content == content

    async def test_get_raises_for_unknown_slug(
        self, repository: ArticleRepository
    ) -> None:
        with pytest.raises(ArticleNotFoundError):
            await repository.get("never-published")

    async def test_create_rejects_a_taken_slug(
        self, repository: ArticleRepository
    ) -> None:
        await repository.create(make_article(title="Trench"))

        with pytest.raises(SlugAlreadyTakenError):
            await repository.create(
                make_article(title="Trench", content="different body")
            )

    async def test_update_persists_the_new_values(
        self, repository: ArticleRepository
    ) -> None:
        article = make_article(title="Trench")
        await repository.create(article)

        revised = article.update(
            title="Trench Revisited",
            content="new body",
            published_at=date(2026, 3, 1),
        )
        await repository.update(revised)

        assert await repository.get(article.slug) == revised

    async def test_update_never_creates_a_missing_article(
        self, repository: ArticleRepository
    ) -> None:
        with pytest.raises(ArticleNotFoundError):
            await repository.update(make_article(title="Ghost Post"))

        with pytest.raises(ArticleNotFoundError):
            await repository.get("ghost-post")

    async def test_delete_removes_the_article(
        self, repository: ArticleRepository
    ) -> None:
        article = make_article()
        await repository.create(article)

        await repository.delete(article.slug)

        with pytest.raises(ArticleNotFoundError):
            await repository.get(article.slug)

    async def test_delete_raises_for_unknown_slug(
        self, repository: ArticleRepository
    ) -> None:
        with pytest.raises(ArticleNotFoundError):
            await repository.delete("never-published")

    async def test_list_all_is_empty_without_articles(
        self, repository: ArticleRepository
    ) -> None:
        assert await repository.list_all() == []

    async def test_list_all_orders_by_publication_date_descending(
        self, repository: ArticleRepository
    ) -> None:
        await repository.create(
            make_article(title="Older", published_at=date(2026, 1, 1))
        )
        await repository.create(
            make_article(title="Newest", published_at=date(2026, 6, 1))
        )
        await repository.create(
            make_article(title="Middle", published_at=date(2026, 3, 1))
        )

        listed = await repository.list_all()

        assert [article.slug for article in listed] == ["newest", "middle", "older"]

    async def test_list_all_breaks_date_ties_by_slug_ascending(
        self, repository: ArticleRepository
    ) -> None:
        same_day = date(2026, 2, 14)
        await repository.create(make_article(title="Vessel", published_at=same_day))
        await repository.create(make_article(title="Blurryface", published_at=same_day))
        await repository.create(make_article(title="Trench", published_at=same_day))

        listed = await repository.list_all()

        assert [article.slug for article in listed] == [
            "blurryface",
            "trench",
            "vessel",
        ]

    @pytest.mark.parametrize("slug", MALFORMED_SLUGS)
    async def test_malformed_slugs_read_as_missing(
        self, repository: ArticleRepository, slug: str
    ) -> None:
        with pytest.raises(ArticleNotFoundError):
            await repository.get(slug)

    @pytest.mark.parametrize("slug", MALFORMED_SLUGS)
    async def test_malformed_slugs_delete_as_missing(
        self, repository: ArticleRepository, slug: str
    ) -> None:
        with pytest.raises(ArticleNotFoundError):
            await repository.delete(slug)


class TestInMemoryArticleRepository(ArticleRepositoryContract):
    @pytest.fixture
    def repository(self) -> InMemoryArticleRepository:
        return InMemoryArticleRepository()


class TestFileSystemArticleRepository(ArticleRepositoryContract):
    @pytest.fixture
    def repository(self, tmp_path: Path) -> FileSystemArticleRepository:
        return FileSystemArticleRepository(tmp_path)
