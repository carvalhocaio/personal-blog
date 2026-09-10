# Personal Blog

A small personal blog built with FastAPI. Articles are stored as `.json` files
on the filesystem (one per slug) — no database required.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
cp .env.example .env
```

Edit `.env` and fill in the required secrets:

- `BLOG_ADMIN_USER` / `BLOG_ADMIN_PASSWORD` — admin login credentials.
- `BLOG_SESSION_KEY` — generate one with `openssl rand -hex 32`.

Optionally, populate `content/` with sample articles:

```bash
make seed
```

Then start the app:

```bash
make run
```

## Commands

| Command          | Description                                      |
| ---------------- | ------------------------------------------------- |
| `make run`       | Start the app (`python -m personal_blog`)          |
| `make test`      | Run the test suite                                 |
| `make coverage`  | Run tests with coverage (100% required)            |
| `make typecheck` | Run mypy against `src/`                            |
| `make lint`      | Run ruff (check + format --check)                  |
| `make format`    | Auto-format and auto-fix with ruff                 |
| `make seed`      | Copy sample articles from `seed/` into `content/`  |
| `make clean`     | Remove `content/`, caches, and `__pycache__` dirs  |

## License

MIT — see [LICENSE](LICENSE).
