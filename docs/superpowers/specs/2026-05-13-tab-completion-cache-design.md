# Tab Completion from Cache — Design Spec

**Date:** 2026-05-13  
**Author:** Richard Yoel Flores Iuit  
**Goal:** When typing an accession argument and pressing Tab, show cached sequences automatically

---

## Context

Commands like `analyze`, `compare`, `blast`, `annotate`, and `transform` accept either a local file path or a cached accession. Without completion, the user has to memorize accessions or run `btk cache` first. The cache index already has all the information needed — the completion just needs to read it.

---

## Scope

One new module (`cli/completions.py`) + five command files updated. No new features, no network calls, no config loading.

---

## Component: cli/completions.py

Single public function:

```python
def complete_cached_accession(incomplete: str) -> list[str]:
```

**Behavior:**
- Searches for `index.json` in this order:
  1. `$BIO_TOOLKIT_CACHE_DIR/index.json` (if env var is set)
  2. `./.cache/bio-toolkit/index.json` (relative to CWD — works in dev)
  3. `~/.cache/bio-toolkit/index.json` (XDG default — works globally)
- Reads `data["records"]`, extracts each `accession` field value
- Returns accessions where `accession.startswith(incomplete)`
- On any error (file missing, JSON invalid, key missing): returns `[]` silently — completion must never crash the shell

**No config loading, no imports from services, no network.** Only `json`, `os`, `pathlib`.

---

## Commands Updated

Each of these commands gets `autocompletion=complete_cached_accession` added to its primary `typer.Argument`:

| Command | File | Argument |
|---------|------|----------|
| `analyze` | `cli/commands/analyze.py` | `target` |
| `compare` | `cli/commands/compare.py` | `COMPARE_TARGETS_ARGUMENT` |
| `blast` | `cli/commands/blast.py` | `target` |
| `annotate` | `cli/commands/annotate.py` | `target` |
| `transform` | `cli/commands/transform.py` | `target` |

**Not updated:** `fetch` (fetches new accessions, not from cache), `query` (external providers).

---

## Out of Scope

- Local file completion (Typer/shell handles `.fasta`/`.gb` natively)
- Completion for `--database` or `--rettype` options
- Completion for `fetch` or `query`
- Dynamic refresh or cache watching

---

## Testing

One test file: `tests/unit/cli/test_completions.py`

- Creates a temporary `index.json` with 3 known accessions
- Verifies `complete_cached_accession("")` returns all three
- Verifies `complete_cached_accession("NM_")` returns only those starting with `NM_`
- Verifies `complete_cached_accession("XYZ")` returns `[]`
- Verifies that a missing cache file returns `[]` without raising

---

## Success Criteria

- `btk analyze <TAB>` shows cached accessions
- `btk compare <TAB>` shows cached accessions  
- `btk blast <TAB>` shows cached accessions
- `btk annotate <TAB>` shows cached accessions
- `btk transform <TAB>` shows cached accessions
- Missing cache → silent empty list, no error
- All existing tests pass
