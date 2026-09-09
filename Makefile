.PHONY: help lint lint-fix format format-check check

help:
	@echo "Available Makefile commands:"
	@echo "  make lint             - Runs the linter (ruff check)"
	@echo "  make lint-fix         - Automatically fixes linter issues (ruff check --fix)"
	@echo "  make format           - Formats the code (ruff format)"
	@echo "  make format-check     - Checks whether the code is formatted (ruff format --check)"
	@echo "  make check            - Runs the linter and validates formatting"

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

check: lint format-check
