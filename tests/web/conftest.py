from collections.abc import AsyncIterator
from datetime import date

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from personal_blog.article.entity import Article
from personal_blog.config import MIN_SESSION_KEY_LENGTH, Settings
from personal_blog.web.app import create_app
from tests.fakes import InMemoryArticleRepository

ADMIN_USER = "clancy"
ADMIN_PASSWORD = "trench"
SESSION_KEY = "k" * MIN_SESSION_KEY_LENGTH
SITE_TITLE = "Trench Dispatch"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        title=SITE_TITLE,
        admin_user=ADMIN_USER,
        admin_password=ADMIN_PASSWORD,
        session_key=SESSION_KEY,
    )


@pytest.fixture
def repository() -> InMemoryArticleRepository:
    return InMemoryArticleRepository()


@pytest.fixture
def app(settings: Settings, repository: InMemoryArticleRepository) -> FastAPI:
    return create_app(settings=settings, repository=repository)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        follow_redirects=False,
    ) as client:
        yield client


def make_article(
    title: str = "Why Clancy Matters",
    content: str = "Every project needs a name.",
    published_at: date = date(2026, 1, 15),
) -> Article:
    return Article.create(title=title, content=content, published_at=published_at)
