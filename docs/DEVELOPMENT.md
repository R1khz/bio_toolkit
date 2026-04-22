# Development

## Principles

- Linux-first development
- CLI-first user experience
- modular code over one-file scripts
- reproducible local setup
- small phases with visible utility

## Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
python -m bio_toolkit doctor
```

If the repository is moved or copied after installation, reinstall the editable package from the new path:

```bash
./.venv/bin/python -m pip install -e ".[dev]"
```

Required environment variables:

- `NCBI_EMAIL`

Recommended environment variables:

- `NCBI_API_KEY`
- `BIO_TOOLKIT_CACHE_DIR`
- `BIO_TOOLKIT_OUTPUT_DIR`

## Quality Tools

- `pytest` for tests
- `ruff` for linting and formatting
- `pyproject.toml` as the single Python project config entrypoint
- `make lint`, `make test`, and `make doctor` use the repo-local `.venv`

## Expected Workflow

1. Work in small phases from `.planning/ROADMAP.md`
2. Keep user-facing behavior documented in `README.md`
3. Add or update tests with every implemented feature
4. Keep CLI behavior compatible with Linux shell execution
5. Prefer reusable modules over notebook-only logic

## Short-Term Priorities

1. Build the CLI contract and configuration layer
2. Add NCBI search and fetch commands
3. Add local cache behavior
4. Add sequence analysis commands
5. Polish terminal output and package ergonomics
