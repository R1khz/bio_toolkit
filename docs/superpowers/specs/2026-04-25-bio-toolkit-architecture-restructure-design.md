# Bio Toolkit Internal Architecture Restructure Design

Date: 2026-04-25
Project: `bio_toolkit`
Status: Approved for planning

## Overview

This design restructures the internal codebase of Bio Toolkit without changing its external CLI behavior.

The goal is to turn the current flat `src/bio_toolkit/` layout into a clearer architecture organized around use-case services, with explicit boundaries for presentation, external providers, storage, configuration, contracts, and domain logic. The main future-facing requirement is to prepare the project for a future API/service layer while keeping the current CLI as the only user-facing interface for now.

## What This Design Must Achieve

1. Keep the current CLI behavior and command surface stable.
2. Reorganize the code so responsibilities are easier to locate and reason about.
3. Introduce explicit request/response contracts between layers.
4. Separate orchestration logic from external adapters and presentation code.
5. Align `src/`, `tests/`, and `docs/` with the same architectural model.
6. Create a structure that can later support an API/service surface over the same core logic.

## Out of Scope

1. Changing user-visible command behavior.
2. Renaming CLI commands or flags.
3. Adding new features as part of the restructure.
4. Introducing a web frontend or an HTTP API in this phase.
5. Performing a destructive all-at-once rewrite.

## Design Principles

1. Organize core orchestration by use case, not by generic utility buckets.
2. Keep presentation code out of business logic.
3. Keep provider, cache, and file access behind explicit adapter boundaries.
4. Prefer explicit models over anonymous `dict` payloads at layer boundaries.
5. Migrate incrementally, with compatibility at the CLI boundary until the new structure is complete.
6. Use folder names that communicate ownership and responsibility without reading internals.

## Target Source Layout

```text
src/bio_toolkit/
  cli/
    app.py
    commands/
    presenters/
    interactive/
  services/
    start/
    search/
    query/
    fetch/
    analyze/
    annotate/
    compare/
    transform/
    blast/
    batch/
    cache/
    doctor/
  contracts/
    common/
    search/
    query/
    fetch/
    analyze/
    annotate/
    compare/
    transform/
    blast/
    batch/
    cache/
    doctor/
    start/
  providers/
    ncbi/
    uniprot/
    kegg/
    alphafold/
  storage/
    cache/
    files/
  config/
    settings.py
    runtime.py
  domain/
    sequences/
    analysis/
    annotations/
  shared/
    formatting/
    errors/
    utils/
```

## Layer Responsibilities

### `cli/`

The CLI layer owns Typer wiring, command parsing, terminal formatting, Rich rendering, and interactive terminal behavior. It can translate terminal input into service requests and translate service responses into terminal output, but it must not own domain rules, provider orchestration, or storage policy.

### `services/`

This is the main application layer. Each folder represents a use case or command-level workflow such as `search`, `query`, `fetch`, or `analyze`. A service receives explicit input models, coordinates domain helpers and adapters, and returns explicit output models. Services must not print, render Rich components, or depend directly on Typer.

### `contracts/`

This layer defines request/response DTOs and shared transport-neutral models. It exists to make layer boundaries explicit and reusable. The CLI will depend on these contracts now, and a future API can depend on the same contracts later.

### `providers/`

This layer contains external upstream adapters for NCBI, UniProt, KEGG, and AlphaFold. It owns HTTP requests, provider-specific parsing, provider-specific data normalization, and provider-specific adapter errors. It must not know about Rich output or command presentation.

### `storage/`

This layer owns local persistence concerns such as cache storage and file sequence I/O. It handles filesystem interaction, cache layout, and storage-specific errors. It must not contain use-case orchestration.

### `config/`

This layer owns runtime settings and runtime path/directory resolution. It should expose a small, stable surface for loading settings and validating runtime directories.

### `domain/`

This layer contains pure or mostly pure domain logic such as sequence analysis, comparisons, transforms, annotation helpers, and domain-specific rule evaluation. It should remain reusable from services without knowledge of CLI or provider details.

### `shared/`

This layer holds cross-cutting pieces that are truly shared and not better owned elsewhere. It should stay intentionally small. It is not a dumping ground for code with unclear ownership.

## Service Folder Convention

Each use-case folder under `services/` should follow a predictable internal pattern:

```text
services/search/
  service.py
  request.py
  response.py
  errors.py
  helpers.py
```

Not every use case needs all files immediately, but `service.py`, `request.py`, and `response.py` should be the default pattern. This makes each use case easy to discover and keeps orchestration logic close to its boundary models.

## Module Mapping From Current Code

The current flat modules should be redistributed as follows.

### CLI and Presentation

- `cli.py` -> split into `cli/app.py`, `cli/commands/*.py`, and presentation helpers
- `cli_views.py` -> `cli/presenters/analysis_presenter.py`, `cli/presenters/query_presenter.py`, `cli/presenters/common.py`
- `interactive_picker.py` -> `cli/interactive/picker.py`

### Services

- `provider_queries.py` -> `services/query/service.py`
- command orchestration currently embedded in `cli.py` -> distributed into the matching use-case folders under `services/`
- provider selection logic from `providers.py` -> split between `services/search/` and `services/query/` support modules where needed

### Providers

