import uvicorn

from personal_blog.article.fs_store import FileSystemArticleRepository
from personal_blog.config import Settings
from personal_blog.web.app import create_app


def main() -> None:  # pragma: no cover
    settings = Settings()
    repository = FileSystemArticleRepository(settings.content_dir)

    uvicorn.run(
        create_app(settings=settings, repository=repository),
        host=settings.host,
        port=settings.port,
    )
