# API Readiness

`bio_toolkit` remains CLI-only in this phase.

The current architecture is intentionally prepared for a future API or web layer by keeping the use-case core outside terminal code.

## Reserved Future Layer

When an HTTP or web interface is added later, create:

`src/bio_toolkit/api/`

That layer should call:

- `bio_toolkit.services.*` for use-case execution
- `bio_toolkit.contracts.*` for request/response validation and serialization

It should not import:

- `bio_toolkit.cli.presenters.*`
- `bio_toolkit.legacy_cli`

## Mapping Rule

The future API layer should:

1. map HTTP requests into service request models
2. call the existing service layer
3. map service responses into JSON or async job payloads

It must not reimplement provider selection, cache behavior, file parsing, analysis rules, or BLAST orchestration.

## Likely First API Candidates

- `search`
- `query`
- `fetch`
- `analyze`
- `annotate`
- `compare`
- `transform`

`blast` and `batch` are also reusable through the same service layer, but they will likely need job/status semantics before a production web surface.
