from collections.abc import Iterable
from typing import Protocol

from personal_blog.article.entity import Article


class ArticleRepositoryError(Exception):
    pass


class ArticleNotFoundError(ArticleRepositoryError):
    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"article {slug!r} not found")


class SlugAlreadyTakenError(ArticleRepositoryError):
    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"an article with slug {slug!r} already exists")


class ArticleStorageError(ArticleRepositoryError):
    pass


class ArticleRepository(Protocol):
    async def create(self, article: Article) -> None: ...

    async def get(self, slug: str) -> Article: ...

    async def update(self, article: Article) -> None: ...

    async def delete(self, slug: str) -> None: ...

    async def list_all(self) -> list[Article]: ...


def sort_by_publication(articles: Iterable[Article]) -> list[Article]:
    by_slug = sorted(articles, key=lambda article: article.slug)
    return sorted(by_slug, key=lambda article: article.published_at, reverse=True)
