# Bio Toolkit

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/R1khz/bio_toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/R1khz/bio_toolkit/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/R1khz/bio_toolkit/releases)
[![Coverage](https://img.shields.io/badge/coverage-72%25-yellow.svg)](https://github.com/R1khz/bio_toolkit)

Bio Toolkit is a Linux-first command line toolkit for finding, fetching, caching, and analyzing biological sequences from NCBI, UniProt, KEGG, and local files.

It is intentionally small, but it is built like a real software project: package metadata, environment configuration, tests, documentation, modular source code, and a clear CLI workflow.

## Demo

<!-- Record with: vhs demo.tape (https://github.com/charmbracelet/vhs) -->
<!-- Suggested flow: search → fetch → analyze -->

## Status

The v1 core workflow and the first expansion milestone are complete and usable.

Today the toolkit can:

- run a guided `start` flow that asks what to search and what to do next
- query provider APIs directly for deeper metadata and cross-references
- search NCBI `nucleotide` and `protein` databases from the terminal
- search UniProt for protein records
- search KEGG for genes, pathways, KO terms, enzymes, or diseases
- filter searches by organism
- preview search results in readable terminal tables
- interactively move through search results in a TTY and choose what to do next with `--pick`
- choose provider-aware quick actions such as annotate, BLAST, or AlphaFold lookup
- fetch records by accession in `fasta` or `genbank`
- save fetched records to local files
- store fetched records in a reusable local cache with metadata
- reuse cached records without hitting NCBI again
- inspect cached records from the CLI
- run batch fetch or batch analysis from accession lists or file lists
- analyze local files or cached sequence records
- annotate local or cached records and inspect metadata/features
- compare two or more local files or cached records side by side
- transform local or cached records with reverse-complement, translate, or subseq
- submit remote BLAST searches from local or cached queries
- detect DNA, RNA, protein, or unknown sequence types
- compute core sequence statistics
- review restriction sites, Kozak motifs, and CpG counts for nucleotide sequences
- scan ORFs across six reading frames for nucleotide sequences
- surface heuristic protein domain hits
- enrich protein analyses with UniProt domains and AlphaFold metadata when a UniProt accession is available
- export analysis reports as JSON
- export annotation reports as JSON, CSV, Markdown, or HTML
- export BLAST results as JSON, CSV, or TSV
- run in normal styled terminal mode or reduced-color mode with `--plain`

## What The Toolkit Can Do

### `doctor`

Validates local runtime configuration:

- `.env` presence
- runtime root detection
- `NCBI_EMAIL`
- `NCBI_API_KEY`
- cache and output directories
- package import path and install mode
- detected platform and Python version
- color mode

Examples:

```bash
./bio-toolkit doctor
./bio-toolkit doctor --create-dirs
./bio-toolkit --plain doctor
```

### `start`

Runs a guided search or API-query flow.

Current capabilities:

- choose between record search and direct API query
- ask what to search
- ask where to search: `auto`, `ncbi`, `uniprot`, `kegg`, or `alphafold` when querying APIs
- auto-detect literal DNA, RNA, or protein sequences and analyze them directly
- show results in a picker and launch a provider-aware follow-up action
- render direct provider metadata reports without leaving the guided flow

Examples:

```bash
./bio-toolkit start
./bio-toolkit --plain start
```

### `search`

Searches NCBI, UniProt, or KEGG from the terminal.

Current capabilities:

- provider selection with `--provider ncbi|uniprot|kegg|auto`
- `nucleotide` or `protein` databases for NCBI
- `genes`, `pathway`, `ko`, `enzyme`, or `disease` databases for KEGG
- free-text queries
- optional organism filter
- adjustable result limit
- terminal table output
- JSON output
- interactive picker mode in TTY-capable terminals
- direct follow-up actions after selection: print accession, fetch, analyze, query API details, annotate, BLAST, AlphaFold lookup, or fetch and analyze depending on provider

Examples:

```bash
./bio-toolkit search "SpoIIIAA" --database protein
./bio-toolkit search "P69905" --provider uniprot
./bio-toolkit search "hsa:10458" --provider auto
./bio-toolkit search "SpoIIIAA" --database protein --organism "Bacillus subtilis"
./bio-toolkit search "SpoIIIAA" --database protein --organism "Bacillus subtilis" --pick
./bio-toolkit search "BRCA1" --database nucleotide --limit 5
./bio-toolkit search "TP53" --database protein --json
```

### `query`

Queries provider APIs directly for deeper metadata.

Current capabilities:

- query `ncbi`, `uniprot`, `kegg`, `alphafold`, or `auto`
- resolve direct accessions and identifiers into richer provider entry summaries
- inspect UniProt functions, domains, keywords, and cross-references
- inspect KEGG pathways, diseases, orthology, DB links, and sequence previews
- preview exact NCBI matches with `efetch`
- include AlphaFold metadata directly or as UniProt enrichment
- emit terminal summaries or JSON

Examples:

```bash
./bio-toolkit query P69905 --provider uniprot
./bio-toolkit query P69905 --provider alphafold
./bio-toolkit query hsa:10458 --provider kegg
./bio-toolkit query BRCA1 --provider ncbi --database nucleotide --organism "Homo sapiens"
./bio-toolkit query P69905 --provider auto --json
```

### `fetch`

Fetches a specific accession from NCBI.

Current capabilities:

- fetch by accession or accession.version
- choose `nucleotide` or `protein`
- choose `fasta` or `gb`/`genbank`
- reuse cache automatically
- force remote refresh with `--refresh`
- save to file
- print to stdout
- preview fetched content in terminal

Examples:

```bash
./bio-toolkit fetch NM_007294.4
./bio-toolkit fetch NP_000537.3 --database protein --rettype fasta --stdout
./bio-toolkit fetch NM_007294.4 --rettype gb --output outputs/brca1.gb
./bio-toolkit fetch NG_005905 --refresh
```

### `cache`

Inspects locally cached records.

Current capabilities:

- list cached records
- filter by database
- filter by rettype
- inspect a specific cached accession
- preview cached content
- emit JSON

Examples:

```bash
./bio-toolkit cache
./bio-toolkit cache --database nucleotide
./bio-toolkit cache NG_005905 --database nucleotide --rettype fasta
./bio-toolkit cache --json
```

### `analyze`

Analyzes either a local file or a cached record.

Current capabilities:

- analyze local FASTA files
- analyze local GenBank files
- analyze cached FASTA or GenBank records
- auto-detect input format when possible
- detect sequence type
- compute length and composition metrics
- compute GC and AT content for nucleotide sequences
- surface warnings for short, ambiguous, or otherwise suspicious sequences
- compute protein metrics such as molecular weight and pI for protein sequences
- show protein domain summaries for protein inputs
- enrich protein reports with UniProt domains and AlphaFold metadata when the input resolves to a UniProt accession
- scan motifs for nucleotide sequences
- scan ORFs in six frames for nucleotide sequences
- show the longest ORF translation and its top codons for nucleotide sequences
- search custom motifs with repeatable `--motif` flags
- render structured terminal reports
- export analysis reports as JSON or CSV

Examples:

```bash
./bio-toolkit analyze outputs/NG_005905.fasta
./bio-toolkit analyze NG_005905 --source cache --database nucleotide --rettype fasta
./bio-toolkit analyze NG_005905 --source cache --database nucleotide --rettype fasta --json
./bio-toolkit analyze outputs/NG_005905.fasta --motif GAATTC --motif 're:GCCACCATG'
./bio-toolkit analyze outputs/NG_005905.fasta --output outputs/NG_005905.analysis.json
./bio-toolkit analyze outputs/NG_005905.fasta --output outputs/NG_005905.analysis.csv --export-format csv
./bio-toolkit --plain analyze outputs/NG_005905.fasta
```

### `annotate`

Inspects higher-level metadata and selected features from local or cached records.

Current capabilities:

- annotate local GenBank files
- annotate cached GenBank records
- annotate FASTA inputs with reduced metadata depth
- extract organism, topology, date, genes, products, and feature counts
- show selected feature summaries in terminal
- export annotation reports as `json`, `csv`, `markdown`, or `html`

Examples:

```bash
./bio-toolkit annotate sample.gb
./bio-toolkit annotate NG_005905 --source cache --database nucleotide --rettype gb
./bio-toolkit annotate sample.gb --output outputs/sample.annotations.md --export-format markdown
./bio-toolkit annotate sample.gb --output outputs/sample.annotations.html --export-format html
```

### `compare`

Compares two or more local files or cached records through the shared analysis path.

Current capabilities:

- compare local FASTA or GenBank files
- compare cached records by accession
- detect mixed molecule types
- render side-by-side terminal summaries
- highlight metric ranges and deltas
- export a JSON comparison report

Examples:

```bash
./bio-toolkit compare sample_a.fasta sample_b.fasta
./bio-toolkit compare NG_005905 NC_139040 --source cache --database nucleotide --rettype fasta
./bio-toolkit compare sample_a.fasta sample_b.fasta --output outputs/compare.json
```

### `transform`

Transforms a local file or cached record and emits reusable FASTA output.

Current capabilities:

- reverse complement for DNA or RNA inputs
- translation for nucleotide inputs with frame selection
- subsequence extraction with 1-based inclusive coordinates
- save transformed output to a FASTA file
- print transformed FASTA with `--stdout`

Examples:

```bash
./bio-toolkit transform sample.fasta --operation reverse-complement
./bio-toolkit transform sample.fasta --operation translate --frame 2
./bio-toolkit transform sample.fasta --operation subseq --start 10 --end 150
./bio-toolkit transform YDX66035 --source cache --database protein --rettype fasta --operation subseq --start 1 --end 60
```

### `blast`

Runs remote BLAST searches from a local file or cached record without leaving the toolkit.

Current capabilities:

- remote-only BLAST workflow through NCBI
- query loading from local FASTA/GenBank or cache
- automatic program defaults based on query type
- terminal spinner and countdown while waiting for NCBI
- clear terminal hit summary when the job finishes
- JSON, CSV, or TSV export
- Linux-safe default polling interval aligned with NCBI guidance

Examples:

```bash
./bio-toolkit blast examples/hemoglobin_beta.fasta
./bio-toolkit blast examples/hemoglobin_beta.fasta --output outputs/hemoglobin_beta.blast.csv --export-format csv
./bio-toolkit blast YDX66035 --source cache --cache-database protein --cache-rettype fasta
./bio-toolkit blast examples/hemoglobin_beta.fasta --program blastp --blast-database swissprot --json
```

### `batch`

Runs repeated fetch or analysis work from a newline-delimited list.

Current capabilities:

- analyze batches of local sequence files
- analyze batches of accession inputs
- fetch batches of accession inputs
- continue through per-item failures unless `--fail-fast` is enabled
- render a readable terminal summary table
- export batch reports as JSON or CSV

Examples:

```bash
./bio-toolkit batch inputs/accessions.txt --mode analyze --input-kind accessions --database protein --rettype fasta
./bio-toolkit batch inputs/files.txt --mode analyze --input-kind files
./bio-toolkit batch inputs/accessions.txt --mode fetch --input-kind accessions --database nucleotide
./bio-toolkit batch inputs/files.txt --mode analyze --input-kind files --output outputs/batch.analysis.json
./bio-toolkit batch inputs/files.txt --mode analyze --input-kind files --output outputs/batch.analysis.csv --export-format csv
```

## Typical Workflows

### Search Then Fetch Then Analyze

```bash
./bio-toolkit search "SpoIIIAA" --database protein --organism "Bacillus subtilis"
./bio-toolkit fetch <ACCESSION> --database protein
./bio-toolkit analyze <ACCESSION> --source cache --database protein --rettype fasta
```

### Search Interactively And Decide In Terminal

```bash
./bio-toolkit search "SpoIIIAA" --database protein --organism "Bacillus subtilis" --pick
```

In picker mode you can:

- move through results with arrow keys
- choose one record
- print the accession
- fetch it immediately
- fetch it and run `analyze` right away

### Analyze A Local File

```bash
./bio-toolkit analyze path/to/sequence.fasta
./bio-toolkit analyze path/to/sequence.gb
```

### Export A JSON Report

```bash
./bio-toolkit analyze NG_005905 --source cache --database nucleotide --rettype fasta --output outputs/NG_005905.analysis.json
```

### Export Annotation Reports

```bash
./bio-toolkit annotate sample.gb --output outputs/sample.annotations.csv --export-format csv
./bio-toolkit annotate sample.gb --output outputs/sample.annotations.md --export-format markdown
./bio-toolkit annotate sample.gb --output outputs/sample.annotations.html --export-format html
```

### Compare Two Records

```bash
./bio-toolkit compare sample_a.fasta sample_b.fasta
./bio-toolkit compare YDX66035 WP_480030509 --source cache --database protein --rettype fasta
```

### Transform A Record

```bash
./bio-toolkit transform sample.fasta --operation reverse-complement
./bio-toolkit transform sample.fasta --operation translate --frame 1 --to-stop --stdout
./bio-toolkit transform sample.fasta --operation subseq --start 25 --end 120
```

### Run A Remote BLAST Search

```bash
./bio-toolkit blast examples/hemoglobin_beta.fasta
./bio-toolkit blast examples/hemoglobin_beta.fasta --output outputs/hemoglobin_beta.blast.csv --export-format csv
```

### Run A Batch From A List

```bash
./bio-toolkit batch inputs/accessions.txt --mode analyze --input-kind accessions --database protein --rettype fasta
./bio-toolkit batch inputs/files.txt --mode analyze --input-kind files
```

## Installation

### Install as a Tool (pipx)

If you just want to use the toolkit without modifying it:

```bash
pipx install git+https://github.com/R1khz/bio_toolkit.git
```

Then run it from anywhere:

```bash
btk --help
bio-toolkit --help  # long form, same thing
```

### Shell Tab Completion

After installing, enable tab completion for your shell once:

```bash
# bash
btk --install-completion bash

# zsh
btk --install-completion zsh

# fish
btk --install-completion fish
```

Restart your shell (or `source ~/.bashrc`), then press Tab on any accession argument to see your cached sequences:

```bash
btk analyze <TAB>          # shows cached accessions
btk compare <TAB>          # shows cached accessions
btk blast <TAB>            # shows cached accessions
btk annotate <TAB>         # shows cached accessions
btk transform <TAB>        # shows cached accessions
```

Completion reads directly from your local cache — no network calls, no configuration needed.

---

### Local Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
python -m bio_toolkit doctor
```

### Easiest Way To Run It

From the repository root:

```bash
./bio-toolkit
```

`./bio-toolkit` now verifies that the installed package resolves to this clone. If you move or copy the repository, rerun:

```bash
./.venv/bin/python -m pip install -e ".[dev]"
```

If you prefer not to type `./`, activate the environment once and use the installed entrypoints directly:

```bash
source .venv/bin/activate
python -m bio_toolkit doctor
btk search "SpoIIIAA" --database protein
```

`btk` is the short alias — it maps to the same CLI as `bio-toolkit`.

## Configuration

The toolkit reads configuration from `.env` or your shell environment.

Important variables:

- `NCBI_EMAIL`: required for polite NCBI usage
- `NCBI_API_KEY`: optional but recommended
- `NCBI_TOOL_NAME`: tool label sent to NCBI
- `BIO_TOOLKIT_CACHE_DIR`: optional cache directory
- `BIO_TOOLKIT_OUTPUT_DIR`: optional output directory
- `BIO_TOOLKIT_COLOR`: enable or disable styled output

Notes:

- if `BIO_TOOLKIT_CACHE_DIR` is unset, the default cache path is used
- if a path in `.env` is relative, it is resolved from the runtime root
- the runtime root is the active repository root when you are inside a clone, otherwise the current working directory
- `doctor` warns when the active repository and imported package point to different clones
- `--plain` reduces color-rich output for constrained terminals or log-oriented sessions

## Command Summary

| Command | Purpose | JSON Support | Notes |
|---------|---------|--------------|-------|
| `doctor` | inspect runtime configuration | no | can create runtime directories and detect install mismatches |
| `search` | search NCBI | yes | supports `nucleotide`, `protein`, and TTY picker mode |
| `fetch` | fetch accession from NCBI | no | uses cache automatically unless `--refresh` |
| `annotate` | inspect metadata and selected features | yes | supports JSON stdout and file export to JSON/CSV/Markdown/HTML |
| `compare` | compare multiple local or cached records | yes | highlights ranges and deltas across compared records |
| `transform` | transform local or cached records | no | emits reusable FASTA output |
| `blast` | run remote BLAST from local or cached queries | yes | remote-first, with terminal waiting feedback and JSON/CSV/TSV export |
| `batch` | process repeated fetch/analyze work from a list | yes | supports accession lists and local file lists |
| `cache` | inspect cache contents | yes | can list or inspect one accession |
| `analyze` | analyze local or cached sequences | yes | supports terminal report and JSON export |

## Terminal UX

The CLI is intentionally designed to look good in terminal without becoming fragile.

Current UX properties:

- Linux shell compatible
- works well in remote server sessions
- Rich tables and panels by default
- interactive cursor-based selection for TTY sessions
- readable summaries before detailed output
- reduced-color mode with `--plain`
- consistent command help
- machine-readable JSON where it matters

## Project Layout

```text
bio_toolkit/
├── .planning/
├── docs/
├── examples/
├── src/bio_toolkit/
├── tests/
├── .env.example
├── .gitignore
├── Makefile
├── pyproject.toml
├── README.md
└── bio-toolkit
```

## Quality And Verification

The project includes:

- `pytest`
- `unittest` coverage for core modules
- modular Python package layout under `src/`
- documented runtime configuration
- CLI launcher script for local use

Useful commands:

```bash
make lint
make test
./bio-toolkit --help
```

## Current Scope Boundaries

Included today:

- NCBI search
- interactive TTY-guided search selection
- accession fetch
- batch fetch and batch analysis
- local cache reuse
- local and cached sequence analysis
- record annotation
- multi-record comparison
- sequence transforms
- remote BLAST from local or cached queries
- JSON export
- flat CSV export for analysis and batch summaries
- CSV, Markdown, and HTML annotation export
- JSON, CSV, and TSV BLAST export
- polished terminal output

Not included yet:

- FASTQ quality workflows
- Snakemake integration
- web UI
- heavy alignment or assembly pipelines

## Next Logical Expansions

Good next steps after this milestone:

- MySQL-backed run persistence built on the current analysis and batch report schemas
- a small API surface on top of the existing analysis core once persistence needs settle
- Snakemake-facing integration after the CLI workflow milestone is stable
- compact text-only output mode only if server/log workflows demand it

Planning artifacts live in `.planning/`.

For a feature-by-feature inventory, see [FUNCTIONALITIES.md](/home/yoel/bioinformatics/bio_toolkit/docs/FUNCTIONALITIES.md).
