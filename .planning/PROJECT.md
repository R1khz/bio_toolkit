# Bio Toolkit

## What This Is

Bio Toolkit is a Linux-first command line toolkit for finding, caching, reviewing, and analyzing biological sequences from NCBI and local files.

It is intentionally small enough to become useful quickly, but structured like a serious software project so it can keep growing into a reusable tool for coursework, research practice, and server-side bioinformatics work.

The first release focuses on the daily pain point the user described: finding sequences once, keeping them locally, and running basic review and analysis from the terminal without repeating manual search work.

## Core Value

Find a sequence once, keep it locally, and analyze it from a Linux terminal without repeated manual lookup.

## Requirements

### Validated

- Search NCBI from the terminal by gene, organism, accession, or free text
- Preview search results in a readable terminal table before downloading anything
- Fetch sequence records and metadata from NCBI into a reusable local cache
- Analyze cached or local sequences with core statistics, motifs, and ORF review
- Keep the CLI clean, aesthetic, and reliable in Linux terminals and remote servers
- Export machine-readable results for later notebooks or reproducible pipelines
- Add guided terminal selection after search so the user can keep moving without copying accessions manually
- Add batch processing for repeated accession and file workflows
- Add comparison commands for practical day-to-day sequence work
- Add transform commands for practical day-to-day sequence work
- Add annotation views and richer export formats

### Active

- [ ] Prepare the repository for first public release and GitHub publishing

### Out of Scope

- Web UI or desktop app in v1 - the immediate use case is terminal work on Linux and servers
- Large workflow orchestration, assembly, or alignment-heavy pipelines in v1 - too broad for the first useful release
- Shared multi-user service or web API in v1 - the first target is a local single-user research tool
- Deep visualization dashboards in v1 - readable terminal UX matters more than graphical interfaces right now

## Context

The project lives in `/home/yoel/bioinformatics/bio_toolkit` and starts from a clean repository. The user wants this to be a real software project even if it stays small: planning artifacts, environment configuration, repo hygiene, modular code layout, and a documented development flow all matter from the beginning.

The main practical problem to solve is sequence retrieval friction. If the work will involve frequent sequence review, it is inefficient to search NCBI manually every time. That makes NCBI integration and local caching core to the product, not optional add-ons.

Because future usage will include Linux servers, the project must behave well in a shell-only environment. The UX should still feel polished: clean help text, readable tables, status feedback, consistent errors, and optional colorized output when the terminal supports it.

The educational value also matters. This project should develop useful skills for a bioinformatics masters path: API integration, sequence parsing, Linux CLI engineering, reproducibility, testing, packaging, and incremental delivery.

## Constraints

- **Platform**: Linux terminal first - the tool must run well in standard shells and remote servers without GUI assumptions
- **Data source**: NCBI APIs must be used politely - the tool should support `email` and optional API key configuration
- **Scope**: The project should stay small enough to ship quickly - useful core workflows matter more than broad feature coverage
- **Architecture**: Code must be modular and package-structured - avoid a one-file prototype that becomes hard to maintain
- **Output**: Results must work for both humans and follow-up tools - terminal output and machine-readable exports are both needed
- **Quality**: Documentation, environment setup, linting, and tests are part of the project from the start, not cleanup work for later

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build a CLI-first tool instead of a web app | The main use case is Linux and remote server work | -- Pending |
| Make NCBI search and fetch a core product capability | The project should remove repeated manual lookup work | -- Pending |
| Use a local cache as a first-class feature | Reuse matters as much as retrieval for daily sequence review | -- Pending |
| Use Python with a `src/` package layout | Python fits the domain and supports a maintainable project structure | -- Pending |
| Use `Typer` and `Rich` for the command interface | The CLI should be both practical and aesthetically readable in terminal sessions | -- Pending |
| Keep the first release focused on search, fetch, cache, and core analysis | Early usefulness matters more than broad v1 scope | Validated |
| After v1, expand workflow depth before pipeline orchestration | Guided terminal flow, batch work, comparison, and BLAST have higher immediate value than Snakemake | Active |
| Keep BLAST remote-first in the CLI | Fits laptop workflows now and leaves local BLAST+ for server-specific expansion later | Validated |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check -> still the right priority?
3. Audit Out of Scope -> reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-20 after remote BLAST implementation and release-readiness updates*
