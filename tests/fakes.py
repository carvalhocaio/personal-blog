from datetime import date

from personal_blog.article.entity import Article
from personal_blog.article.repository import ArticleNotFoundError, SlugAlreadyTakenError


class InMemoryArticleRepository:
    def __init__(self) -> None:
        self._articles: dict[str, Article] = {}

    async def create(self, article: Article) -> None:
        if article.slug in self._articles:
            raise SlugAlreadyTakenError(article.slug)
        self._articles[article.slug] = article

    async def get(self, slug: str) -> Article:
        try:
            return self._articles[slug]
        except KeyError:
            raise ArticleNotFoundError(slug) from None

    async def update(self, article: Article) -> None:
        if article.slug not in self._articles:
            raise ArticleNotFoundError(article.slug)
        self._articles[article.slug] = article

    async def delete(self, slug: str) -> None:
        if self._articles.pop(slug, None) is None:
            raise ArticleNotFoundError(slug)

    async def list_all(self) -> list[Article]:
        return sorted(self._articles.values(), key=_publication_order)


def _publication_order(article: Article) -> tuple[date, str]:
    return (article.published_at, article.slug)
