from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from personal_blog.article.repository import ArticleRepository
from personal_blog.config import Settings
from personal_blog.web.routes import public
from personal_blog.web.templates import STATIC_DIR, create_templates


def create_app(settings: Settings, repository: ArticleRepository) -> FastAPI:
    app = FastAPI(title=settings.title, docs_url=None, redoc_url=None, openapi_url=None)

    app.state.settings = settings
    app.state.repository = repository
    app.state.templates = create_templates()

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(public.router)

    return app
