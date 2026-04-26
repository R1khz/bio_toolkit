# CLI Contract

## Internal Boundary

The CLI remains the user-facing entrypoint, but implementation is now split internally:

- `cli.commands` parses flags and builds typed service requests
- `services` performs the actual work
- `cli.presenters` renders terminal output

This keeps command behavior stable while making the core reusable outside the terminal later.

## Current Commands

### `python -m bio_toolkit`

Shows a short project overview and the planned command surface.

Recommended local launcher from the repo root:

```bash
./bio-toolkit
```

### `python -m bio_toolkit start`

Run a guided flow for provider selection, result picking, and quick follow-up actions.

Examples:

```bash
./bio-toolkit start
./bio-toolkit --plain start
```

Current behavior:

- asks whether you want record search or direct API query
- asks what to search and where to search
- supports `auto`, `ncbi`, `uniprot`, `kegg`, and `alphafold` for API-query mode
- detects literal DNA, RNA, or protein sequences and analyzes them directly
- opens the same interactive action picker used by `search --pick`

### `python -m bio_toolkit doctor`

Prints runtime diagnostics for:

- `.env` presence
- runtime root detection
- NCBI email and API key configuration
- runtime cache and output directories
- package import path, install mode, and active repo match
- platform and Python version
- color mode

Useful variants:

```bash
./bio-toolkit doctor
./bio-toolkit doctor --create-dirs
./bio-toolkit --plain doctor
```

If `doctor` reports an active-repo mismatch, reinstall the current clone with:

```bash
./.venv/bin/python -m pip install -e ".[dev]"
```

### `python -m bio_toolkit search`

Search NCBI, UniProt, or KEGG with terminal-friendly results.

Examples:

```bash
./bio-toolkit search "insulin" --database protein --organism "Homo sapiens"
./bio-toolkit search "P69905" --provider uniprot
./bio-toolkit search "hsa:10458" --provider auto
./bio-toolkit search "BRCA1" --database nucleotide --limit 5
./bio-toolkit search "SpoIIIAA" --database protein --organism "Bacillus subtilis" --pick
./bio-toolkit search "TP53" --json
```

TTY picker mode:

- requires a TTY-capable terminal session
- lets the user move through search results with arrow keys
- supports direct follow-up actions after selection
- current actions depend on provider and include: print accession, fetch, analyze, query API details, annotate, BLAST, AlphaFold lookup, and fetch then analyze

### `python -m bio_toolkit query`

Query provider APIs directly for structured metadata.

Examples:

```bash
./bio-toolkit query P69905 --provider uniprot
./bio-toolkit query P69905 --provider alphafold
./bio-toolkit query hsa:10458 --provider kegg
./bio-toolkit query BRCA1 --provider ncbi --database nucleotide --organism "Homo sapiens"
./bio-toolkit query P69905 --provider auto --json
```

Current behavior:

- supports `auto`, `ncbi`, `uniprot`, `kegg`, and `alphafold`
- uses search-style summaries when the query is broad text
- resolves direct identifiers into richer provider entry reports when possible
- enriches UniProt entry reports with AlphaFold metadata when available
- prints Rich tables/panels or emits JSON to stdout

### `python -m bio_toolkit fetch`

Retrieve a selected accession and save it to a local file. By default, the command now also reuses and updates the local cache.

Examples:

```bash
./bio-toolkit fetch NM_007294.4
./bio-toolkit fetch NP_000537.3 --database protein --rettype fasta --stdout
./bio-toolkit fetch NM_007294.4 --output outputs/brca1.gb --rettype gb
./bio-toolkit fetch NM_007294.4 --refresh
```

### `python -m bio_toolkit batch`

Run repeated fetch or analysis work from a newline-delimited list of accessions or file paths.

Examples:

```bash
./bio-toolkit batch inputs/accessions.txt --mode analyze --input-kind accessions --database protein --rettype fasta
./bio-toolkit batch inputs/files.txt --mode analyze --input-kind files
./bio-toolkit batch inputs/accessions.txt --mode fetch --input-kind accessions --database nucleotide
./bio-toolkit batch inputs/files.txt --mode analyze --input-kind files --output outputs/batch.json
./bio-toolkit batch inputs/files.txt --mode analyze --input-kind files --output outputs/batch.csv --export-format csv
```

Current behavior:

- accepts list files with blank lines and `#` comments ignored
- supports `analyze` and `fetch`
- supports `auto`, `accessions`, and `files` input modes
- continues on per-item failures unless `--fail-fast` is enabled
- prints a Rich summary table and can export JSON or CSV

### `python -m bio_toolkit annotate`

Inspect higher-level metadata and selected features from local or cached records.

Examples:

