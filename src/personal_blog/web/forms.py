from dataclasses import dataclass, field, replace
from datetime import date

from personal_blog.article.entity import Article

INVALID_DATE = "published date must be a valid date"
DUPLICATE_TITLE = "an article with this title already exists"

NEW_ARTICLE_ACTION = "/admin/articles/new"


@dataclass(frozen=True, slots=True)
class ArticleForm:
    heading: str
    action: str
    submit_label: str
    title: str = ""
    published_at: str = ""
    content: str = ""
    errors: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def for_new_article(
        cls, title: str = "", published_at: str = "", content: str = ""
    ) -> "ArticleForm":
        return cls(
            heading="New Article",
            action=NEW_ARTICLE_ACTION,
            submit_label="Publish",
            title=title,
            published_at=published_at,
            content=content,
        )

    @classmethod
    def for_existing_article(
        cls, slug: str, title: str = "", published_at: str = "", content: str = ""
    ) -> "ArticleForm":
        return cls(
            heading="Edit Article",
            action=f"/admin/articles/{slug}/edit",
            submit_label="Update",
            title=title,
            published_at=published_at,
            content=content,
        )

    @classmethod
    def from_article(cls, article: Article) -> "ArticleForm":
        return cls.for_existing_article(
            slug=article.slug,
            title=article.title,
            published_at=article.published_at.isoformat(),
            content=article.content,
        )

    def with_errors(self, *errors: str) -> "ArticleForm":
        return replace(self, errors=tuple(errors))


def parse_published_at(raw: str) -> date | None:
    try:
        return date.fromisoformat(raw.strip())
    except ValueError:
        return None
