from typing import Annotated

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates

from personal_blog.article.repository import ArticleRepository
from personal_blog.config import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_repository(request: Request) -> ArticleRepository:
    return request.app.state.repository


def get_templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates


SettingsDep = Annotated[Settings, Depends(get_settings)]
RepositoryDep = Annotated[ArticleRepository, Depends(get_repository)]
TemplatesDep = Annotated[Jinja2Templates, Depends(get_templates)]
