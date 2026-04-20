# Roadmap: Bio Toolkit

## Overview

This roadmap builds a small but professional bioinformatics CLI focused on one practical workflow: search NCBI, fetch useful records once, keep them locally, and analyze them from a Linux terminal with a clean user experience.

Milestone v1 established the core workflow. Milestone v1.1 completed the guided-terminal expansion with interactive picking, batch execution, comparison, annotation, BLAST, and richer exports.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4, 5): planned milestone work
- Decimal phases (2.1, 2.2): urgent insertions if scope changes mid-stream

- [x] **Phase 1: Foundation And CLI Contract** - Create the package structure, runtime configuration, and base command contract for Linux usage
- [x] **Phase 2: NCBI Search And Fetch** - Add sequence discovery from NCBI and record retrieval by accession
- [x] **Phase 3: Local Cache And Record Management** - Persist fetched records locally and make reuse a first-class workflow
- [x] **Phase 4: Sequence Analysis Core** - Analyze local or cached records with core sequence review features
- [x] **Phase 5: Terminal UX And Release Hardening** - Polish the Linux CLI experience, output modes, docs, and release readiness
- [x] **Phase 6: Guided Search And Interactive Selection** - Let the user move through search results in terminal and launch the next action from there
- [x] **Phase 7: Batch Workflow Foundations** - Process lists of accessions and multiple sequence inputs in one run
- [x] **Phase 8: Compare And Transform Commands** - Add side-by-side comparison and practical sequence transforms
- [x] **Phase 9: Annotation And Richer Exports** - Surface higher-level record metadata and support more report formats
- [x] **Phase 10: BLAST Integration** - Wrap remote BLAST first and leave a clear path to local BLAST+ usage

## Phase Details

### Phase 1: Foundation And CLI Contract
**Goal**: The repository behaves like a real Python CLI project with documented setup, environment configuration, tests, linting, and a stable command entrypoint.
**Depends on**: Nothing (first phase)
**Requirements**: [ENG-01, ENG-02, ENG-03, TERM-01, TERM-04]
**Success Criteria** (what must be TRUE):
  1. A maintainer can create a virtual environment, install the package, and understand how to configure it from repo docs.
  2. The project exposes a base CLI entrypoint with command help that works in Linux shells.
  3. The repository contains project metadata, lint/test commands, and a maintainable source layout instead of a one-file prototype.
**Plans**: 2 plans

Plans:
- [x] 01-01: Finalize project scaffold, package metadata, and runtime configuration model
- [x] 01-02: Establish CLI shell, developer docs, and verification baseline

### Phase 2: NCBI Search And Fetch
**Goal**: A user can search NCBI from the terminal, preview useful results, and fetch selected records by accession.
**Depends on**: Phase 1
**Requirements**: [SEARCH-01, SEARCH-02, SEARCH-03, SEARCH-04, FETCH-01]
**Success Criteria** (what must be TRUE):
  1. Search commands support both `nucleotide` and `protein` workflows.
  2. Search results are readable and useful enough to choose records without opening a browser.
  3. A user can fetch a selected record by accession from the terminal.
**Plans**: 2 plans

Plans:
- [x] 02-01: Implement NCBI client for search workflows and result normalization
- [x] 02-02: Implement fetch command and accession-driven record retrieval

### Phase 3: Local Cache And Record Management
**Goal**: Retrieved records become reusable local assets rather than one-off downloads.
**Depends on**: Phase 2
**Requirements**: [FETCH-02, FETCH-03, FETCH-04]
**Success Criteria** (what must be TRUE):
  1. Fetched records are stored locally with enough metadata to understand origin and format.
  2. Reusing a cached record does not require another NCBI request.
  3. A user can inspect cache contents from the CLI before fetching again.
**Plans**: 2 plans

Plans:
- [x] 03-01: Implement cache storage and metadata model
- [x] 03-02: Add cache inspection and cache-aware retrieval behavior

### Phase 4: Sequence Analysis Core
**Goal**: A user can analyze local or cached sequences without leaving the toolkit.
**Depends on**: Phase 3
**Requirements**: [ANLY-01, ANLY-02, ANLY-03, ANLY-04, ANLY-05]
**Success Criteria** (what must be TRUE):
  1. The toolkit can read local FASTA input and cached records through a shared analysis path.
  2. The analysis output includes molecule-aware basic metrics and nucleotide-specific review features.
  3. Analysis results can be exported to JSON for downstream use.
**Plans**: 3 plans

Plans:
- [x] 04-01: Implement parser and molecule detection layer
- [x] 04-02: Implement core analysis metrics, motifs, and ORF review
- [x] 04-03: Implement JSON export and analysis command integration

### Phase 5: Terminal UX And Release Hardening
**Goal**: The CLI feels polished, reliable, and ready for repeated use on Linux terminals and servers.
**Depends on**: Phase 4
**Requirements**: [TERM-02, TERM-03]
**Success Criteria** (what must be TRUE):
  1. Command output is clear, attractive, and consistent across supported commands.
  2. The tool supports plain output or reduced-color usage when terminal support is limited.
  3. Release docs and command ergonomics are good enough for repeat use without re-learning the project.
