# Docker Wrapper

- [Docker Wrapper](#docker-wrapper)


This repo contains a python helper library that allows us to automate
a number of workflow actions when interacting with Docker.

For details see the rest of the [documentation](./docs/index.md).

# Documentation

HTML rendered documentation is available at [DockerWrapper](https://idoudali.github.io/DockerWrapper/).

# Quick Start

Install [uv](https://docs.astral.sh/uv/), then set up the project environment
and git hooks:

```bash
uv sync --all-groups
uv run pre-commit install
uv run pre-commit install --hook-type pre-push
```

Use conventional commits via commitizen:

```bash
uv run cz commit
```

`make install`, `make check`, `make fmt`, `make test`, and `make docs` wrap
the same uv commands. Agent and contributor guidelines live in
[`AGENTS.md`](AGENTS.md).
