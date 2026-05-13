# Changelog

All notable changes to this project are documented here.

## [1.0.0] — 2026-05-13

### Added

- Guided `start` flow with provider-aware follow-up actions
- `search` command for NCBI nucleotide/protein, UniProt, and KEGG databases
- `query` command for direct provider API access (NCBI, UniProt, KEGG, AlphaFold)
- `fetch` command with automatic local cache reuse
- `analyze` command — sequence statistics, GC/AT content, ORF scanning, motif search, protein domain enrichment, UniProt and AlphaFold integration
- `annotate` command with JSON/CSV/Markdown/HTML export
- `compare` command for side-by-side multi-record metric comparison
- `transform` command — reverse complement, translation, subsequence extraction
- `blast` command for remote NCBI BLAST from local or cached queries
- `batch` command for repeated fetch or analysis from accession lists
- `cache` command for local cache inspection
- `doctor` command for runtime environment validation
- Interactive TTY picker with arrow-key navigation and provider-aware follow-up actions
- `--plain` mode for reduced-color terminal output
- JSON, CSV, TSV, Markdown, and HTML export formats across commands
- Service/domain/contract architecture with a clean CLI layer
