# Agent guidelines

This file is the source of truth for humans and coding agents working in this
repository. Follow it for Cursor, Claude Code, Codex, and similar tools.

## Project

`docker_wrapper` is a typed Python library and Typer CLI that automates common
Docker workflows: discover image extensions, build/pull/push images, and run
commands or interactive prompts inside containers.

| Path | Role |
| --- | --- |
| `src/docker_wrapper/` | Installable package (`cli.py`, `docker_helpers.py`) |
| `tests/` | pytest suite |
| `sample-images/` | Example image extensions used by `repo-cli.py` |
| `repo-cli.py` | Example repo entrypoint that registers images |
| `docs/` | MkDocs user and API docs |
| `pyproject.toml` | Project metadata, dependencies, and tool config |

## Tooling

Use **uv** for environments, dependencies, and command execution. Do not add
`requirements.txt`, `setup.py`, `Pipfile`, or `tox.ini`.

```bash
uv sync --all-groups          # create .venv and install runtime + dev + docs
uv lock                       # refresh uv.lock after dependency edits
uv add <pkg>                  # runtime dependency
uv add --group dev <pkg>      # development dependency
uv run pytest                 # run a tool in the project environment
```

Quality tools (all configured in `pyproject.toml`):

| Tool | Purpose | Command |
| --- | --- | --- |
| Ruff | Lint + format (replaces Black, isort, Flake8) | `uv run ruff check --fix .` and `uv run ruff format .` |
| mypy | Strict static types | `uv run mypy src tests` |
| pytest | Tests and coverage | `uv run pytest --cov` |
| pre-commit | Git hooks for the above | `uv run pre-commit run -a` |
| commitizen | Conventional commits | `uv run cz commit` |

`make install`, `make check`, `make fmt`, `make test`, and `make docs` wrap the
same commands.

## Coding standards

Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
and PEP 8, as summarized in the idea-space Python best practices:

- `snake_case` for functions and variables; `CamelCase` for classes.
- Google-style docstrings with `Args:`, `Returns:`, and `Raises:` where useful.
- Explicit imports only. Keep imports at the top of the module.
- Type-hint public functions and keep `mypy --strict` passing.
- Prefer built-in generics and `|` unions (`list[str]`, `str | None`) over
  `typing.List` / `Optional`.
- Do not add inline imports unless a circular import is documented.

Ruff enforces formatting, import order, bugbear, naming, pyupgrade, security,
and Google pydocstyle. Do not disable a rule to paper over a real issue; use a
targeted `noqa` only when the violation is intentional (for example Typer
dynamic signatures).

## Testing

- Put tests in `tests/` and name them `test_*.py`.
- Prefer pytest fixtures and `pytest-mock` over ad-hoc stubs.
- Cover new CLI behavior and `DockerImage` hashing / run-argument logic.
- Run `uv run pytest` before finishing a change. If you touch packaging or
  tool config, also run `uv run ruff check .`, `uv run ruff format --check .`,
  and `uv run mypy src tests`.

## Docker image extensions

Each image folder under `sample-images/` (or a consumer repo's image directory)
must contain:

- `Docker/Dockerfile` (and related files such as `entrypoint.sh`)
- `docker_wrapper_extensions.py` defining a `DockerImage` subclass with a
  unique `NAME`

`create_cli(image_dir=...)` discovers those classes and registers Typer
commands. Preserve that contract unless you are intentionally changing it and
updating docs and tests together.

## Git

- Use Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`,
  `test:`, `ci:`). Prefer `uv run cz commit`.
- Do not commit secrets, `.venv/`, or generated `site/` / `htmlcov/` output.
- Keep `uv.lock` committed and in sync with `pyproject.toml`.

## Safety

- Never force-push to `main`.
- Always run `uv run pytest` before committing. If you touched packaging or
  tool config, also run `uv run ruff check .`, `uv run ruff format --check .`,
  and `uv run mypy src tests`.
- Use conventional commits.
