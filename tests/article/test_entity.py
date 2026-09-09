from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from personal_blog.article.entity import (
    CONTENT_REQUIRED,
    CONTENT_TOO_LONG,
    MAX_CONTENT_LENGTH,
    MAX_TITLE_LENGTH,
    TITLE_REQUIRED,
    TITLE_TOO_LONG,
    Article,
    ArticleValidationError,
    slugify,
)

PUBLISHED_AT = date(2026, 1, 15)


def build_article(
    title: str = "Why Clancy Matters",
    content: str = "Every project needs a name.",
    published_at: date = PUBLISHED_AT,
) -> Article:
    return Article.create(title=title, content=content, published_at=published_at)


class TestSlugify:
    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            ("Why Clancy Matters", "why-clancy-matters"),
            (
                "F1 2026: What Changed in the Cost Cap?",
                "f1-2026-what-changed-in-the-cost-cap",
            ),
            ("  Trench  ", "trench"),
            ("Vessel   Album", "vessel-album"),
            ("Sai-Kō / Saturday", "sai-k-saturday"),
            ("---Blurryface---", "blurryface"),
            ("???", ""),
        ],
    )
    def test_derives_url_safe_slug(self, title: str, expected: str) -> None:
        assert slugify(title) == expected


class TestCreate:
    def test_derives_slug_from_title(self) -> None:
        assert build_article(title="Why Clancy Matters").slug == "why-clancy-matters"

    def test_trims_surrounding_whitespace_from_title(self) -> None:
        assert build_article(title="  Trench  ").title == "Trench"

    def test_preserves_content_verbatim(self) -> None:
        content = "  ## Heading\n\n  indented line\n"

        assert build_article(content=content).content == content

    def test_rejects_title_that_slugifies_to_nothing(self) -> None:
        with pytest.raises(ArticleValidationError) as exc_info:
            build_article(title="???")

        assert TITLE_REQUIRED in exc_info.value.errors


class TestValidation:
    @pytest.mark.parametrize("title", ["", "   ", "\n\t"])
    def test_rejects_blank_title(self, title: str) -> None:
        with pytest.raises(ArticleValidationError) as exc_info:
            build_article(title=title)

        assert exc_info.value.errors == (TITLE_REQUIRED,)

    def test_accepts_title_at_the_length_limit(self) -> None:
        assert (
            len(build_article(title="a" * MAX_TITLE_LENGTH).title) == MAX_TITLE_LENGTH
        )

    def test_rejects_title_over_the_length_limit(self) -> None:
        with pytest.raises(ArticleValidationError) as exc_info:
            build_article(title="a" * (MAX_TITLE_LENGTH + 1))

        assert exc_info.value.errors == (TITLE_TOO_LONG,)

    @pytest.mark.parametrize("content", ["", "   ", "\n\t"])
    def test_rejects_blank_content(self, content: str) -> None:
        with pytest.raises(ArticleValidationError) as exc_info:
            build_article(content=content)

        assert exc_info.value.errors == (CONTENT_REQUIRED,)

    def test_rejects_content_over_the_length_limit(self) -> None:
        with pytest.raises(ArticleValidationError) as exc_info:
            build_article(content="a" * (MAX_CONTENT_LENGTH + 1))

        assert exc_info.value.errors == (CONTENT_TOO_LONG,)

    def test_reports_every_violation_at_once(self) -> None:
        with pytest.raises(ArticleValidationError) as exc_info:
            build_article(title="", content="")

        assert exc_info.value.errors == (TITLE_REQUIRED, CONTENT_REQUIRED)

    def test_direct_construction_enforces_the_same_invariants(self) -> None:
        with pytest.raises(ArticleValidationError):
            Article(slug="trench", title="", content="body", published_at=PUBLISHED_AT)


class TestUpdate:
    def test_keeps_the_slug_when_the_title_changes(self) -> None:
        original = build_article(title="Why Clancy Matters")

        updated = original.update(
            title="Why Clancy Still Matters",
            content=original.content,
            published_at=original.published_at,
        )

        assert updated.slug == "why-clancy-matters"
        assert updated.title == "Why Clancy Still Matters"

    def test_leaves_the_original_untouched(self) -> None:
        original = build_article(title="Trench")

        original.update(
            title="Vessel", content="new body", published_at=date(2026, 2, 1)
        )

        assert original.title == "Trench"

    def test_validates_the_result(self) -> None:
        original = build_article()

        with pytest.raises(ArticleValidationError) as exc_info:
            original.update(
                title="", content=original.content, published_at=PUBLISHED_AT
            )

        assert exc_info.value.errors == (TITLE_REQUIRED,)

    def test_instances_are_frozen(self) -> None:  # noqa: E501
        with pytest.raises(FrozenInstanceError):
            build_article().title = "Blurryface"  # type: ignore[misc]
