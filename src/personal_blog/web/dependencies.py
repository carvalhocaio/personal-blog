from typing import Annotated, cast

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates

from personal_blog.article.repository import ArticleRepository
from personal_blog.auth.session import COOKIE_NAME, InvalidSessionError, verify_session
from personal_blog.config import Settings


def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def get_repository(request: Request) -> ArticleRepository:
    return cast(ArticleRepository, request.app.state.repository)


def get_templates(request: Request) -> Jinja2Templates:
    return cast(Jinja2Templates, request.app.state.templates)


SettingsDep = Annotated[Settings, Depends(get_settings)]
RepositoryDep = Annotated[ArticleRepository, Depends(get_repository)]
TemplatesDep = Annotated[Jinja2Templates, Depends(get_templates)]


class AuthenticationRequiredError(Exception):
    pass


def require_admin(request: Request, settings: SettingsDep) -> None:
    try:
        verify_session(settings.session_key_bytes, request.cookies.get(COOKIE_NAME, ""))
    except InvalidSessionError:
        raise AuthenticationRequiredError from None
