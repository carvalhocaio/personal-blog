import uvicorn

from personal_blog.article.fs_store import FileSystemArticleRepository
from personal_blog.config import Settings
from personal_blog.web.app import create_app


def main() -> None:  # pragma: no cover
    # admin_user/admin_password/session_key have no defaults because they're
    # meant to come from the environment, not the constructor — mypy can't
    # know that, hence the ignore.
    settings = Settings()  # type: ignore[call-arg]
    repository = FileSystemArticleRepository(settings.content_dir)

    uvicorn.run(
        create_app(settings=settings, repository=repository),
        host=settings.host,
        port=settings.port,
    )
