#!/usr/bin/env sh
set -eu

uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run bandit -q -c pyproject.toml -r src
uv run pytest
uv run pip-audit
