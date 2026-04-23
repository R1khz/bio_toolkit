# Functionalities

This document tracks what Bio Toolkit can do today, what is in progress, and what is intentionally left for later.

## Available Now

### Core Runtime

Available:
- Linux-first CLI launcher with `./bio-toolkit`
- `.env`-driven runtime configuration
- cache and output directory management
- reduced-color mode with `--plain`
- runtime validation with `doctor`
- guided workflow entrypoint with `start`
- install mismatch detection when the active repo and imported package diverge

Examples:
```bash
./bio-toolkit
./bio-toolkit doctor
./bio-toolkit doctor --create-dirs
./bio-toolkit --plain doctor
```

### Search And Retrieval

Available:
- NCBI search against `nucleotide` and `protein`
- UniProt search for protein records
- KEGG search for genes, pathways, KO terms, enzymes, and diseases
- guided `start` flow with provider selection
- direct API query mode for NCBI, UniProt, KEGG, and AlphaFold
- organism filtering and result limits
- Rich terminal tables for search results
- interactive TTY picker with `search --pick` and provider-aware follow-up actions
- fetch by accession in `fasta` or `genbank`
- cache-aware fetch with optional refresh
- local save, stdout preview, and cached record inspection

Examples:
```bash
./bio-toolkit search "SpoIIIAA" --database protein
./bio-toolkit search "SpoIIIAA" --database protein --organism "Bacillus subtilis" --pick
./bio-toolkit fetch YDX66035 --database protein
./bio-toolkit fetch NG_005905 --database nucleotide --rettype gb --output outputs/NG_005905.gb
./bio-toolkit cache
./bio-toolkit cache YDX66035 --database protein --rettype fasta
```

### Provider Query

Available:
- direct metadata queries against NCBI
- direct metadata queries against UniProt
- direct metadata queries against KEGG
- direct AlphaFold model lookup by UniProt accession
- API-query mode inside `start`
- `Query API details` action from the interactive picker

Examples:
```bash
./bio-toolkit query P69905 --provider uniprot
./bio-toolkit query P69905 --provider alphafold
./bio-toolkit query hsa:10458 --provider kegg
./bio-toolkit query BRCA1 --provider ncbi --database nucleotide --organism "Homo sapiens"
```

### Analysis

Available:
- analyze local FASTA files
- analyze local GenBank files
- analyze cached FASTA or GenBank records
- auto-detect molecule type: DNA, RNA, protein, unknown
- nucleotide metrics: length, GC, AT, base composition, CpG counts
- nucleotide quality signals: warnings and ambiguous IUPAC base counts
- protein metrics: length, amino-acid composition, molecular weight, pI, instability, gravy, aromaticity
- heuristic protein domain detection
- UniProt domain and AlphaFold enrichment when a UniProt accession is available
- nucleotide motif review: restriction sites and Kozak matches
- repeatable `--motif` search for literal motifs or `re:<regex>` patterns
- ORF scanning across six reading frames
- longest ORF translation and top codon usage summary
- JSON or CSV export for analysis reports

Examples:
```bash
./bio-toolkit analyze sample.fasta
./bio-toolkit analyze sample.gb
./bio-toolkit analyze YDX66035 --source cache --database protein --rettype fasta
./bio-toolkit analyze sample.fasta --motif GAATTC --motif 're:GCCACCATG'
./bio-toolkit analyze NG_005905 --source cache --database nucleotide --rettype fasta --output outputs/NG_005905.analysis.json
./bio-toolkit analyze NG_005905 --source cache --database nucleotide --rettype fasta --output outputs/NG_005905.analysis.csv --export-format csv
```

### Annotation And Rich Exports

Available:
- annotate local GenBank files
- annotate cached GenBank records
- annotate FASTA input with reduced metadata depth
- extract organism, topology, date, genes, products, and feature counts
- terminal feature summaries for selected features
- export annotation reports to `json`, `csv`, `markdown`, and `html`

Examples:
```bash
./bio-toolkit annotate sample.gb
./bio-toolkit annotate NG_005905 --source cache --database nucleotide --rettype gb
./bio-toolkit annotate sample.gb --output outputs/sample.annotations.csv --export-format csv
./bio-toolkit annotate sample.gb --output outputs/sample.annotations.md --export-format markdown
./bio-toolkit annotate sample.gb --output outputs/sample.annotations.html --export-format html
./bio-toolkit annotate sample.gb --json
```

### Batch Workflows

Available:
- batch analyze from file lists
- batch analyze from accession lists
- batch fetch from accession lists
- per-item error isolation with optional `--fail-fast`
- terminal batch summary tables
- JSON or CSV export for batch reports

Examples:
```bash
./bio-toolkit batch inputs/files.txt --mode analyze --input-kind files
./bio-toolkit batch inputs/accessions.txt --mode analyze --input-kind accessions --database protein --rettype fasta
./bio-toolkit batch inputs/accessions.txt --mode fetch --input-kind accessions --database nucleotide
./bio-toolkit batch inputs/accessions.txt --mode analyze --input-kind accessions --database protein --rettype fasta --output outputs/batch.json
./bio-toolkit batch inputs/files.txt --mode analyze --input-kind files --output outputs/batch.csv --export-format csv
```

### Comparison

Available:
- compare two or more local files or cached accessions
- shared analysis path with `analyze`
- side-by-side terminal comparison table
- comparison highlights for sequence length
- comparison highlights for GC content, ORF counts, restriction hits, and CpG counts on nucleotide records
- comparison highlights for molecular weight, pI, and instability index on protein records
- JSON export for comparison reports

Examples:
```bash
./bio-toolkit compare sample_a.fasta sample_b.fasta
./bio-toolkit compare YDX66035 WP_480030509 --source cache --database protein --rettype fasta
./bio-toolkit compare sample_a.fasta sample_b.fasta --output outputs/compare.json
```

### Transformations

Available:
- reverse complement for DNA or RNA inputs
- translation for nucleotide inputs with frame selection
- subsequence extraction with 1-based inclusive coordinates
- FASTA output that can be saved or printed to stdout

Examples:
```bash
./bio-toolkit transform sample.fasta --operation reverse-complement
./bio-toolkit transform sample.fasta --operation translate --frame 2
./bio-toolkit transform sample.fasta --operation translate --frame 1 --to-stop --stdout
./bio-toolkit transform sample.fasta --operation subseq --start 10 --end 150
./bio-toolkit transform YDX66035 --source cache --database protein --rettype fasta --operation subseq --start 1 --end 60
```

### Remote BLAST

Available:
- remote-only BLAST workflows through NCBI
- query input from local files or cached records
- automatic `blastn` or `blastp` defaults based on query type
- terminal spinner and countdown while waiting for the RID to finish
- summarized hit tables in terminal
- export to `json`, `csv`, and `tsv`
- example FASTA included in `examples/hemoglobin_beta.fasta`

Examples:
```bash
./bio-toolkit blast examples/hemoglobin_beta.fasta
./bio-toolkit blast examples/hemoglobin_beta.fasta --output outputs/hemoglobin_beta.blast.csv --export-format csv
./bio-toolkit blast examples/hemoglobin_beta.fasta --program blastp --blast-database swissprot --json
./bio-toolkit blast YDX66035 --source cache --cache-database protein --cache-rettype fasta
```

## Planned Next

- repository publishing and release polish
- MySQL-backed persistence for saved runs and summaries
- a small API surface on top of the existing analysis core

## Future

- Snakemake integration
- FASTQ quality-oriented workflows
- compact text-only mode if real server/log usage demands it
