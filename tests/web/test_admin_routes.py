from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from personal_blog.article.repository import ArticleNotFoundError
from personal_blog.auth.session import COOKIE_NAME, issue_session
from personal_blog.config import Settings
from tests.fakes import InMemoryArticleRepository
from tests.web.conftest import ADMIN_PASSWORD, ADMIN_USER, make_article

pytestmark = pytest.mark.anyio

PROTECTED_ROUTES = [
    ("GET", "/admin"),
    ("GET", "/admin/articles/new"),
    ("POST", "/admin/articles/new"),
    ("GET", "/admin/articles/why-clancy-matters/edit"),
    ("POST", "/admin/articles/why-clancy-matters/edit"),
    ("POST", "/admin/articles/why-clancy-matters/delete"),
]

ARTICLE_FORM = {
    "title": "Why Clancy Matters",
    "published_at": "2026-01-15",
    "content": "Every project needs a name.",
}


class TestAccessControl:
    @pytest.mark.parametrize(("method", "path"), PROTECTED_ROUTES)
    async def test_redirects_anonymous_visitors_to_login(
        self, client: AsyncClient, method: str, path: str
    ) -> None:
        response = await client.request(method, path)

        assert response.status_code == 303
        assert response.headers["location"] == "/admin/login"

    @pytest.mark.parametrize(("method", "path"), PROTECTED_ROUTES)
    async def test_rejects_a_forged_session(
        self, client: AsyncClient, method: str, path: str
    ) -> None:
        client.cookies.set(COOKIE_NAME, "9999999999.forged-signature")

        response = await client.request(method, path)

        assert response.status_code == 303
        assert response.headers["location"] == "/admin/login"

    async def test_rejects_an_expired_session(
        self, client: AsyncClient, settings: Settings
    ) -> None:
        expired = issue_session(settings.session_key_bytes, timedelta(seconds=-1))
        client.cookies.set(COOKIE_NAME, expired)

        response = await client.get("/admin")

        assert response.status_code == 303

    async def test_grants_access_with_a_valid_session(
        self, admin_client: AsyncClient
    ) -> None:
        assert (await admin_client.get("/admin")).status_code == 200


