import pytest
from httpx import AsyncClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from tests.web.conftest import SITE_TITLE

pytestmark = pytest.mark.anyio


class TestNotFoundPage:
    async def test_serves_html_instead_of_json(self, client: AsyncClient) -> None:
        response = await client.get("/articles/never-published")

        assert response.status_code == 404
        assert response.headers["content-type"].startswith("text/html")
        assert "detail" not in response.text

    async def test_keeps_the_site_chrome(self, client: AsyncClient) -> None:
        response = await client.get("/articles/never-published")

        assert SITE_TITLE in response.text
        assert 'href="/"' in response.text

    async def test_explains_what_happened(self, client: AsyncClient) -> None:
        response = await client.get("/articles/never-published")

        assert "not found" in response.text.lower()

    async def test_covers_unmatched_paths(self, client: AsyncClient) -> None:
        response = await client.get("/no/such/page")

        assert response.status_code == 404
        assert response.headers["content-type"].startswith("text/html")

    async def test_does_not_leak_admin_chrome(self, client: AsyncClient) -> None:
        response = await client.get("/admin/articles/never-published/edit")

        assert "/admin/logout" not in response.text


class TestOtherHttpErrors:
    async def test_does_not_render_the_not_found_page(
        self, client: AsyncClient
    ) -> None:
        with pytest.raises(StarletteHTTPException) as excinfo:
            await client.get("/admin/logout")

        assert excinfo.value.status_code == 405
