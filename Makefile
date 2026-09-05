SHELL := /bin/bash

.PHONY: install check fmt test docs help

install: ## create .venv and install runtime + dev + docs groups
	uv sync --all-groups

fmt: ## auto-fix lint and format
	uv run ruff check --fix .
	uv run ruff format .

check: ## lint, format check, and type-check
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src tests

test: ## run pytest with coverage
	uv run pytest

docs: ## build MkDocs site
	uv run mkdocs build

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
