from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from personal_blog.article.repository import ArticleRepository
from personal_blog.auth.session import LOGIN_PATH
from personal_blog.config import Settings
from personal_blog.web.dependencies import AuthenticationRequiredError
from personal_blog.web.routes import admin, public
from personal_blog.web.templates import STATIC_DIR, create_templates, render_page


def create_app(settings: Settings, repository: ArticleRepository) -> FastAPI:
    app = FastAPI(title=settings.title, docs_url=None, redoc_url=None, openapi_url=None)

    app.state.settings = settings
    app.state.repository = repository
    app.state.templates = create_templates()

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(public.router)
    app.include_router(admin.auth_router)
    app.include_router(admin.router)

    @app.exception_handler(AuthenticationRequiredError)
    async def redirect_to_login(request: Request, exception: Exception) -> Response:
        return RedirectResponse(LOGIN_PATH, status_code=303)

    @app.exception_handler(StarletteHTTPException)
    async def render_http_error(request: Request, exception: Exception) -> Response:
        assert isinstance(exception, StarletteHTTPException)

        if exception.status_code != status.HTTP_404_NOT_FOUND:
            raise exception

        return render_page(
            app.state.templates,
            request,
            "not_found",
            settings.title,
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return app
