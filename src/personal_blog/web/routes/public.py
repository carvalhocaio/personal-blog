from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from personal_blog.article.repository import ArticleNotFoundError
from personal_blog.render.markdown import render
from personal_blog.web.dependencies import RepositoryDep, SettingsDep, TemplatesDep
from personal_blog.web.templates import render_page

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    repository: RepositoryDep,
    settings: SettingsDep,
    templates: TemplatesDep,
) -> HTMLResponse:
    articles = await repository.list_all()

    return render_page(templates, request, "home", settings.title, articles=articles)


@router.get("/articles/{slug}", response_class=HTMLResponse)
async def read_article(
    slug: str,
    request: Request,
    repository: RepositoryDep,
    settings: SettingsDep,
    templates: TemplatesDep,
) -> HTMLResponse:
    try:
        article = await repository.get(slug)
    except ArticleNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND) from None

    return render_page(
        templates,
        request,
        "article",
        settings.title,
        article=article,
        content_html=render(article.content),
    )
