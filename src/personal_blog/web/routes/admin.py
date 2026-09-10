import contextlib

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse

from personal_blog.article.entity import Article, ArticleValidationError
from personal_blog.article.repository import ArticleNotFoundError, SlugAlreadyTakenError
from personal_blog.auth.session import (
    COOKIE_NAME,
    issue_session,
    verify_credentials,
)
from personal_blog.config import Settings
from personal_blog.web.dependencies import (
    RepositoryDep,
    SettingsDep,
    TemplatesDep,
    require_admin,
)
from personal_blog.web.forms import (
    DUPLICATE_TITLE,
    INVALID_DATE,
    ArticleForm,
    parse_published_at,
)
from personal_blog.web.templates import render_page

DASHBOARD_PATH = "/admin"
INVALID_CREDENTIALS = "Invalid username or password"

auth_router = APIRouter(prefix="/admin")
router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])


@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request, settings: SettingsDep, templates: TemplatesDep
) -> HTMLResponse:
    return render_page(templates, request, "login", settings.title)


@auth_router.post("/login")
async def submit_login(
    request: Request,
    settings: SettingsDep,
    templates: TemplatesDep,
    username: str = Form(""),
    password: str = Form(""),
) -> Response:
    if not verify_credentials(
        settings.admin_user, settings.admin_password, username, password
    ):
        return render_page(
            templates,
            request,
            "login",
            settings.title,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error=INVALID_CREDENTIALS,
        )

    response = RedirectResponse(DASHBOARD_PATH, status_code=status.HTTP_303_SEE_OTHER)
    _issue_session_cookie(response, request, settings)

    return response


@auth_router.post("/logout")
async def logout(request: Request) -> Response:
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        httponly=True,
        secure=_is_secure(request),
        samesite="lax",
    )

    return response


@router.get("", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    repository: RepositoryDep,
    settings: SettingsDep,
    templates: TemplatesDep,
) -> HTMLResponse:
    articles = await repository.list_all()

    return render_page(
        templates,
        request,
        "dashboard",
        settings.title,
        is_admin=True,
        articles=articles,
    )


@router.get("/articles/new", response_class=HTMLResponse)
async def new_article_form(
    request: Request, settings: SettingsDep, templates: TemplatesDep
) -> HTMLResponse:
    return _render_form(templates, request, settings, ArticleForm.for_new_article())


@router.post("/articles/new")
async def create_article(
    request: Request,
    repository: RepositoryDep,
    settings: SettingsDep,
    templates: TemplatesDep,
    title: str = Form(""),
    published_at: str = Form(""),
    content: str = Form(""),
) -> Response:
    form = ArticleForm.for_new_article(
        title=title, published_at=published_at, content=content
    )

    parsed_date = parse_published_at(published_at)
    if parsed_date is None:
        return _render_invalid_form(
            templates, request, settings, form.with_errors(INVALID_DATE)
        )

    try:
        article = Article.create(title=title, content=content, published_at=parsed_date)
    except ArticleValidationError as error:
        return _render_invalid_form(
            templates, request, settings, form.with_errors(*error.errors)
        )

    try:
        await repository.create(article)
    except SlugAlreadyTakenError:
        return _render_form(
            templates,
            request,
            settings,
            form.with_errors(DUPLICATE_TITLE),
            status_code=status.HTTP_409_CONFLICT,
        )

    return RedirectResponse(DASHBOARD_PATH, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/articles/{slug}/edit", response_class=HTMLResponse)
async def edit_article_form(
    slug: str,
    request: Request,
    repository: RepositoryDep,
    settings: SettingsDep,
    templates: TemplatesDep,
) -> HTMLResponse:
    article = await _find_article(repository, slug)

    return _render_form(templates, request, settings, ArticleForm.from_article(article))


@router.post("/articles/{slug}/edit")
async def update_article(
    slug: str,
    request: Request,
    repository: RepositoryDep,
    settings: SettingsDep,
    templates: TemplatesDep,
    title: str = Form(""),
    published_at: str = Form(""),
    content: str = Form(""),
) -> Response:
    existing = await _find_article(repository, slug)
    form = ArticleForm.for_existing_article(
        slug=slug, title=title, published_at=published_at, content=content
    )

    parsed_date = parse_published_at(published_at)
    if parsed_date is None:
        return _render_invalid_form(
            templates, request, settings, form.with_errors(INVALID_DATE)
        )

    try:
        revised = existing.update(
            title=title, content=content, published_at=parsed_date
        )
    except ArticleValidationError as error:
        return _render_invalid_form(
            templates, request, settings, form.with_errors(*error.errors)
        )

    await repository.update(revised)

    return RedirectResponse(DASHBOARD_PATH, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/articles/{slug}/delete")
async def delete_article(slug: str, repository: RepositoryDep) -> Response:
    with contextlib.suppress(ArticleNotFoundError):
        await repository.delete(slug)

    return RedirectResponse(DASHBOARD_PATH, status_code=status.HTTP_303_SEE_OTHER)


async def _find_article(repository: RepositoryDep, slug: str) -> Article:
    try:
        return await repository.get(slug)
    except ArticleNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND) from None


def _render_form(
    templates: TemplatesDep,
    request: Request,
    settings: Settings,
    form: ArticleForm,
    status_code: int = status.HTTP_200_OK,
) -> HTMLResponse:
    return render_page(
        templates,
        request,
        "article_form",
        settings.title,
        status_code=status_code,
        is_admin=True,
        form=form,
    )


def _render_invalid_form(
    templates: TemplatesDep, request: Request, settings: Settings, form: ArticleForm
) -> HTMLResponse:
    return _render_form(
        templates, request, settings, form, status.HTTP_422_UNPROCESSABLE_ENTITY
    )


def _issue_session_cookie(
    response: Response, request: Request, settings: Settings
) -> None:
    response.set_cookie(
        COOKIE_NAME,
        issue_session(settings.session_key_bytes, settings.session_ttl),
        max_age=int(settings.session_ttl.total_seconds()),
        path="/",
        httponly=True,
        secure=_is_secure(request),
        samesite="lax",
    )


def _is_secure(request: Request) -> bool:
    return request.url.scheme == "https"
