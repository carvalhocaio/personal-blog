from datetime import date

import pytest
from httpx import AsyncClient

from tests.fakes import InMemoryArticleRepository
from tests.web.conftest import SITE_TITLE, make_article

pytestmark = pytest.mark.anyio


class TestHomePage:
    async def test_serves_html(self, client: AsyncClient) -> None:
        response = await client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    async def test_shows_the_site_title(self, client: AsyncClient) -> None:
        response = await client.get("/")

        assert SITE_TITLE in response.text

    async def test_shows_an_empty_state_without_articles(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/")

        assert "No articles published yet" in response.text

    async def test_links_each_article_by_slug(
        self, client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article(title="Why Clancy Matters"))

        response = await client.get("/")

        assert 'href="/articles/why-clancy-matters"' in response.text
        assert "Why Clancy Matters" in response.text

    async def test_lists_newest_articles_first(
        self, client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(
            make_article(title="Older", published_at=date(2026, 1, 1))
        )
        await repository.create(
            make_article(title="Newest", published_at=date(2026, 6, 1))
        )

        body = (await client.get("/")).text

        assert body.index("/articles/newest") < body.index("/articles/older")

    async def test_formats_the_publication_date(
        self, client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article(published_at=date(2026, 1, 15)))

        response = await client.get("/")

        assert "January 15, 2026" in response.text

    async def test_does_not_offer_admin_controls(
        self, client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article())

        body = (await client.get("/")).text

        assert "/admin/logout" not in body
        assert "/admin/articles" not in body

    async def test_escapes_article_titles(
        self, client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(
            make_article(title="Cost Cap <script>alert(1)</script>")
        )

        body = (await client.get("/")).text

        assert "<script>alert(1)</script>" not in body
        assert "&lt;script&gt;" in body


class TestArticlePage:
    async def test_renders_a_published_article(
        self, client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article(title="Why Clancy Matters"))

        response = await client.get("/articles/why-clancy-matters")

        assert response.status_code == 200
        assert "Why Clancy Matters" in response.text

    async def test_renders_the_markdown_content_as_html(
        self, client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article(content="a **cost cap** rule"))

        response = await client.get("/articles/why-clancy-matters")

        assert "<strong>cost cap</strong>" in response.text

    async def test_does_not_escape_the_rendered_markup(
        self, client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article(content="## Heading"))

        response = await client.get("/articles/why-clancy-matters")

        assert "<h2>Heading</h2>" in response.text
        assert "&lt;h2&gt;" not in response.text

    async def test_still_escapes_html_written_by_the_author(
        self, client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article(content="<script>alert(1)</script>"))

        response = await client.get("/articles/why-clancy-matters")

        assert "<script>alert(1)</script>" not in response.text

    async def test_returns_404_for_an_unknown_slug(self, client: AsyncClient) -> None:
        response = await client.get("/articles/never-published")

        assert response.status_code == 404

    @pytest.mark.parametrize("slug", ["Not-A-Slug", "trench.json", "-trench"])
    async def test_returns_404_for_a_malformed_slug(
        self, client: AsyncClient, slug: str
    ) -> None:
        response = await client.get(f"/articles/{slug}")

        assert response.status_code == 404


class TestStaticFiles:
    async def test_serves_the_stylesheet(self, client: AsyncClient) -> None:
        response = await client.get("/static/css/style.css")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/css")
