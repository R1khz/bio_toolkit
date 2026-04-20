# Requirements: Bio Toolkit

**Defined:** 2026-04-19
**Core Value:** Find a sequence once, keep it locally, and analyze it from a Linux terminal without repeated manual lookup.

## v1 Requirements

### Search

- [ ] **SEARCH-01**: User can search the NCBI `nucleotide` database from the terminal with a free-text query
- [ ] **SEARCH-02**: User can search the NCBI `protein` database from the terminal with a free-text query
- [ ] **SEARCH-03**: User can narrow searches by organism and maximum result count
- [ ] **SEARCH-04**: User can inspect search results in a concise terminal table with accession, title, organism, and source database

### Retrieval And Cache

- [ ] **FETCH-01**: User can fetch a selected NCBI record by accession from the terminal
- [ ] **FETCH-02**: User can save fetched records into a reusable local cache with metadata about source, date, and format
- [ ] **FETCH-03**: User can re-open a cached record without performing a new NCBI request
- [ ] **FETCH-04**: User can inspect what is already stored in cache before downloading again

### Analysis

- [ ] **ANLY-01**: User can analyze a local FASTA file or cached record from the terminal
- [ ] **ANLY-02**: User can obtain sequence length and molecule-aware composition metrics
- [ ] **ANLY-03**: User can run GC and basic nucleotide summary on DNA or RNA sequences
- [ ] **ANLY-04**: User can run motif review and ORF scanning on nucleotide sequences
- [ ] **ANLY-05**: User can export analysis results to JSON

### Terminal UX

- [ ] **TERM-01**: User can run all supported commands in a Linux shell without GUI dependencies
- [ ] **TERM-02**: User can read outputs in a polished terminal presentation with tables, panels, status messages, and readable errors
- [ ] **TERM-03**: User can disable color or run in plain output mode when terminal support is limited
- [ ] **TERM-04**: User can discover usage through consistent command help and examples

### Engineering

- [ ] **ENG-01**: Maintainer can install the project from documented Python project metadata and a virtual environment workflow
- [ ] **ENG-02**: Maintainer can configure NCBI credentials and runtime paths through `.env` or environment variables
- [ ] **ENG-03**: Maintainer can run linting and tests from documented local commands

## v2 Requirements

### Guided Workflow

- **GUIDE-01**: User can move through search results interactively in a TTY terminal and select one result without manually copying the accession
- **GUIDE-02**: After selecting a result, user can choose a next action from the terminal flow such as printing the accession, fetching the record, or fetching and analyzing it

### Batch Workflow

- **BATCH-01**: User can process a text file containing multiple accessions in one command
- **BATCH-02**: User can process multiple local sequence files in one command
- **BATCH-03**: Batch runs produce a readable per-item status summary and structured output for later inspection

### Comparison And Transforms

- **COMPARE-01**: User can compare at least two local or cached sequence records side by side
- **COMPARE-02**: Comparison output highlights practical differences such as length, molecule type, GC, ORFs, and motif hits when relevant
- **XFORM-01**: User can run common transforms such as translation, reverse complement, and subsequence extraction from the CLI
- **XFORM-02**: Transform outputs can be printed or saved in a reusable sequence format

### Annotation And Export

- **ANN-01**: User can inspect annotation-rich metadata and features from GenBank or NCBI-backed records
- **ANN-02**: Annotation output includes practical fields such as accession, organism, gene/product labels, and selected feature summaries
- **EXPORT-01**: User can export results in `csv` and `markdown` in addition to JSON
- **EXPORT-02**: User can generate a shareable HTML report without losing terminal-first usability

### BLAST

- **BLAST-01**: User can submit a remote BLAST workflow from the toolkit and retrieve summarized hits
- **BLAST-02**: The codebase leaves a clear integration path for local BLAST+ usage on Linux servers

### Additional Data Support

- **DATA-01**: User can ingest FASTQ inputs for quality-oriented workflows
- **DATA-02**: User can integrate the toolkit into Snakemake or similar reproducible pipelines

## Out of Scope

| Feature | Reason |
|---------|--------|
| Web dashboard | CLI-first Linux workflow is the primary use case |
| Shared database service | Not needed for the first single-user research tool |
| Heavy genome assembly or alignment pipeline | Too broad for the first useful release |
| Graphical plotting suite | Nice later, but not core to terminal-first sequence review |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENG-01 | Phase 1 | Complete |
| ENG-02 | Phase 1 | Complete |
| ENG-03 | Phase 1 | Complete |
| TERM-01 | Phase 1 | Complete |
| TERM-04 | Phase 1 | Complete |
| SEARCH-01 | Phase 2 | Complete |
| SEARCH-02 | Phase 2 | Complete |
| SEARCH-03 | Phase 2 | Complete |
| SEARCH-04 | Phase 2 | Complete |
| FETCH-01 | Phase 2 | Complete |
| FETCH-02 | Phase 3 | Complete |
| FETCH-03 | Phase 3 | Complete |
| FETCH-04 | Phase 3 | Complete |
| ANLY-01 | Phase 4 | Complete |
| ANLY-02 | Phase 4 | Complete |
| ANLY-03 | Phase 4 | Complete |
| ANLY-04 | Phase 4 | Complete |
| ANLY-05 | Phase 4 | Complete |
| TERM-02 | Phase 5 | Complete |
| TERM-03 | Phase 5 | Complete |
| GUIDE-01 | Phase 6 | Complete |
| GUIDE-02 | Phase 6 | Complete |
| BATCH-01 | Phase 7 | Complete |
| BATCH-02 | Phase 7 | Complete |
| BATCH-03 | Phase 7 | Complete |
| COMPARE-01 | Phase 8 | Complete |
| COMPARE-02 | Phase 8 | Complete |
| XFORM-01 | Phase 8 | Complete |
| XFORM-02 | Phase 8 | Complete |
| ANN-01 | Phase 9 | Complete |
| ANN-02 | Phase 9 | Complete |
| EXPORT-01 | Phase 9 | Complete |
| EXPORT-02 | Phase 9 | Complete |
| BLAST-01 | Phase 10 | Complete |
| BLAST-02 | Phase 10 | Complete |
| DATA-01 | Future | Planned |
| DATA-02 | Future | Planned |

**Coverage:**
- v1 requirements: 20 total
- v2+ requirements: 16 total
- Mapped to phases/future: 36
- Unmapped: 0

---
*Requirements defined: 2026-04-19*
*Last updated: 2026-04-20 after remote BLAST implementation and release-readiness updates*