class TestLogin:
    async def test_serves_the_login_form(self, client: AsyncClient) -> None:
        response = await client.get("/admin/login")

        assert response.status_code == 200
        assert 'name="password"' in response.text

    async def test_rejects_wrong_credentials(self, client: AsyncClient) -> None:
        response = await client.post(
            "/admin/login", data={"username": ADMIN_USER, "password": "wrong"}
        )

        assert response.status_code == 401
        assert "Invalid username or password" in response.text
        assert COOKIE_NAME not in response.cookies

    async def test_issues_a_session_on_success(self, client: AsyncClient) -> None:
        response = await client.post(
            "/admin/login", data={"username": ADMIN_USER, "password": ADMIN_PASSWORD}
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/admin"
        assert COOKIE_NAME in response.cookies

    async def test_hardens_the_session_cookie(self, client: AsyncClient) -> None:
        response = await client.post(
            "/admin/login", data={"username": ADMIN_USER, "password": ADMIN_PASSWORD}
        )

        cookie = response.headers["set-cookie"].lower()
        assert "httponly" in cookie
        assert "samesite=lax" in cookie
        assert "path=/" in cookie

    async def test_logout_clears_the_session(self, admin_client: AsyncClient) -> None:
        response = await admin_client.post("/admin/logout")

        assert response.status_code == 303
        assert response.headers["location"] == "/"
        assert (await admin_client.get("/admin")).status_code == 303


class TestDashboard:
    async def test_shows_an_empty_state(self, admin_client: AsyncClient) -> None:
        response = await admin_client.get("/admin")

        assert "No articles yet" in response.text

    async def test_offers_admin_controls_for_each_article(
        self, admin_client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article())

        body = (await admin_client.get("/admin")).text

        assert "/admin/articles/why-clancy-matters/edit" in body
        assert "/admin/articles/why-clancy-matters/delete" in body
        assert "/admin/logout" in body


class TestCreateArticle:
    async def test_serves_the_new_article_form(self, admin_client: AsyncClient) -> None:
        response = await admin_client.get("/admin/articles/new")

        assert response.status_code == 200
        assert 'action="/admin/articles/new"' in response.text

    async def test_publishes_a_valid_article(
        self, admin_client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        response = await admin_client.post("/admin/articles/new", data=ARTICLE_FORM)

        assert response.status_code == 303
        assert response.headers["location"] == "/admin"

        stored = await repository.get("why-clancy-matters")
        assert stored.title == "Why Clancy Matters"
        assert stored.published_at == date(2026, 1, 15)

    async def test_reports_domain_violations(self, admin_client: AsyncClient) -> None:
        response = await admin_client.post(
            "/admin/articles/new", data={**ARTICLE_FORM, "title": "", "content": ""}
        )

        assert response.status_code == 422
        assert "title is required" in response.text
        assert "content is required" in response.text

    async def test_rejects_an_unparseable_date(self, admin_client: AsyncClient) -> None:
        response = await admin_client.post(
            "/admin/articles/new", data={**ARTICLE_FORM, "published_at": "yesterday"}
        )

        assert response.status_code == 422
        assert "published date must be a valid date" in response.text

    async def test_preserves_submitted_input_on_failure(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.post(
            "/admin/articles/new",
            data={**ARTICLE_FORM, "title": "Kept Title", "published_at": "yesterday"},
        )

        assert 'value="Kept Title"' in response.text
        assert "Every project needs a name." in response.text

    async def test_rejects_a_duplicate_title(
        self, admin_client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article(title="Why Clancy Matters"))

        response = await admin_client.post("/admin/articles/new", data=ARTICLE_FORM)

        assert response.status_code == 409
        assert "already exists" in response.text


class TestEditArticle:
    async def test_prefills_the_edit_form(
        self, admin_client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article())

        response = await admin_client.get("/admin/articles/why-clancy-matters/edit")

        assert response.status_code == 200
        assert 'value="Why Clancy Matters"' in response.text
        assert 'value="2026-01-15"' in response.text

    async def test_returns_404_for_an_unknown_article(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.get("/admin/articles/never-published/edit")

        assert response.status_code == 404

    async def test_saves_the_changes(
        self, admin_client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article())

        response = await admin_client.post(
            "/admin/articles/why-clancy-matters/edit",
            data={**ARTICLE_FORM, "title": "Why Clancy Still Matters"},
        )

        assert response.status_code == 303

        stored = await repository.get("why-clancy-matters")
        assert stored.title == "Why Clancy Still Matters"

    async def test_never_changes_the_published_url(
        self, admin_client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article())

        await admin_client.post(
            "/admin/articles/why-clancy-matters/edit",
            data={**ARTICLE_FORM, "title": "A Completely Different Title"},
        )

        assert [article.slug for article in await repository.list_all()] == [
            "why-clancy-matters"
        ]

    async def test_reports_domain_violations(
        self, admin_client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article())

        response = await admin_client.post(
            "/admin/articles/why-clancy-matters/edit",
            data={**ARTICLE_FORM, "content": ""},
        )

        assert response.status_code == 422
        assert "content is required" in response.text

    async def test_rejects_an_unparseable_date(
        self, admin_client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article())

        response = await admin_client.post(
            "/admin/articles/why-clancy-matters/edit",
            data={**ARTICLE_FORM, "published_at": "yesterday"},
        )

        assert response.status_code == 422
        assert "published date must be a valid date" in response.text

    async def test_returns_404_when_updating_an_unknown_article(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.post(
            "/admin/articles/never-published/edit", data=ARTICLE_FORM
        )

        assert response.status_code == 404


class TestDeleteArticle:
    async def test_removes_the_article(
        self, admin_client: AsyncClient, repository: InMemoryArticleRepository
    ) -> None:
        await repository.create(make_article())

        response = await admin_client.post("/admin/articles/why-clancy-matters/delete")

        assert response.status_code == 303
        assert response.headers["location"] == "/admin"

        with pytest.raises(ArticleNotFoundError):
            await repository.get("why-clancy-matters")

    async def test_tolerates_deleting_an_unknown_article(
        self, admin_client: AsyncClient
    ) -> None:
        response = await admin_client.post("/admin/articles/never-published/delete")

        assert response.status_code == 303