```bash
./bio-toolkit annotate sample.gb
./bio-toolkit annotate NG_005905 --source cache --database nucleotide --rettype gb
./bio-toolkit annotate sample.gb --output outputs/sample.annotations.csv --export-format csv
./bio-toolkit annotate sample.gb --output outputs/sample.annotations.md --export-format markdown
./bio-toolkit annotate sample.gb --output outputs/sample.annotations.html --export-format html
```

Current behavior:

- works best with GenBank inputs or cached `gb` records
- still accepts FASTA input, but metadata depth is naturally limited
- extracts organism, topology, date, genes, products, and feature counts
- shows selected feature summaries in terminal
- supports JSON to stdout and JSON/CSV/Markdown/HTML exports to files

### `python -m bio_toolkit compare`

Compare two or more local files or cached records and surface practical differences in terminal.

Examples:

```bash
./bio-toolkit compare sample_a.fasta sample_b.fasta
./bio-toolkit compare YDX66035 WP_480030509 --source cache --database protein --rettype fasta
./bio-toolkit compare sample_a.fasta sample_b.fasta --output outputs/compare.json
```

Current behavior:

- reuses the same loading and analysis path as `analyze`
- supports local files and cached accessions
- works with nucleotide, protein, or mixed comparisons
- prints a side-by-side comparison table plus metric highlights
- can emit JSON for downstream processing

### `python -m bio_toolkit transform`

Transform a local file or cached record and emit FASTA output that can be saved or printed.

Examples:

```bash
./bio-toolkit transform sample.fasta --operation reverse-complement
./bio-toolkit transform sample.fasta --operation translate --frame 2
./bio-toolkit transform sample.fasta --operation translate --frame 1 --to-stop --stdout
./bio-toolkit transform sample.fasta --operation subseq --start 10 --end 150
```

Current behavior:

- supports `reverse-complement`, `translate`, and `subseq`
- reuses the same loading path as `analyze`
- writes reusable FASTA output by default
- supports `--stdout` for shell pipelines
- enforces molecule-aware restrictions for invalid operations

### `python -m bio_toolkit blast`

Run a remote BLAST workflow from a local query file or cached record.

Examples:

```bash
./bio-toolkit blast examples/hemoglobin_beta.fasta
./bio-toolkit blast examples/hemoglobin_beta.fasta --output outputs/hemoglobin_beta.blast.csv --export-format csv
./bio-toolkit blast examples/hemoglobin_beta.fasta --program blastp --blast-database swissprot --json
./bio-toolkit blast YDX66035 --source cache --cache-database protein --cache-rettype fasta
```

Current behavior:

- remote-only BLAST through NCBI
- local spinner and countdown while respecting a 60-second default polling interval
- automatic `blastn` or `blastp` defaults based on query type
- terminal summary panel with RID, status, elapsed time, and hit table
- JSON stdout or JSON/CSV/TSV file export

### `python -m bio_toolkit cache`

Inspect local cache contents and avoid repeated downloads.

Examples:

```bash
./bio-toolkit cache
./bio-toolkit cache --database nucleotide
./bio-toolkit cache NM_007294.4 --database nucleotide --rettype fasta
./bio-toolkit cache --json
```

### `python -m bio_toolkit analyze`

Analyze either a local file or a cached record and render a structured terminal report.

Examples:

```bash
./bio-toolkit analyze outputs/NG_005905.fasta
./bio-toolkit analyze NG_005905 --source cache --database nucleotide --rettype fasta
./bio-toolkit analyze NG_005905 --source cache --database nucleotide --rettype fasta --json
./bio-toolkit analyze outputs/NG_005905.fasta --motif GAATTC --motif 're:GCCACCATG'
./bio-toolkit analyze outputs/NG_005905.fasta --output outputs/NG_005905.analysis.json
./bio-toolkit analyze outputs/NG_005905.fasta --output outputs/NG_005905.analysis.csv --export-format csv
```

Current behavior:

- works on local files or cached accessions through the same analysis path
- surfaces warnings for short, ambiguous, or unstable-looking inputs
- reports ambiguous nucleotide content when present
- shows longest-ORF translation and top codons for nucleotide records
- shows protein domain summaries for protein records
- enriches protein reports with UniProt domains and AlphaFold metadata when a UniProt accession is available
- accepts repeatable `--motif` flags for literal motifs or `re:<regex>` patterns
- supports JSON to stdout and JSON/CSV exports to files

## Future Commands

MySQL-backed persistence and a small API surface are the next structural expansion targets once the standalone CLI workflow is stable.

## UX Direction

- Linux shell compatible
- readable on remote servers
- Rich-based output by default
- interactive picker for TTY sessions
- reduced-color mode for limited terminals or logs
- NCBI credentials loaded from `.env` or environment variables
- single analysis path for local files and cached records
