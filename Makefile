.PHONY: run test lint format seed clean

run:
	uv run python -m personal_blog

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .

seed:
	mkdir -p content
	cp seed/*.json content/

clean:
	rm -rf content .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