**Plans**: 2 plans

Plans:
- [x] 05-01: Polish terminal rendering, errors, and plain-output behavior
- [x] 05-02: Tighten user docs, examples, and release checks

### Phase 6: Guided Search And Interactive Selection
**Goal**: A user can stay inside the terminal after searching, move through results interactively, and choose the next action without copying accessions manually.
**Depends on**: Phase 5
**Requirements**: [GUIDE-01, GUIDE-02, TERM-02]
**Success Criteria** (what must be TRUE):
  1. A TTY user can navigate search results with the keyboard and select one item.
  2. After selection, the user can choose a follow-up action without leaving the search flow.
  3. The guided flow still respects the existing cache-aware fetch and shared analysis path.
**Plans**: 2 plans

Plans:
- [x] 06-01: Add terminal picker abstraction and interactive search-result selection
- [x] 06-02: Wire selected-result actions into fetch/analyze flow and document the UX

### Phase 7: Batch Workflow Foundations
**Goal**: A user can process many accessions or local files in one command while preserving readable terminal feedback and machine-friendly outputs.
**Depends on**: Phase 6
**Requirements**: [BATCH-01, BATCH-02, BATCH-03]
**Success Criteria** (what must be TRUE):
  1. The toolkit can read a list of accessions or paths from a file and execute the requested operation across them.
  2. Per-item failures do not destroy the whole batch unless explicitly requested.
  3. The output includes a clear summary of successes, failures, and saved artifacts.
**Plans**: 2 plans

Plans:
- [x] 07-01: Implement batch command inputs, validation, and operation modes
- [x] 07-02: Implement batch summaries, structured result export, and failure handling

### Phase 8: Compare And Transform Commands
**Goal**: The toolkit can compare records side by side and perform practical sequence transformations without leaving the CLI.
**Depends on**: Phase 7
**Requirements**: [COMPARE-01, COMPARE-02, XFORM-01, XFORM-02]
**Success Criteria** (what must be TRUE):
  1. A user can compare at least two local or cached records through one shared reporting flow.
  2. The comparison highlights meaningful differences instead of dumping raw analysis objects.
  3. Common transforms can be run from the terminal and saved cleanly.
**Plans**: 2 plans

Plans:
- [x] 08-01: Implement multi-record comparison command and report rendering
- [x] 08-02: Implement transform command family for practical sequence utilities

### Phase 9: Annotation And Richer Exports
**Goal**: The toolkit exposes record-level annotations and can emit reports in formats beyond JSON.
**Depends on**: Phase 8
**Requirements**: [ANN-01, ANN-02, EXPORT-01, EXPORT-02]
**Success Criteria** (what must be TRUE):
  1. Annotation views expose useful metadata and features from GenBank or NCBI-backed records.
  2. Export modes support common downstream uses such as tabular summaries and shareable reports.
  3. Export behavior stays consistent with the Linux-first terminal workflow.
**Plans**: 2 plans

Plans:
- [x] 09-01: Implement annotation extraction and CLI presentation
- [x] 09-02: Add CSV, Markdown, and HTML report exporters

### Phase 10: BLAST Integration
**Goal**: The toolkit can initiate BLAST workflows without abandoning the CLI-first research flow.
**Depends on**: Phase 9
**Requirements**: [BLAST-01, BLAST-02]
**Success Criteria** (what must be TRUE):
  1. A user can launch a remote BLAST search from a query sequence or accession-derived record.
  2. BLAST results are summarized clearly in terminal and can be exported for later work.
  3. The codebase leaves a clean integration path for local BLAST+ on servers.
**Plans**: 2 plans

Plans:
- [x] 10-01: Implement remote BLAST submission, polling, and summarized result rendering
- [x] 10-02: Define local BLAST+ integration contract and compatible output handling

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation And CLI Contract | 2/2 | Complete | 2026-04-19 |
| 2. NCBI Search And Fetch | 2/2 | Complete | 2026-04-19 |
| 3. Local Cache And Record Management | 2/2 | Complete | 2026-04-19 |
| 4. Sequence Analysis Core | 3/3 | Complete | 2026-04-19 |
| 5. Terminal UX And Release Hardening | 2/2 | Complete | 2026-04-19 |
| 6. Guided Search And Interactive Selection | 2/2 | Complete | 2026-04-19 |
| 7. Batch Workflow Foundations | 2/2 | Complete | 2026-04-19 |
| 8. Compare And Transform Commands | 2/2 | Complete | 2026-04-20 |
| 9. Annotation And Richer Exports | 2/2 | Complete | 2026-04-20 |
| 10. BLAST Integration | 2/2 | Complete | 2026-04-20 |

## Future Direction

These items are intentionally not part of the active milestone, but the design should keep them easy to add later:

- Snakemake integration and reproducible pipeline wrappers
- FASTQ quality-oriented workflows
- compact text-only mode if real server/log usage demands it
- broader dataset and format support beyond the current core sequence focus