- `ncbi.py` -> `providers/ncbi/client.py`, `providers/ncbi/models.py`, `providers/ncbi/blast.py`
- `uniprot.py` -> `providers/uniprot/client.py`, `providers/uniprot/models.py`
- `kegg.py` -> `providers/kegg/client.py`, `providers/kegg/models.py`
- `alphafold.py` -> `providers/alphafold/client.py`

### Storage and Config

- `cache_store.py` -> `storage/cache/store.py`, `storage/cache/models.py`
- `sequence_io.py` -> `storage/files/sequence_reader.py`, `storage/files/sequence_writer.py`
- `config.py` -> `config/settings.py`, `config/runtime.py`

### Domain

- `analysis.py` -> `domain/analysis/sequence_analyzer.py`, `domain/analysis/comparison.py`, `domain/analysis/warnings.py`
- `annotations.py` -> `domain/annotations/report_builder.py` plus use-case orchestration in `services/annotate/service.py`
- `transforms.py` -> `domain/sequences/transforms.py` plus use-case orchestration in `services/transform/service.py`

### Export and Presentation Support

- `exporters.py` -> `cli/presenters/exporters/*.py` unless later split reveals a domain-neutral export layer is needed

## Contracts and DTOs

The new design explicitly requires contracts between layers.

Each major use case should define:

1. A request model used by the CLI or future API to call the service.
2. A response model returned by the service.
3. Shared nested models for common structures such as search results, provider metadata, fetch records, analysis summaries, and export metadata.

This design does not force one validation library at this stage. The important requirement is explicit structure and type clarity. The implementation plan can decide whether the first iteration uses `dataclass` models or a validation library, but the architecture assumes named models instead of anonymous payloads.

## Error Model

Errors should be separated by boundary:

1. Provider adapters raise provider-specific technical errors.
2. Storage adapters raise cache/file/persistence errors.
3. Services translate lower-level failures into use-case-level errors with stable meaning.
4. CLI presenters translate those service errors into terminal-friendly output.

The critical architectural rule is that the CLI should not need to understand provider internals in order to report a user-facing failure cleanly.

## Testing Structure

The test suite should be reorganized to mirror the architecture:

```text
tests/
  unit/
    domain/
    services/
    providers/
    storage/
    cli/
    config/
  integration/
    services/
    providers/
  contracts/
    cli_to_service/
    service_to_provider/
  smoke/
    cli/
```

### Testing Intent

- `unit/` verifies isolated logic inside each layer.
- `integration/` verifies multi-module collaboration inside the new architecture.
- `contracts/` verifies request/response structure and adapter translation boundaries.
- `smoke/cli/` verifies that key commands still run and preserve the public command surface.

This design keeps the existing emphasis on CLI contract testing, but places it in a clearer testing taxonomy.

## Documentation Alignment

The architecture docs and development docs should be updated to describe the new layered structure and use-case-centered `services/` model. The project should document:

1. The purpose of each top-level folder under `src/bio_toolkit/`.
2. The rule that CLI only handles input/output concerns.
3. The rule that service layers use explicit contracts.
4. The rule that provider and storage layers are adapters, not orchestrators.

## Migration Strategy

The migration should be phased, not big-bang.

### Phase 1: Architectural Scaffolding

Create the new folder tree, common contracts, shared error categories, and base module layout. No behavior change should happen here beyond import plumbing.

### Phase 2: Adaptation Boundaries

Move `config`, `storage`, and `providers` first. These are foundational adapters and give the later service layer stable dependencies.

### Phase 3: Core Use Cases

Extract the most central workflows into `services/` first:

1. `search`
2. `query`
3. `fetch`
4. `analyze`

These provide the strongest architectural leverage because many other flows depend on the same patterns.

### Phase 4: CLI Decomposition

Break `cli.py` into `cli/app.py`, `cli/commands/`, `cli/presenters/`, and `cli/interactive/`. The CLI should become a thin composition layer over services.

### Phase 5: Remaining Use Cases and Cleanup

Migrate `annotate`, `compare`, `transform`, `blast`, `batch`, `cache`, `doctor`, and `start`, then remove flat legacy modules once no active import path depends on them.

### Phase 6: Test and Docs Realignment

Reorganize the test suite, update architecture and development docs, and verify that the CLI contract remains stable across the migration.

## Risks and Controls

### Risk: Folder churn without real separation

Control: every moved module must get a clearly documented responsibility and boundary. This is not a rename-only exercise.

### Risk: Reintroducing business logic into CLI

Control: all new command implementations should call service entry points through explicit contracts.

### Risk: Contracts become thin wrappers around `dict`

Control: request/response structures must use named, typed models with explicit fields.

### Risk: Migration stalls halfway

Control: plan work in phases that each leave the tree cleaner than before and keep the project runnable at the end of each phase.

## Success Criteria

This design is successful when:

1. The CLI behavior stays stable from a user perspective.
2. A developer can locate orchestration logic by use case under `services/`.
3. External provider code is isolated under `providers/`.
4. Cache and file concerns are isolated under `storage/`.
5. Presentation and Rich rendering are isolated under `cli/presenters/`.
6. Core service entry points communicate through explicit request/response contracts.
7. The resulting structure is suitable for adding a future API layer without extracting the core logic again.
