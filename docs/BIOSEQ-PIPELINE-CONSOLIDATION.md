# BioSeq Pipeline Consolidation

This note records what was kept from `bioseq-pipeline`, what was intentionally not migrated, and when the old repo is safe to delete.

## Kept In Bio Toolkit

- the practical idea of flat tabular exports for downstream loading
- the assumption that one run may contain multiple analyzed records
- the direction of adding persistence and an API on top of the existing analysis core

`bio_toolkit` now exposes flat CSV export for:

- `analyze --output ... --export-format csv`
- `batch --output ... --export-format csv`

These exports are the preferred bridge into future MySQL ingestion.

## Not Migrated

- local BLAST support
- SQLite/PostgreSQL-specific persistence code
- FastAPI scaffolding from `bioseq-pipeline`
- file-writing logger side effects on import

These parts were not migrated because the current direction is:

- keep BLAST remote-only
- avoid carrying a second project-level runtime model
- design persistence directly for MySQL instead of adapting the old SQLite-first shape
- add any future API on top of `bio_toolkit` instead of maintaining a parallel app

## Deletion Rule

`bioseq-pipeline` is safe to delete if all of the following are true:

- you do not need its current FastAPI prototype
- you do not need its SQLite/PostgreSQL persistence code as working code
- you do not want local BLAST support
- your active CLI workflow is now centered on `bio_toolkit`

Given the current direction, the old repo should be treated as deprecated reference material, not as an active dependency.
