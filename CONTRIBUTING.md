# Contributing

## Development Setup

```bash
git clone https://github.com/R1khz/bio_toolkit.git
cd bio_toolkit
make setup
```

`make setup` creates the virtual environment, installs all dependencies, and copies `.env.example` to `.env`.

## Environment Variables

Edit `.env` and set at minimum:

```
NCBI_EMAIL=your@email.com       # required for NCBI API usage
NCBI_API_KEY=                   # optional but recommended for higher rate limits
```

## Running Tests

```bash
make test
```

## Linting

```bash
make lint
```

## Coverage Report

```bash
make coverage
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests for your changes
4. Ensure `make lint` and `make test` both pass
5. Open a pull request against `main`

## Code Style

- Line length: 100 characters (enforced by ruff)
- Python 3.11+
- Type hints throughout
- No comments that describe what the code does — only why, when non-obvious
