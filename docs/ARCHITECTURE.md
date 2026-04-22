# Architecture

## Goal

Build a CLI-first bioinformatics toolkit that works well on Linux terminals and remote servers, while staying modular enough to grow beyond the MVP.

## Core Modules

### CLI Layer

Handles command parsing, user help, terminal formatting, tables, status messages, and error presentation.

Planned commands:

- `start`: guided provider-aware search and action flow
- `search`: search NCBI
- `fetch`: download a record into local cache
- `analyze`: analyze a local or cached sequence
- `annotate`: inspect richer metadata and selected features
- `compare`: compare records side by side
- `transform`: produce reusable FASTA transforms
- `blast`: submit remote BLAST jobs and summarize hits
- `cache`: inspect or clean local cache
- `doctor`: validate runtime configuration

### Config Layer

Reads environment variables and resolves runtime paths such as cache and output directories.

Primary configuration values:

- `NCBI_EMAIL`
- `NCBI_API_KEY`
- `NCBI_TOOL_NAME`
- `BIO_TOOLKIT_CACHE_DIR`
- `BIO_TOOLKIT_OUTPUT_DIR`

### Provider Client Layer

Responsible for talking to upstream sequence or annotation services and translating responses into shared internal models.

Initial responsibilities:

- NCBI search for `nucleotide` and `protein`
- NCBI fetch of FASTA or GenBank text
- UniProt protein search and record enrichment
- KEGG search and sequence retrieval when available
- AlphaFold metadata lookup for UniProt-linked proteins
- submit remote BLAST jobs, poll RID status, and parse tabular results
- respect upstream API etiquette and rate limits

### Cache Layer

Stores fetched records locally to avoid repeated manual lookups and repeated API hits.

Planned approach:

- disk cache for raw record payloads
- lightweight metadata index for source, accession, query, retrieval date, and format
- deterministic cache keys so repeated requests reuse stored data

### Parsing Layer

Transforms FASTA or GenBank content into normalized in-memory sequence objects for downstream analysis.

Primary parser dependency:

- Biopython

### Analysis Layer

Runs sequence analysis on local or cached records.

MVP analysis targets:

- sequence length
- GC content for nucleotides
- base or amino acid composition
- simple motif review
- ORF scanning for nucleotide sequences
- heuristic protein domain review
- optional UniProt and AlphaFold enrichment for protein records

### Output Layer

Produces both human-readable terminal output and machine-readable files.

Current outputs:

- Rich tables in terminal
- JSON export
- CSV/TSV export for BLAST
- CSV/Markdown/HTML export for annotations

## Data Flow

```text
user command
  -> CLI
  -> config
  -> provider client or local file reader
  -> cache
  -> parser
  -> analysis
  -> terminal report or JSON output
```

## Architectural Decisions

| Decision | Reason |
|----------|--------|
| CLI only for v1 | The main use case is Linux terminal and server execution |
| Typer + Rich | Good balance of usability, structure, and terminal aesthetics |
| Python package layout under `src/` | Cleaner imports, packaging, and testing |
| Dedicated provider client layer | Keeps external API handling separate from analysis logic |
| Cache as first-class concern | The main user value is not searching the same sequence repeatedly |
| JSON as first export format | Easy integration with notebooks and later pipelines |
| Remote-first BLAST | Fits laptop and server usage without forcing local database downloads |

## BLAST Integration Boundary

The current BLAST workflow is intentionally remote-only.

- The CLI owns query loading, terminal waiting feedback, and result rendering.
- The NCBI client owns submission, status polling, and result parsing.
- Exporters own file serialization for BLAST outputs.

This keeps the future persistence/API path clean: MySQL-backed saved runs or a small HTTP layer can plug into the same analysis and export layers without rewriting the user-facing command contract.

## Non-Goals For v1

- web frontend
- distributed services
- large workflow orchestration
- heavy alignment or assembly pipelines

## Near-Term Expansion Direction

- keep BLAST remote-only
- add MySQL-backed persistence for saved analysis runs
- add a thin API layer on top of the existing CLI/core report contracts
