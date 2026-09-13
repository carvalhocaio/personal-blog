# Personal Blog

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Checked with mypy](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Coverage 100%](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](#)

A small personal blog built with **FastAPI**. Articles are stored as `.json`
files on the filesystem — one per slug, no database required.

---

## Features

- **Filesystem-backed articles**: no database, no ORM — each article is a
  single `.json` file, written atomically.
- **Custom markdown renderer**: a minimal, dependency-free markdown-to-HTML
  renderer that escapes content by default and validates link URLs against
  an allowlist of safe schemes.
- **Stateless admin sessions**: HMAC-signed session cookies, no session
  store, constant-time credential comparison.
- **Admin dashboard**: create, edit, and delete articles behind a login wall.
- **100% test coverage**, enforced in CI.

---

## Project structure

```
src/personal_blog/
├── article/
│   ├── entity.py        # Article domain model + validation
│   ├── repository.py    # Repository protocol + domain errors
│   └── fs_store.py       # Filesystem-backed repository implementation
├── auth/
│   └── session.py       # HMAC-signed session tokens, credential check
├── render/
│   └── markdown.py      # Minimal markdown -> safe HTML renderer
└── web/
    ├── app.py            # FastAPI app factory, error handlers
    ├── dependencies.py    # FastAPI dependencies (settings, repo, auth)
    ├── forms.py            # Admin form parsing/validation
    ├── templates.py         # Jinja2 environment setup
    └── routes/
        ├── public.py        # Home page, article page
        └── admin.py          # Login, dashboard, article CRUD
```

---

## Configuration

Settings are loaded from environment variables (prefixed `BLOG_`) or a `.env`
file — see [`.env.example`](.env.example).

| Variable            | Default          | Description                                                        |
| -------------------- | ---------------- | -------------------------------------------------------------------- |
| `BLOG_HOST`          | `127.0.0.1`      | Bind host address                                                    |
| `BLOG_PORT`          | `8080`           | HTTP port                                                             |
| `BLOG_TITLE`         | `Personal Blog`  | Site title shown in templates                                        |
| `BLOG_CONTENT_DIR`   | `content`        | Directory where article `.json` files are stored                     |
| `BLOG_ADMIN_USER`    | *(required)*     | Admin login username                                                  |
| `BLOG_ADMIN_PASSWORD`| *(required)*     | Admin login password                                                  |
| `BLOG_SESSION_KEY`   | *(required)*     | HMAC signing key, min. 32 chars — generate with `openssl rand -hex 32` |
| `BLOG_SESSION_TTL`   | `86400` (24h)    | Session lifetime, in seconds or an ISO-8601 duration (e.g. `PT24H`)   |

Unknown `BLOG_*` variables (typos included) are rejected at startup.

---

## Development

### Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)

### Setup

```bash
uv sync
cp .env.example .env
```

Fill in `BLOG_ADMIN_USER`, `BLOG_ADMIN_PASSWORD`, and `BLOG_SESSION_KEY` in
`.env`, then optionally seed sample articles:

```bash
make seed
```

### Running locally

```bash
make run
```

### Testing & quality assurance

```bash
make test        # run the test suite
make coverage    # run tests with coverage (100% required)
make typecheck   # mypy, strict mode
make lint        # ruff check + format --check
make format      # ruff format + check --fix
```

### Other commands

```bash
make seed   # copy sample articles from seed/ into content/
make clean  # remove content/, caches, and __pycache__ dirs
```

---

## CI

Every push and pull request to `main` runs lint, type checking, and the full
test suite with coverage — see
[`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## Project origin

Built as an implementation of the
[Personal Blog](https://roadmap.sh/projects/personal-blog) project from
[roadmap.sh](https://roadmap.sh).

---

## License

MIT — see [LICENSE](LICENSE).
