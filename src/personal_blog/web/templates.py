from datetime import date
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"
STATIC_DIR = ASSETS_DIR / "static"


def format_date(value: date) -> str:
    return f"{value:%B} {value.day}, {value.year}"


def create_templates() -> Jinja2Templates:
    templates = Jinja2Templates(directory=TEMPLATES_DIR)
    templates.env.filters["format_date"] = format_date

    return templates


def render_page(
    templates: Jinja2Templates,
    request: Request,
    name: str,
    site_title: str,
    *,
    status_code: int = 200,
    is_admin: bool = False,
    **context: Any,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name=f"{name}.html",
        context={"site_title": site_title, "is_admin": is_admin, **context},
        status_code=status_code,
    )
