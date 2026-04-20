# Bio Toolkit

Bio Toolkit is a Linux-first command line toolkit for finding, fetching, caching, and analyzing biological sequences from NCBI and local files.

It is intentionally small, but it is built like a real software project: package metadata, environment configuration, tests, documentation, modular source code, and a clear CLI workflow.

## Status

The v1 core workflow and the first expansion milestone are complete and usable.

Today the toolkit can:

- search NCBI `nucleotide` and `protein` databases from the terminal
- filter searches by organism
- preview search results in readable terminal tables
- interactively move through search results in a TTY and choose what to do next with `--pick`
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
- export analysis reports as JSON
- export annotation reports as JSON, CSV, Markdown, or HTML
- export BLAST results as JSON, CSV, or TSV
- run in normal styled terminal mode or reduced-color mode with `--plain`

## What The Toolkit Can Do

### `doctor`

Validates local runtime configuration:

- `.env` presence
- `NCBI_EMAIL`
- `NCBI_API_KEY`
- cache and output directories
- detected platform and Python version
- color mode

Examples:

```bash
./bio-toolkit doctor
./bio-toolkit doctor --create-dirs
./bio-toolkit --plain doctor
```

### `search`

Searches NCBI from the terminal.

Current capabilities:

- `nucleotide` or `protein` databases
- free-text queries
- optional organism filter
- adjustable result limit
- terminal table output
- JSON output
- interactive picker mode in TTY-capable terminals
- direct follow-up actions after selection: print accession, fetch, or fetch and analyze

Examples:

```bash
./bio-toolkit search "SpoIIIAA" --database protein
./bio-toolkit search "SpoIIIAA" --database protein --organism "Bacillus subtilis"
./bio-toolkit search "SpoIIIAA" --database protein --organism "Bacillus subtilis" --pick
./bio-toolkit search "BRCA1" --database nucleotide --limit 5
./bio-toolkit search "TP53" --database protein --json
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
- compute protein metrics such as molecular weight and pI for protein sequences
- scan motifs for nucleotide sequences
- scan ORFs in six frames for nucleotide sequences
- render structured terminal reports
- export JSON reports

Examples:

```bash
./bio-toolkit analyze outputs/NG_005905.fasta
./bio-toolkit analyze NG_005905 --source cache --database nucleotide --rettype fasta
./bio-toolkit analyze NG_005905 --source cache --database nucleotide --rettype fasta --json
./bio-toolkit analyze outputs/NG_005905.fasta --output outputs/NG_005905.analysis.json
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
- export a JSON batch report

Examples:

```bash
./bio-toolkit batch inputs/accessions.txt --mode analyze --input-kind accessions --database protein --rettype fasta
./bio-toolkit batch inputs/files.txt --mode analyze --input-kind files
./bio-toolkit batch inputs/accessions.txt --mode fetch --input-kind accessions --database nucleotide
./bio-toolkit batch inputs/files.txt --mode analyze --input-kind files --output outputs/batch.analysis.json
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

### Local Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade
pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
```

### Easiest Way To Run It

From the repository root:

```bash
./bio-toolkit
```

If you prefer not to type `./`, activate the environment once:

```bash
source .venv/bin/activate
bio-toolkit search "SpoIIIAA" --database protein
```

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
- if a path in `.env` is relative, it is resolved from the repository root
- `--plain` reduces color-rich output for constrained terminals or log-oriented sessions

## Command Summary

| Command | Purpose | JSON Support | Notes |
|---------|---------|--------------|-------|
| `doctor` | inspect runtime configuration | no | can create runtime directories |
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

- server-oriented local BLAST+ integration on Linux hosts that need it later
- Snakemake-facing integration after the CLI workflow milestone is stable
- compact text-only output mode only if server/log workflows demand it

Planning artifacts live in `.planning/`.

For a feature-by-feature inventory, see [FUNCTIONALITIES.md](/home/yoel/bioinformatics/bio_toolkit/docs/FUNCTIONALITIES.md).
