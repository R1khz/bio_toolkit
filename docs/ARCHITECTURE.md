# Architecture

## Goal

Keep `bio_toolkit` CLI-first today while separating orchestration, providers, storage, and presentation so the same core can later back an API or web interface.

## Package Layout

### `src/bio_toolkit/cli/`

Terminal adapter layer.

- `app.py`: Typer composition root
- `commands/`: translate CLI flags into service requests
- `presenters/`: Rich tables, panels, previews, and export notices
- `interactive/`: picker-facing helpers for guided terminal flows

### `src/bio_toolkit/services/`

Use-case orchestration layer.

- owns request validation and cross-module coordination
- talks to providers, storage, and domain code
- returns transport-neutral response models instead of terminal output

Current service areas include:

- `search`, `query`, `fetch`
- `analyze`, `annotate`, `compare`, `transform`
- `blast`, `batch`, `cache`, `doctor`, `start`

### `src/bio_toolkit/contracts/`

Typed request/response payloads shared across adapters.

- stable shapes for CLI today
- reusable inputs/outputs for a future API
- strict validation with Pydantic v2

### `src/bio_toolkit/providers/`

External system adapters.

- NCBI
- UniProt
- KEGG
- AlphaFold
- provider selection and normalization rules

### `src/bio_toolkit/storage/`

Persistence and file adapters.

- `storage/cache/`: local record cache and metadata index
- `storage/files/`: FASTA/GenBank parsing and serialization

### `src/bio_toolkit/config/`

Runtime discovery and environment-backed settings.

- runtime root detection
- installation diagnostics
- cache/output directory resolution

### `src/bio_toolkit/domain/`

Pure or mostly pure business logic.

- `analysis/`: molecule detection, sequence analysis, comparisons
- `annotations/`: annotation extraction and report shaping
- `sequences/`: transforms and related helpers

### Compatibility Shims

Flat modules such as `legacy_cli.py`, `legacy_config.py`, `legacy_providers.py`, `analysis.py`, `annotations.py`, `transforms.py`, `cache_store.py`, `sequence_io.py`, and `provider_queries.py` remain as compatibility surfaces while imports migrate to the package layout above.

## Data Flow

```text
CLI command
  -> cli.commands.<use_case>
  -> services.<use_case>
  -> providers / storage / domain
  -> contracts.<use_case>
  -> cli.presenters.<use_case>
```

## Design Rules

- CLI modules must not own business logic.
- Service modules must not print to the terminal.
- Presenter modules must not call provider or storage code directly.
- New reusable behavior should go into `services/`, `domain/`, `providers/`, or `storage/`, not back into `legacy_cli.py`.
- Future API code must reuse `services/` and `contracts/`, not duplicate orchestration.

## Expansion Path

- keep BLAST remote-first
- add persistence or job tracking above existing services
- introduce `src/bio_toolkit/api/` later as another adapter over the same service layer
