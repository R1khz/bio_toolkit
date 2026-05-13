# Portfolio Professionalization — Design Spec

**Date:** 2026-05-13  
**Author:** Richard Yoel Flores Iuit  
**Goal:** Make bio-toolkit public-ready as a portfolio project

---

## Context

bio-toolkit is a Linux-first CLI toolkit for bioinformatics (NCBI, UniProt, KEGG, AlphaFold, BLAST). The code quality and architecture are already solid — 116 tests, zero lint errors, clean service/domain/contract layers. What's missing is the public-facing packaging: CI/CD, clean author metadata, legacy file removal, documentation polish, and visual evidence of what the tool does.

---

## Scope

Five sequential phases. Each is independently deployable. No new features.

---

## Phase 1 — Repo Hygiene

**What:** Update configuration files only. No source code changes.

- `.gitignore`: add `.planning/`, `.superpowers/`, `.codex`, `inputs/`
- `pyproject.toml`:
  - `authors = [{ name = "Richard Yoel Flores Iuit", email = "yoelflores0211@gmail.com" }]`
  - `version = "1.0.0"`
  - Add `[project.urls]` block: Homepage, Repository, Documentation
- `LICENSE`: update copyright name to "Richard Yoel Flores Iuit"
- `Makefile`: `setup` target adds `cp -n .env.example .env` (skips if already exists)

**Risk:** None — no executable code changes.

---

## Phase 2 — Remove Legacy Files

**What:** Delete the three legacy shim files after verifying what is still consumed.

Files to remove:
- `src/bio_toolkit/legacy_cli.py` (3,503 lines — the monolith predecessor)
- `src/bio_toolkit/legacy_config.py` (29 lines)
- `src/bio_toolkit/legacy_providers.py` (31 lines)

Process:
1. Grep for all imports of these three modules across the codebase.
2. `cli/__init__.py` currently re-exports from `legacy_cli` for backward compat — move any surviving shim to `cli/__init__.py` directly or inline into callers.
3. Delete the three files.
4. Run `make test` and `make lint` to confirm nothing broke.

**Risk:** Medium — requires careful import audit before deletion. Mitigated by running tests immediately after.

---

## Phase 3 — README + Docs

**What:** Add badges, polish install instructions, add CHANGELOG and CONTRIBUTING.

README changes:
- Add badge row after the title: Python 3.11+, MIT license, CI status (GitHub Actions), version
- Add `pipx install bio-toolkit` to the Installation section (for public use)
- Add a `## Demo` section with a placeholder for the terminal GIF (recorded separately by the author using `vhs` or `asciinema`)

New files:
- `CHANGELOG.md`: one entry per completed milestone (v1.0.0 with feature list drawn from README)
- `CONTRIBUTING.md`: minimal — how to set up the dev environment, how to run tests, how to submit a PR

**Risk:** None — pure documentation.

---

## Phase 4 — CI/CD + Coverage

**What:** Add GitHub Actions workflow and test coverage measurement.

`.github/workflows/ci.yml`:
- Trigger: push and pull_request on `main`
- Matrix: Python 3.11 on ubuntu-latest
- Steps: checkout → setup Python → install `.[dev]` → `ruff check` → `pytest`
- No secrets required (tests are fully offline/mocked)

`pyproject.toml` dev dependencies: add `pytest-cov>=5.0`

`Makefile`: add `coverage` target:
```
coverage:
    $(VENV_PYTHON) -m pytest --cov=bio_toolkit --cov-report=term-missing
```

Badge: use shields.io static badge for coverage once a baseline number is known (or Codecov if the author wants automated tracking).

**Risk:** Low — tests already pass. The only unknown is whether any test requires TTY that GitHub Actions won't have (already mocked in the test suite).

---

## Phase 5 — Demo Placeholder

**What:** Document how to record the terminal demo and add the placeholder to the README.

The demo cannot be automated by the assistant (requires interactive terminal and real NCBI credentials). The design is:

Recommended flow to record:
```bash
./bio-toolkit search "hemoglobin" --database protein --organism "Homo sapiens"
./bio-toolkit fetch NP_000509.1 --database protein
./bio-toolkit analyze NP_000509.1 --source cache --database protein --rettype fasta
```

Tool recommendation: `vhs` (generates GIF from a `.tape` script) or `asciinema` + `svg-term`.

README gets a `## Demo` section with a placeholder image tag and instructions in a comment.

---

## Out of Scope

- New features
- Database persistence
- Web UI
- Alignment pipelines
- Snakemake integration
- Publishing to PyPI (can follow after portfolio review)

---

## Success Criteria

- [ ] `git ls-files | grep -E '\.planning|\.superpowers|legacy'` returns nothing
- [ ] `pyproject.toml` has full author name, email, urls, version 1.0.0
- [ ] `make test` passes
- [ ] `.github/workflows/ci.yml` exists and the badge renders on GitHub
- [ ] README has badges and a Demo section
- [ ] `CHANGELOG.md` and `CONTRIBUTING.md` exist
