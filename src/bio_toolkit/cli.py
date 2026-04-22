from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bio_toolkit import __version__
from bio_toolkit.alphafold import AlphaFoldError, fetch_alphafold_prediction
from bio_toolkit.analysis import SequenceAnalyzer, compare_sequence_records, detect_molecule_type
from bio_toolkit.annotations import build_annotation_report, default_annotation_export_path
from bio_toolkit.cache_store import CacheError, CacheStore
from bio_toolkit.config import (
    ensure_runtime_dirs,
    get_installation_info,
    get_settings,
    refresh_settings,
)
from bio_toolkit.exporters import (
    normalize_blast_export_format,
    normalize_export_format,
    normalize_report_export_format,
    render_analysis_export,
    render_annotation_export,
    render_batch_export,
    render_blast_export,
)
from bio_toolkit.interactive_picker import (
    InteractivePickerCancelled,
    InteractivePickerError,
    pick_post_search_action,
    pick_search_result,
    prompt_guided_search,
)
from bio_toolkit.kegg import KeggError, fetch_kegg_sequence, search_kegg
from bio_toolkit.ncbi import (
    SUPPORTED_DATABASES,
    BlastSearchInfo,
    FetchResult,
    NcbiClient,
    NcbiConfigurationError,
    NcbiError,
    blast_hits_to_dict,
    default_fetch_path,
    search_results_to_dict,
)
from bio_toolkit.providers import (
    infer_query_input,
    infer_search_provider,
    normalize_kegg_search_database,
    normalize_search_provider,
    supported_kegg_databases_text,
)
from bio_toolkit.sequence_io import (
    SequenceIOError,
    dump_records_to_text,
    format_from_rettype,
    load_records_from_path,
    load_records_from_text,
)
from bio_toolkit.transforms import (
    TransformError,
    default_transform_path,
    transform_records,
)
from bio_toolkit.uniprot import (
    UniProtError,
    extract_uniprot_protein_context,
    fetch_uniprot_entry,
    fetch_uniprot_fasta,
    is_uniprot_accession,
    search_uniprot,
)

app = typer.Typer(
    add_completion=False,
    help="Linux-first CLI toolkit for NCBI sequence retrieval and analysis.",
    no_args_is_help=False,
)

FETCH_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional explicit output file path. Defaults to the configured output directory.",
)
ANALYZE_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional JSON output path for the analysis report.",
)
ANALYZE_MOTIF_OPTION = typer.Option(
    None,
    "--motif",
    help=(
        "Custom motif to search for during analysis. Repeat for multiple motifs. "
        "Use 're:<pattern>' for regex."
    ),
)
ANNOTATE_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional export file path for annotation output.",
)
COMPARE_TARGETS_ARGUMENT = typer.Argument(
    ...,
    help="Two or more local file paths or cached accessions to compare.",
)
COMPARE_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional JSON output path for the comparison report.",
)
TRANSFORM_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional output FASTA path. Defaults to the configured output directory.",
)
BLAST_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional export path for BLAST results.",
)
BATCH_TARGETS_ARGUMENT = typer.Argument(
    ...,
    help="Newline-delimited file with accessions or local sequence file paths.",
)
BATCH_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional JSON output path for the batch report.",
)


def _console(ctx: typer.Context | None = None) -> Console:
    settings = get_settings()
    plain = bool(ctx and ctx.obj and ctx.obj.get("plain"))
    return Console(no_color=plain or not settings.color_enabled)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    plain: bool = typer.Option(
        False,
        "--plain",
        help="Disable color-rich output for limited or log-oriented terminals.",
    ),
) -> None:
    """Show a concise project summary when no command is provided."""
    ctx.obj = {"plain": plain}
    if ctx.invoked_subcommand is not None:
        return

    console = _console(ctx)
    console.print(
        Panel.fit(
            (
                "Bio Toolkit\n"
                "NCBI search, local cache, and sequence analysis for Linux terminals."
            ),
            title=f"v{__version__}",
        )
    )

    table = Table(title="Command Surface")
    table.add_column("Command", style="cyan")
    table.add_column("Purpose", style="white")
    table.add_row("doctor", "Validate local runtime configuration")
    table.add_row("start", "Guided search and action picker")
    table.add_row("search", "Search NCBI records from the terminal")
    table.add_row("fetch", "Download an NCBI record by accession")
    table.add_row("batch", "Process repeated fetch/analyze work from a list")
    table.add_row("analyze", "Analyze a local or cached sequence record")
    table.add_row("annotate", "Inspect record metadata and selected features")
    table.add_row("compare", "Compare two or more local or cached records")
    table.add_row("transform", "Transform local or cached sequence records")
    table.add_row("blast", "Run remote BLAST searches from local or cached queries")
    table.add_row("cache", "Inspect local cache contents")
    console.print(table)
    console.print("Use `python -m bio_toolkit doctor --create-dirs` to validate local setup.")


@app.command()
def doctor(
    ctx: typer.Context,
    create_dirs: bool = typer.Option(
        False, "--create-dirs", help="Create cache and output directories if missing."
    ),
) -> None:
    """Inspect local configuration needed by the toolkit."""
    settings = refresh_settings()
    if create_dirs:
        ensure_runtime_dirs(settings)
        settings = refresh_settings()
    installation = get_installation_info()

    console = _console(ctx)

    table = Table(title="Runtime Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Status", style="green")

    email_status = "configured" if settings.ncbi_email else "missing"
    api_key_status = "configured" if settings.ncbi_api_key else "optional"

    table.add_row("NCBI_EMAIL", settings.ncbi_email or "-", email_status)
    table.add_row("NCBI_API_KEY", _mask(settings.ncbi_api_key), api_key_status)
    table.add_row("NCBI_TOOL_NAME", settings.ncbi_tool_name, "configured")
    table.add_row("ENV_FILE", str(settings.env_file), _env_status(settings))
    table.add_row("RUNTIME_ROOT", str(settings.runtime_root), "detected")
    table.add_row("PACKAGE_ROOT", str(installation.package_root), "detected")
    table.add_row("INSTALL_MODE", installation.install_mode, "detected")
    if installation.active_repo_root is not None:
        table.add_row(
            "ACTIVE_REPO",
            str(installation.active_repo_root),
            _active_repo_status(installation),
        )
    table.add_row("PLATFORM", platform.system().lower(), _platform_status())
    table.add_row("PYTHON", sys.version.split()[0], "detected")
    table.add_row("CACHE_DIR", str(settings.cache_dir), _path_status(settings.cache_dir))
    table.add_row("OUTPUT_DIR", str(settings.output_dir), _path_status(settings.output_dir))
    table.add_row("COLOR", str(settings.color_enabled).lower(), "configured")

    console.print(table)

    if not settings.ncbi_email:
        console.print(
            "[yellow]NCBI_EMAIL is not set. Add it in `.env` or export it before using "
            "NCBI commands.[/yellow]"
        )
    if installation.active_repo_matches_import is False:
        console.print(
            "[yellow]Bio Toolkit is being imported from a different clone than the active "
            "repository.[/yellow]"
        )
        console.print(f"[yellow]Imported package root:[/yellow] {installation.package_root}")
        console.print(f"[yellow]Active repository:[/yellow] {installation.active_repo_root}")
        console.print(
            "[yellow]Reinstall this clone with `./.venv/bin/python -m pip install -e "
            "\".[dev]\"` to realign the environment.[/yellow]"
        )


@app.command()
def start(ctx: typer.Context) -> None:
    """Run a guided search flow and open the interactive post-search actions."""
    console = _console(ctx)

    try:
        search_input = prompt_guided_search()
        settings = refresh_settings()
        query = str(search_input["query"])
        query_info = infer_query_input(query)

        if query_info["kind"] == "sequence":
            report = _build_guided_sequence_report(query_info)
            _render_analysis_report(
                console=console,
                report=report,
                exported_path=None,
                export_format=None,
            )
            return

        provider = str(search_input["provider"])
        results, provider_label = _search_provider_results(
            settings=settings,
            provider=provider,
            query=query,
            ncbi_database=str(search_input["database"]),
            organism=str(search_input["organism"]),
            limit=int(search_input["limit"]),
        )
    except InteractivePickerCancelled:
        console.print("[yellow]Guided search cancelled.[/yellow]")
        return
    except InteractivePickerError as exc:
        _fail(console, str(exc))
        return
    except (
        KeggError,
        NcbiConfigurationError,
        NcbiError,
        UniProtError,
        ValueError,
    ) as exc:
        _fail(console, str(exc))
        return

    if not results:
        console.print(Panel.fit("No results found for the guided search.", title="Search"))
        return

    console.print(_search_results_table(results, provider_label))
    console.print(f"{len(results)} result(s) returned.")
    _run_interactive_search_flow(
        console=console,
        settings=settings,
        database=str(search_input["database"]),
        results=results,
    )


@app.command()
def search(
    ctx: typer.Context,
    query: str = typer.Argument(
        ...,
        help="Free-text query, gene name, accession fragment, or term.",
    ),
    database: str = typer.Option(
        "nucleotide",
        "--database",
        "-d",
        help=(
            "Database to search. For NCBI use nucleotide or protein. "
            f"For KEGG use one of: {supported_kegg_databases_text()}."
        ),
    ),
    organism: str = typer.Option("", "--organism", "-o", help="Optional organism filter."),
    provider: str = typer.Option(
        "ncbi",
        "--provider",
        "-p",
        help="Search provider: ncbi, uniprot, kegg, or auto.",
    ),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of results (1-100)."),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON instead of a Rich table."),
    pick: bool = typer.Option(
        False,
        "--pick",
        help="Interactively choose a result and decide what to do next.",
    ),
) -> None:
    """Search NCBI, UniProt, or KEGG from the terminal."""
    console = _console(ctx)

    if as_json and pick:
        _fail(console, "--json and --pick cannot be used together.")

    try:
        settings = refresh_settings()
        results, provider_label = _search_provider_results(
            settings=settings,
            provider=provider,
            query=query,
            ncbi_database=database,
            organism=organism,
            limit=limit,
        )
    except (
        KeggError,
        NcbiConfigurationError,
        NcbiError,
        UniProtError,
        ValueError,
    ) as exc:
        _fail(console, str(exc))
        return

    if as_json:
        console.print_json(json.dumps(search_results_to_dict(results), indent=2))
        return

    if not results:
        console.print(Panel.fit("No results found for the given query.", title="Search"))
        return

    console.print(_search_results_table(results, provider_label))
    console.print(f"{len(results)} result(s) returned.")

    if pick:
        _run_interactive_search_flow(
            console=console,
            settings=settings,
            database=database,
            results=results,
        )


@app.command()
def fetch(
    ctx: typer.Context,
    accession: str = typer.Argument(..., help="NCBI accession or accession.version to retrieve."),
    database: str = typer.Option(
        "nucleotide",
        "--database",
        "-d",
        help=f"NCBI database to fetch from ({', '.join(sorted(SUPPORTED_DATABASES))}).",
    ),
    rettype: str = typer.Option(
        "fasta",
        "--rettype",
        "-r",
        help="Remote record format to fetch: fasta, gb, or genbank.",
    ),
    output: Path | None = FETCH_OUTPUT_OPTION,
    stdout: bool = typer.Option(False, "--stdout", help="Print the fetched record to stdout."),
    preview_lines: int = typer.Option(
        8,
        "--preview-lines",
        help="Number of leading lines to preview after saving the record.",
    ),
    use_cache: bool = typer.Option(
        True,
        "--use-cache/--no-use-cache",
        help="Reuse a matching cached record before making a new NCBI request.",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        help="Bypass any cached copy and force a fresh NCBI request.",
    ),
    save_cache: bool = typer.Option(
        True,
        "--cache/--no-cache",
        help="Save fetched records into the local cache.",
    ),
) -> None:
    """Fetch a sequence record by accession."""
    console = _console(ctx)

    try:
        settings = refresh_settings()
        ensure_runtime_dirs(settings)
        cache_store, cache_record, record = _resolve_fetch(
            console=console,
            settings=settings,
            accession=accession,
            database=database,
            rettype=rettype,
            use_cache=use_cache,
            refresh=refresh,
            save_cache=save_cache,
        )
    except (CacheError, NcbiConfigurationError, NcbiError, ValueError) as exc:
        _fail(console, str(exc))
        return

    _render_fetch_output(
        console=console,
        settings=settings,
        cache_store=cache_store,
        cache_record=cache_record,
        record=record,
        accession=accession,
        rettype=rettype,
        output=output,
        stdout=stdout,
        preview_lines=preview_lines,
    )


@app.command()
def analyze(
    ctx: typer.Context,
    target: str = typer.Argument(
        ...,
        help="Local sequence file path or cached accession, depending on --source.",
    ),
    source: str = typer.Option(
        "auto",
        "--source",
        "-s",
        help="Input source: auto, file, or cache.",
    ),
    input_format: str = typer.Option(
        "auto",
        "--input-format",
        "-f",
        help="Input format for local or cached content: auto, fasta, genbank, or gb.",
    ),
    database: str = typer.Option(
        "",
        "--database",
        "-d",
        help="Optional cache database when analyzing a cached accession.",
    ),
    rettype: str = typer.Option(
        "",
        "--rettype",
        "-r",
        help="Optional cache format when analyzing a cached accession.",
    ),
    min_orf_aa: int = typer.Option(
        30,
        "--min-orf-aa",
        help="Minimum ORF length in amino acids for nucleotide analysis.",
    ),
    motif: list[str] | None = ANALYZE_MOTIF_OPTION,
    as_json: bool = typer.Option(False, "--json", help="Emit JSON to stdout."),
    output: Path | None = ANALYZE_OUTPUT_OPTION,
    export_format: str = typer.Option(
        "auto",
        "--export-format",
        help="Export format when using --output: auto, json, or csv.",
    ),
) -> None:
    """Analyze a local file or cached sequence record."""
    console = _console(ctx)

    try:
        settings = refresh_settings()
        ensure_runtime_dirs(settings)
        records, resolved_format, source_info = _load_analysis_input(
            settings=settings,
            target=target,
            source=source,
            input_format=input_format,
            database=database,
            rettype=rettype,
        )
        with console.status("Analyzing sequence records..."):
            report = _build_analysis_report(
                records=records,
                resolved_format=resolved_format,
                source_info=source_info,
                min_orf_aa=min_orf_aa,
                custom_motifs=motif,
            )
    except (CacheError, SequenceIOError, ValueError) as exc:
        _fail(console, str(exc))
        return

    if output is None and export_format.strip().lower() != "auto":
        _fail(console, "Use --output together with --export-format.")

    normalized_export_format = None
    exported_path = None
    if output is not None:
        normalized_export_format = _resolve_report_export_format(export_format, output)
        exported_path = _write_text_export(
            settings=settings,
            output=output,
            default_output=output,
            content=render_analysis_export(report, normalized_export_format),
        )

    if as_json:
        console.print_json(json.dumps(report, indent=2))
        return

    _render_analysis_report(
        console=console,
        report=report,
        exported_path=exported_path,
        export_format=normalized_export_format,
    )


@app.command()
def annotate(
    ctx: typer.Context,
    target: str = typer.Argument(
        ...,
        help="Local sequence file path or cached accession to annotate.",
    ),
    source: str = typer.Option(
        "auto",
        "--source",
        "-s",
        help="Input source: auto, file, or cache.",
    ),
    input_format: str = typer.Option(
        "auto",
        "--input-format",
        "-f",
        help="Input format for local or cached content: auto, fasta, genbank, or gb.",
    ),
    database: str = typer.Option(
        "",
        "--database",
        "-d",
        help="Optional cache database when annotating cached accessions.",
    ),
    rettype: str = typer.Option(
        "",
        "--rettype",
        "-r",
        help="Optional cache format when annotating cached accessions.",
    ),
    feature_limit: int = typer.Option(
        10,
        "--feature-limit",
        help="Maximum number of feature summaries to include per record.",
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON to stdout."),
    output: Path | None = ANNOTATE_OUTPUT_OPTION,
    export_format: str = typer.Option(
        "json",
        "--export-format",
        help="Export format when using --output: json, csv, markdown, or html.",
    ),
) -> None:
    """Inspect annotations and selected features for local or cached records."""
    console = _console(ctx)

    try:
        settings = refresh_settings()
        ensure_runtime_dirs(settings)
        records, resolved_format, source_info = _load_analysis_input(
            settings=settings,
            target=target,
            source=source,
            input_format=input_format,
            database=database,
            rettype=rettype,
        )
        with console.status("Extracting annotations..."):
            report = build_annotation_report(
                records=records,
                input_format=resolved_format,
                source_info=source_info,
                feature_limit=feature_limit,
            )
            normalized_export_format = normalize_export_format(export_format)
    except (CacheError, SequenceIOError, ValueError) as exc:
        _fail(console, str(exc))
        return

    exported_path = None
    if output is not None:
        exported_path = _write_text_export(
            settings=settings,
            output=output,
            default_output=default_annotation_export_path(
                settings.output_dir,
                _annotation_output_label(source_info),
                normalized_export_format,
            ),
            content=render_annotation_export(report, normalized_export_format),
        )

    if as_json:
        console.print_json(json.dumps(report, indent=2))
        if exported_path is not None:
            console.print(
                "[green]"
                f"{normalized_export_format.upper()} export written to:[/green] "
                f"{exported_path}"
            )
        return

    _render_annotation_report(
        console=console,
        report=report,
        exported_path=exported_path,
        export_format=normalized_export_format if exported_path is not None else None,
    )


@app.command()
def compare(
    ctx: typer.Context,
    targets: list[str] = COMPARE_TARGETS_ARGUMENT,
    source: str = typer.Option(
        "auto",
        "--source",
        "-s",
        help="Input source: auto, file, or cache.",
    ),
    input_format: str = typer.Option(
        "auto",
        "--input-format",
        "-f",
        help="Input format for local or cached content: auto, fasta, genbank, or gb.",
    ),
    database: str = typer.Option(
        "",
        "--database",
        "-d",
        help="Optional cache database when comparing cached accessions.",
    ),
    rettype: str = typer.Option(
        "",
        "--rettype",
        "-r",
        help="Optional cache format when comparing cached accessions.",
    ),
    min_orf_aa: int = typer.Option(
        30,
        "--min-orf-aa",
        help="Minimum ORF length in amino acids for nucleotide comparison.",
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON to stdout."),
    output: Path | None = COMPARE_OUTPUT_OPTION,
) -> None:
    """Compare two or more local files or cached sequence records."""
    console = _console(ctx)

    if len(targets) < 2:
        _fail(console, "Compare requires at least two targets.")

    try:
        settings = refresh_settings()
        ensure_runtime_dirs(settings)
        with console.status("Comparing sequence records..."):
            report = _build_compare_report(
                settings=settings,
                targets=targets,
                source=source,
                input_format=input_format,
                database=database,
                rettype=rettype,
                min_orf_aa=min_orf_aa,
            )
    except (CacheError, SequenceIOError, ValueError) as exc:
        _fail(console, str(exc))
        return

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if as_json:
        console.print_json(json.dumps(report, indent=2))
        return

    _render_compare_report(console, report, output)


@app.command()
def transform(
    ctx: typer.Context,
    target: str = typer.Argument(
        ...,
        help="Local sequence file path or cached accession to transform.",
    ),
    operation: str = typer.Option(
        "reverse-complement",
        "--operation",
        "-m",
        help="Transform to run: reverse-complement, translate, or subseq.",
    ),
    source: str = typer.Option(
        "auto",
        "--source",
        "-s",
        help="Input source: auto, file, or cache.",
    ),
    input_format: str = typer.Option(
        "auto",
        "--input-format",
        "-f",
        help="Input format for local or cached content: auto, fasta, genbank, or gb.",
    ),
    database: str = typer.Option(
        "",
        "--database",
        "-d",
        help="Optional cache database when transforming cached accessions.",
    ),
    rettype: str = typer.Option(
        "",
        "--rettype",
        "-r",
        help="Optional cache format when transforming cached accessions.",
    ),
    frame: int = typer.Option(
        1,
        "--frame",
        help="Translation frame for translate: 1, 2, or 3.",
    ),
    to_stop: bool = typer.Option(
        False,
        "--to-stop",
        help="Stop translation at the first stop codon.",
    ),
    start: int = typer.Option(
        1,
        "--start",
        help="1-based inclusive subsequence start.",
    ),
    end: int = typer.Option(
        0,
        "--end",
        help="1-based inclusive subsequence end. Use 0 for end-of-sequence.",
    ),
    output: Path | None = TRANSFORM_OUTPUT_OPTION,
    stdout: bool = typer.Option(False, "--stdout", help="Print transformed FASTA to stdout."),
    preview_lines: int = typer.Option(
        8,
        "--preview-lines",
        help="Number of leading lines to preview after saving transformed output.",
    ),
) -> None:
    """Transform local or cached sequence records into reusable FASTA output."""
    console = _console(ctx)

    try:
        settings = refresh_settings()
        ensure_runtime_dirs(settings)
        with console.status("Transforming sequence records..."):
            report, fasta_text = _build_transform_report(
                settings=settings,
                target=target,
                operation=operation,
                source=source,
                input_format=input_format,
                database=database,
                rettype=rettype,
                frame=frame,
                to_stop=to_stop,
                start=start,
                end=end,
            )
    except (CacheError, SequenceIOError, TransformError, ValueError) as exc:
        _fail(console, str(exc))
        return

    _render_transform_output(
        console=console,
        settings=settings,
        report=report,
        fasta_text=fasta_text,
        output=output,
        stdout=stdout,
        preview_lines=preview_lines,
    )


@app.command()
def blast(
    ctx: typer.Context,
    target: str = typer.Argument(
        ...,
        help="Local sequence file path or cached accession to submit as the BLAST query.",
    ),
    source: str = typer.Option(
        "auto",
        "--source",
        "-s",
        help="Input source: auto, file, or cache.",
    ),
    input_format: str = typer.Option(
        "auto",
        "--input-format",
        "-f",
        help="Input format for local or cached content: auto, fasta, genbank, or gb.",
    ),
    cache_database: str = typer.Option(
        "",
        "--cache-database",
        help="Optional cache database when blasting a cached accession.",
    ),
    cache_rettype: str = typer.Option(
        "",
        "--cache-rettype",
        help="Optional cache format when blasting a cached accession.",
    ),
    program: str = typer.Option(
        "auto",
        "--program",
        "-p",
        help="Remote BLAST program: auto, blastn, blastp, blastx, tblastn, or tblastx.",
    ),
    blast_database: str = typer.Option(
        "auto",
        "--blast-database",
        "-d",
        help=(
            "Remote BLAST database. Defaults to core_nt for nucleotide searches and "
            "swissprot for protein searches."
        ),
    ),
    hitlist_size: int = typer.Option(
        10,
        "--hitlist-size",
        help="Maximum number of target sequences NCBI should keep for the job.",
    ),
    expect: float = typer.Option(
        10.0,
        "--expect",
        help="Expectation value threshold for the remote BLAST search.",
    ),
    poll_interval: int = typer.Option(
        60,
        "--poll-interval",
        help="Seconds between remote RID status checks. NCBI guidance recommends at least 60.",
    ),
    timeout_seconds: int = typer.Option(
        1800,
        "--timeout-seconds",
        help="Maximum time to wait for the remote BLAST job to finish.",
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit the full BLAST report as JSON."),
    output: Path | None = BLAST_OUTPUT_OPTION,
    export_format: str = typer.Option(
        "auto",
        "--export-format",
        help="Export format when using --output: auto, json, csv, or tsv.",
    ),
) -> None:
    """Run a remote BLAST workflow from a local or cached query sequence."""
    console = _console(ctx)

    try:
        settings = refresh_settings()
        ensure_runtime_dirs(settings)
        records, resolved_format, source_info = _load_analysis_input(
            settings=settings,
            target=target,
            source=source,
            input_format=input_format,
            database=cache_database,
            rettype=cache_rettype,
        )
        report = _run_remote_blast(
            console=console,
            records=records,
            resolved_format=resolved_format,
            source_info=source_info,
            program=program,
            blast_database=blast_database,
            hitlist_size=hitlist_size,
            expect=expect,
            poll_interval=poll_interval,
            timeout_seconds=timeout_seconds,
        )
    except (CacheError, NcbiConfigurationError, NcbiError, SequenceIOError, ValueError) as exc:
        _fail(console, str(exc))
        return

    if output is None and export_format.strip().lower() != "auto":
        _fail(console, "Use --output together with --export-format.")

    normalized_export_format = None
    exported_path = None
    if output is not None:
        normalized_export_format = _resolve_blast_export_format(export_format, output)
        exported_path = _write_text_export(
            settings=settings,
            output=output,
            default_output=output,
            content=render_blast_export(report, normalized_export_format),
        )

    if as_json:
        console.print_json(json.dumps(report, indent=2))
        if exported_path is not None and normalized_export_format is not None:
            console.print(
                "[green]"
                f"{normalized_export_format.upper()} export written to:[/green] "
                f"{exported_path}"
            )
        return

    _render_blast_report(
        console=console,
        report=report,
        exported_path=exported_path,
        export_format=normalized_export_format,
    )


@app.command()
def batch(
    ctx: typer.Context,
    targets_file: Path = BATCH_TARGETS_ARGUMENT,
    mode: str = typer.Option(
        "analyze",
        "--mode",
        "-m",
        help="Batch operation to run: analyze or fetch.",
    ),
    input_kind: str = typer.Option(
        "auto",
        "--input-kind",
        "-k",
        help="Interpret input lines as auto, accessions, or files.",
    ),
    database: str = typer.Option(
        "nucleotide",
        "--database",
        "-d",
        help=(
            "NCBI database to use for accession items "
            f"({', '.join(sorted(SUPPORTED_DATABASES))})."
        ),
    ),
    rettype: str = typer.Option(
        "fasta",
        "--rettype",
        "-r",
        help="Record format for accession items: fasta, gb, or genbank.",
    ),
    input_format: str = typer.Option(
        "auto",
        "--input-format",
        "-f",
        help="Input format for local sequence files: auto, fasta, genbank, or gb.",
    ),
    min_orf_aa: int = typer.Option(
        30,
        "--min-orf-aa",
        help="Minimum ORF length in amino acids for nucleotide analysis.",
    ),
    use_cache: bool = typer.Option(
        True,
        "--use-cache/--no-use-cache",
        help="Reuse cached accession records before contacting NCBI.",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        help="Force fresh NCBI retrieval for accession items.",
    ),
    fail_fast: bool = typer.Option(
        False,
        "--fail-fast",
        help="Stop the batch on the first item that fails.",
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit the full batch report as JSON."),
    output: Path | None = BATCH_OUTPUT_OPTION,
    export_format: str = typer.Option(
        "auto",
        "--export-format",
        help="Export format when using --output: auto, json, or csv.",
    ),
) -> None:
    """Process multiple accession or local sequence inputs in one run."""
    console = _console(ctx)

    try:
        settings = refresh_settings()
        ensure_runtime_dirs(settings)
        items = _read_batch_targets(targets_file)
        report = _run_batch(
            console=console,
            settings=settings,
            items=items,
            targets_file=targets_file,
            mode=mode,
            input_kind=input_kind,
            database=database,
            rettype=rettype,
            input_format=input_format,
            min_orf_aa=min_orf_aa,
            use_cache=use_cache,
            refresh=refresh,
            fail_fast=fail_fast,
        )
    except (CacheError, NcbiConfigurationError, NcbiError, SequenceIOError, ValueError) as exc:
        _fail(console, str(exc))
        return

    if output is None and export_format.strip().lower() != "auto":
        _fail(console, "Use --output together with --export-format.")

    normalized_export_format = None
    exported_path = None
    if output is not None:
        normalized_export_format = _resolve_report_export_format(export_format, output)
        exported_path = _write_text_export(
            settings=settings,
            output=output,
            default_output=output,
            content=render_batch_export(report, normalized_export_format),
        )

    if as_json:
        console.print_json(json.dumps(report, indent=2))
        return

    _render_batch_report(
        console=console,
        report=report,
        exported_path=exported_path,
        export_format=normalized_export_format,
    )


@app.command()
def cache(
    ctx: typer.Context,
    accession: str | None = typer.Argument(
        None,
        help="Optional accession to inspect in detail. Omit it to list cached records.",
    ),
    database: str = typer.Option(
        "",
        "--database",
        "-d",
        help="Optional database filter when listing, or exact database for record lookup.",
    ),
    rettype: str = typer.Option(
        "",
        "--rettype",
        "-r",
        help="Optional format filter when listing, or exact format for record lookup.",
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
    preview_lines: int = typer.Option(
        8,
        "--preview-lines",
        help="Number of lines to preview when showing a specific cached record.",
    ),
) -> None:
    """Inspect local cache contents."""
    console = _console(ctx)

    try:
        settings = refresh_settings()
        cache_store = CacheStore(settings.cache_dir)
        if accession is None:
            records = cache_store.list_records(database=database, rettype=rettype)
        else:
            lookup_database = database or "nucleotide"
            lookup_rettype = rettype or "fasta"
            loaded = cache_store.load_fetch_result(
                accession=accession,
                database=lookup_database,
                rettype=lookup_rettype,
            )
            if loaded is None:
                _fail(
                    console,
                    "No cached record matched that accession/database/rettype combination.",
                )
                return
            cache_record, fetch_result = loaded
    except (CacheError, ValueError) as exc:
        _fail(console, str(exc))
        return

    if accession is None:
        if as_json:
            console.print_json(
                json.dumps([_cache_record_to_dict(item) for item in records], indent=2)
            )
            return

        if not records:
            console.print(Panel.fit("Cache is empty.", title="Cache"))
            return

        table = Table(title="Cached Records")
        table.add_column("Accession", style="cyan", no_wrap=True)
        table.add_column("Database", style="green")
        table.add_column("Format", style="magenta")
        table.add_column("Fetched At", style="white")
        table.add_column("Size", justify="right")
        table.add_column("Path", style="white")

        for item in records:
            table.add_row(
                item.accession,
                item.database,
                item.rettype,
                item.fetched_at,
                _human_size(item.file_size),
                str(cache_store.resolve_content_path(item)),
            )

        console.print(table)
        console.print(f"{len(records)} cached record(s).")
        return

    if as_json:
        payload = _cache_record_to_dict(cache_record) | {
            "content_preview": _preview_text(fetch_result.content, preview_lines)
        }
        console.print_json(json.dumps(payload, indent=2))
        return

    summary = Table(title="Cached Record")
    summary.add_column("Field", style="cyan")
    summary.add_column("Value", style="white")
    summary.add_row("Accession", cache_record.accession)
    summary.add_row("Database", cache_record.database)
    summary.add_row("Format", cache_record.rettype)
    summary.add_row("Fetched At", cache_record.fetched_at)
    summary.add_row("Size", _human_size(cache_record.file_size))
    summary.add_row("Path", str(cache_store.resolve_content_path(cache_record)))
    console.print(summary)

    preview = _preview_text(fetch_result.content, preview_lines)
    if preview:
        console.print(Panel(preview, title="Preview", expand=False))


def _mask(value: str) -> str:
    if not value:
        return "-"
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}***{value[-2:]}"


def _path_status(path: Path) -> str:
    return "exists" if path.exists() else "not-created"


def _env_status(settings) -> str:
    return "found" if settings.env_file_found else "not-found"


def _active_repo_status(installation) -> str:
    if installation.active_repo_matches_import:
        return "matches-import"
    return "mismatch"


def _platform_status() -> str:
    return "preferred" if platform.system().lower() == "linux" else "supported"


def _planned_command(ctx: typer.Context, message: str) -> None:
    console = _console(ctx)
    console.print(Panel.fit(message, title="Planned Command"))


def _build_ncbi_client() -> NcbiClient:
    return NcbiClient.from_settings(refresh_settings())


def _search_provider_results(
    *,
    settings,
    provider: str,
    query: str,
    ncbi_database: str,
    organism: str,
    limit: int,
) -> tuple[list, str]:
    resolved_provider = normalize_search_provider(provider)
    if resolved_provider == "auto":
        resolved_provider = infer_search_provider(query)

    if resolved_provider == "ncbi":
        results = NcbiClient.from_settings(settings).search(
            database=ncbi_database,
            query=query,
            organism=organism,
            limit=limit,
        )
        return results, f"NCBI:{ncbi_database}"

    if resolved_provider == "uniprot":
        results = search_uniprot(query=query, organism=organism, limit=limit)
        return results, "UniProt"

    try:
        kegg_database = normalize_kegg_search_database(ncbi_database)
    except ValueError:
        kegg_database = "genes"

    results = search_kegg(query=query, database=kegg_database, limit=limit)
    return results, f"KEGG:{kegg_database}"


def _build_guided_sequence_report(query_info: dict[str, str]) -> dict:
    sequence_text = f">guided_query\n{query_info['normalized']}\n"
    records, resolved_format = load_records_from_text(sequence_text, input_format="fasta")
    return _build_analysis_report(
        records=records,
        resolved_format=resolved_format,
        source_info={
            "kind": "guided-sequence",
            "label": "guided-query",
            "provider": "local-sequence",
            "molecule_type": query_info["molecule_type"],
        },
        min_orf_aa=30,
    )


def _preview_text(content: str, preview_lines: int) -> str:
    if preview_lines <= 0:
        return ""
    return "\n".join(content.splitlines()[:preview_lines])


def _fail(console: Console, message: str) -> None:
    console.print(f"[red]{message}[/red]")
    raise typer.Exit(code=1)


def _cache_record_to_dict(record) -> dict[str, str | int]:
    return {
        "accession": record.accession,
        "database": record.database,
        "rettype": record.rettype,
        "source": record.source,
        "fetched_at": record.fetched_at,
        "content_path": record.content_path,
        "file_size": record.file_size,
    }


def _read_batch_targets(targets_file: Path) -> list[str]:
    if not targets_file.exists():
        raise ValueError(f"Batch input file was not found: {targets_file}")

    items = []
    for line in targets_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        items.append(stripped)

    if not items:
        raise ValueError("Batch input file did not contain any usable items.")

    return items


def _run_batch(
    *,
    console: Console,
    settings,
    items: list[str],
    targets_file: Path,
    mode: str,
    input_kind: str,
    database: str,
    rettype: str,
    input_format: str,
    min_orf_aa: int,
    use_cache: bool,
    refresh: bool,
    fail_fast: bool,
) -> dict:
    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"analyze", "fetch"}:
        raise ValueError("Unsupported batch mode. Use one of: analyze, fetch.")

    normalized_input_kind = input_kind.strip().lower()
    if normalized_input_kind not in {"auto", "accessions", "files"}:
        raise ValueError("Unsupported input kind. Use one of: auto, accessions, files.")

    if normalized_mode == "fetch" and normalized_input_kind == "files":
        raise ValueError("Fetch mode does not support --input-kind files.")

    results = []
    with console.status(f"Running batch {normalized_mode} on {len(items)} item(s)..."):
        for raw_item in items:
            try:
                item_report = _run_batch_item(
                    console=console,
                    settings=settings,
                    raw_item=raw_item,
                    base_dir=targets_file.parent,
                    mode=normalized_mode,
                    input_kind=normalized_input_kind,
                    database=database,
                    rettype=rettype,
                    input_format=input_format,
                    min_orf_aa=min_orf_aa,
                    use_cache=use_cache,
                    refresh=refresh,
                )
            except (
                CacheError,
                NcbiConfigurationError,
                NcbiError,
                SequenceIOError,
                ValueError,
            ) as exc:
                item_report = {
                    "item": raw_item,
                    "status": "error",
                    "operation": normalized_mode,
                    "error": str(exc),
                }
                results.append(item_report)
                if fail_fast:
                    raise ValueError(f"Batch stopped at '{raw_item}': {exc}") from exc
                continue

            results.append(item_report)

    succeeded = sum(1 for item in results if item["status"] == "ok")
    failed = len(results) - succeeded

    return {
        "mode": normalized_mode,
        "input_kind": normalized_input_kind,
        "targets_file": str(targets_file.resolve()),
        "database": database,
        "rettype": rettype,
        "total_items": len(results),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }


def _run_batch_item(
    *,
    console: Console,
    settings,
    raw_item: str,
    base_dir: Path,
    mode: str,
    input_kind: str,
    database: str,
    rettype: str,
    input_format: str,
    min_orf_aa: int,
    use_cache: bool,
    refresh: bool,
) -> dict:
    item_type, resolved_path = _resolve_batch_item_kind(
        raw_item=raw_item,
        base_dir=base_dir,
        input_kind=input_kind,
    )

    if item_type == "file":
        if mode == "fetch":
            raise ValueError("Fetch mode only accepts accession items.")
        records, resolved_format = load_records_from_path(resolved_path, input_format=input_format)
        report = _build_analysis_report(
            records=records,
            resolved_format=resolved_format,
            source_info={"kind": "file", "label": str(resolved_path.resolve())},
            min_orf_aa=min_orf_aa,
        )
        return {
            "item": raw_item,
            "status": "ok",
            "operation": mode,
            "source_kind": "file",
            "label": str(resolved_path.resolve()),
            "input_format": resolved_format,
            "record_count": report["record_count"],
            "molecule_types": sorted({record["molecule_type"] for record in report["records"]}),
            "analysis": report,
        }

    cache_store, cache_record, record = _resolve_fetch(
        console=console,
        settings=settings,
        accession=raw_item,
        database=database,
        rettype=rettype,
        use_cache=use_cache,
        refresh=refresh,
        save_cache=True,
    )

    if mode == "fetch":
        saved_to = _write_fetched_output(
            settings=settings,
            record=record,
            accession=raw_item,
            rettype=rettype,
        )
        return {
            "item": raw_item,
            "status": "ok",
            "operation": mode,
            "source_kind": "accession",
            "accession": record.accession,
            "database": record.database,
            "rettype": record.rettype,
            "retrieved_from": record.source,
            "saved_to": str(saved_to),
            "cache_path": (
                str(cache_store.resolve_content_path(cache_record))
                if cache_record is not None
                else None
            ),
        }

    resolved_input_format = format_from_rettype(record.rettype)
    records, resolved_format = load_records_from_text(
        record.content,
        input_format=resolved_input_format,
    )
    report = _build_analysis_report(
        records=records,
        resolved_format=resolved_format,
        source_info={
            "kind": record.source,
            "label": record.accession,
            "accession": record.accession,
            "database": record.database,
            "provider": record.provider,
            "rettype": record.rettype,
        },
        min_orf_aa=min_orf_aa,
    )
    return {
        "item": raw_item,
        "status": "ok",
        "operation": mode,
        "source_kind": "accession",
        "accession": record.accession,
        "database": record.database,
        "rettype": record.rettype,
        "retrieved_from": record.source,
        "record_count": report["record_count"],
        "molecule_types": sorted({entry["molecule_type"] for entry in report["records"]}),
        "analysis": report,
    }


def _resolve_batch_item_kind(
    *,
    raw_item: str,
    base_dir: Path,
    input_kind: str,
) -> tuple[str, Path | None]:
    if input_kind == "accessions":
        return "accession", None

    candidate = Path(raw_item)
    if not candidate.is_absolute():
        candidate = (base_dir / candidate).resolve()

    if input_kind == "files":
        if not candidate.exists():
            raise ValueError(f"Listed file was not found: {candidate}")
        return "file", candidate

    if candidate.exists():
        return "file", candidate

    return "accession", None


def _resolve_fetch(
    *,
    console: Console,
    settings,
    accession: str,
    database: str,
    rettype: str,
    use_cache: bool,
    refresh: bool,
    save_cache: bool,
):
    cache_store = CacheStore(settings.cache_dir)
    cache_record = None
    record = None

    if use_cache and not refresh:
        cached = cache_store.load_fetch_result(
            accession=accession,
            database=database,
            rettype=rettype,
        )
        if cached is not None:
            cache_record, record = cached

    if record is None:
        client = _build_ncbi_client()
        with console.status("Fetching record from NCBI..."):
            record = client.fetch(database=database, accession=accession, rettype=rettype)
        if save_cache:
            cache_record = cache_store.save_fetch_result(record)

    return cache_store, cache_record, record


def _write_fetched_output(
    *,
    settings,
    record: FetchResult,
    accession: str,
    rettype: str,
    output: Path | None = None,
) -> Path:
    destination = output or default_fetch_path(settings.output_dir, accession, rettype)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(record.content, encoding="utf-8")
    return destination


def _render_fetch_output(
    *,
    console: Console,
    settings,
    cache_store: CacheStore,
    cache_record,
    record: FetchResult,
    accession: str,
    rettype: str,
    output: Path | None,
    stdout: bool,
    preview_lines: int,
) -> Path | None:
    if stdout:
        console.print(record.content)
        return None

    destination = _write_fetched_output(
        settings=settings,
        record=record,
        accession=accession,
        rettype=rettype,
        output=output,
    )

    summary = Table(title="Fetched Record")
    summary.add_column("Field", style="cyan")
    summary.add_column("Value", style="white")
    summary.add_row("Accession", record.accession)
    summary.add_row("Database", record.database)
    summary.add_row("Format", record.rettype)
    summary.add_row("Retrieved From", record.source)
    summary.add_row("Output", str(destination))
    if cache_record is not None:
        summary.add_row("Cache Path", str(cache_store.resolve_content_path(cache_record)))
    console.print(summary)

    preview = _preview_text(record.content, preview_lines)
    if preview:
        console.print(Panel(preview, title="Preview", expand=False))

    return destination


def _load_analysis_input(
    *,
    settings,
    target: str,
    source: str,
    input_format: str,
    database: str,
    rettype: str,
) -> tuple[list, str, dict[str, str]]:
    normalized_source = source.strip().lower()
    if normalized_source not in {"auto", "file", "cache"}:
        raise ValueError("Unsupported source. Use one of: auto, file, cache.")

    target_path = Path(target)
    if normalized_source in {"auto", "file"} and target_path.exists():
        records, resolved_format = load_records_from_path(target_path, input_format=input_format)
        return (
            records,
            resolved_format,
            {"kind": "file", "label": str(target_path.resolve())},
        )

    if normalized_source == "file":
        raise SequenceIOError(f"Local input file was not found: {target}")

    cache_store = CacheStore(settings.cache_dir)

    if database or rettype:
        lookup_database = database or "nucleotide"
        lookup_rettype = rettype or "fasta"
        loaded = cache_store.load_fetch_result(
            accession=target,
            database=lookup_database,
            rettype=lookup_rettype,
        )
        if loaded is None:
            raise CacheError(
                "No cached record matched that accession/database/rettype combination."
            )
        cache_record, fetch_result = loaded
    else:
        matches = cache_store.find_records_by_accession(target)
        if not matches:
            raise CacheError(
                "No cached record matched that accession. Provide --database/--rettype "
                "or fetch it first."
            )
        if len(matches) > 1:
            raise CacheError(
                "Multiple cached records matched that accession. Re-run with --database "
                "and --rettype."
            )
        cache_record = matches[0]
        loaded = cache_store.load_fetch_result(
            accession=cache_record.accession,
            database=cache_record.database,
            rettype=cache_record.rettype,
        )
        if loaded is None:
            raise CacheError("Cached record metadata exists but the record could not be loaded.")
        _, fetch_result = loaded

    resolved_input_format = (
        format_from_rettype(cache_record.rettype) if input_format == "auto" else input_format
    )
    records, resolved_format = load_records_from_text(
        fetch_result.content,
        input_format=resolved_input_format,
    )
    return (
        records,
        resolved_format,
        {
            "kind": "cache",
            "label": cache_record.accession,
            "accession": cache_record.accession,
            "database": cache_record.database,
            "provider": fetch_result.provider,
            "rettype": cache_record.rettype,
        },
    )


def _render_analysis_report(
    *,
    console: Console,
    report: dict,
    exported_path: Path | None,
    export_format: str | None,
) -> None:
    source = report["source"]
    summary_lines = [
        f"Source: {source['kind']}",
        f"Label: {source['label']}",
        f"Input format: {report['input_format']}",
        f"Records analyzed: {report['record_count']}",
    ]
    if source["kind"] == "cache":
        summary_lines.append(f"Cache database: {source['database']}")
        summary_lines.append(f"Cache format: {source['rettype']}")

    console.print(Panel.fit("\n".join(summary_lines), title="Analysis Report"))
    console.print(_analysis_summary_table(report["records"]))

    if len(report["records"]) == 1:
        _render_single_record_details(console, report["records"][0])

    if exported_path is not None and export_format is not None:
        console.print(f"[green]{export_format.upper()} report written to:[/green] {exported_path}")


def _render_annotation_report(
    *,
    console: Console,
    report: dict,
    exported_path: Path | None,
    export_format: str | None,
) -> None:
    source = report["source"]
    summary_lines = [
        f"Source: {source['kind']}",
        f"Label: {source['label']}",
        f"Input format: {report['input_format']}",
        f"Records annotated: {report['record_count']}",
        f"Feature limit: {report['feature_limit']}",
    ]
    if source["kind"] == "cache":
        summary_lines.append(f"Cache database: {source['database']}")
        summary_lines.append(f"Cache format: {source['rettype']}")

    console.print(Panel.fit("\n".join(summary_lines), title="Annotation Report"))
    console.print(_annotation_summary_table(report["records"]))

    if len(report["records"]) == 1:
        console.print(_annotation_metadata_table(report["records"][0]))
        feature_table = _annotation_features_table(report["records"][0]["selected_features"])
        if feature_table is not None:
            console.print(feature_table)

    if exported_path is not None and export_format is not None:
        console.print(f"[green]{export_format.upper()} export written to:[/green] {exported_path}")


def _build_compare_report(
    *,
    settings,
    targets: list[str],
    source: str,
    input_format: str,
    database: str,
    rettype: str,
    min_orf_aa: int,
) -> dict:
    compared_records = []
    target_summaries = []

    for target in targets:
        records, resolved_format, source_info = _load_analysis_input(
            settings=settings,
            target=target,
            source=source,
            input_format=input_format,
            database=database,
            rettype=rettype,
        )
        analyzed_records = SequenceAnalyzer(min_orf_aa=min_orf_aa).analyze_records(records)

        for analyzed_record in analyzed_records:
            compared_records.append(analyzed_record | {"source": source_info})

        target_summaries.append(
            {
                "target": target,
                "source": source_info,
                "input_format": resolved_format,
                "record_count": len(analyzed_records),
            }
        )

    return {
        "target_count": len(targets),
        "record_count": len(compared_records),
        "targets": target_summaries,
        "records": compared_records,
        "comparison": compare_sequence_records(compared_records),
    }


def _render_compare_report(console: Console, report: dict, output: Path | None) -> None:
    comparison = report["comparison"]
    summary_lines = [
        f"Targets compared: {report['target_count']}",
        f"Records compared: {report['record_count']}",
        f"Molecule types: {', '.join(comparison['molecule_types'])}",
        f"Same molecule type: {str(comparison['all_same_molecule_type']).lower()}",
    ]

    console.print(Panel.fit("\n".join(summary_lines), title="Comparison Report"))
    console.print(_compare_records_table(report["records"]))
    highlight_table = _comparison_highlights_table(comparison)
    if highlight_table is not None:
        console.print(highlight_table)

    if output is not None:
        console.print(f"[green]JSON comparison report written to:[/green] {output}")


def _build_transform_report(
    *,
    settings,
    target: str,
    operation: str,
    source: str,
    input_format: str,
    database: str,
    rettype: str,
    frame: int,
    to_stop: bool,
    start: int,
    end: int,
) -> tuple[dict, str]:
    records, resolved_format, source_info = _load_analysis_input(
        settings=settings,
        target=target,
        source=source,
        input_format=input_format,
        database=database,
        rettype=rettype,
    )
    transformed_records, transform_meta = transform_records(
        records=records,
        operation=operation,
        frame=frame,
        to_stop=to_stop,
        start=start,
        end=None if end == 0 else end,
    )
    fasta_text = dump_records_to_text(transformed_records, output_format="fasta")
    report = {
        "source": source_info,
        "input_format": resolved_format,
        "operation": transform_meta["operation"],
        "parameters": transform_meta,
        "input_record_count": len(records),
        "output_record_count": len(transformed_records),
        "output_format": "fasta",
        "target": target,
    }
    return report, fasta_text


def _render_transform_output(
    *,
    console: Console,
    settings,
    report: dict,
    fasta_text: str,
    output: Path | None,
    stdout: bool,
    preview_lines: int,
) -> Path | None:
    if stdout:
        console.print(fasta_text)
        return None

    destination = output or default_transform_path(
        settings.output_dir,
        _transform_output_label(report["source"]),
        report["operation"],
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(fasta_text, encoding="utf-8")

    summary_lines = [
        f"Operation: {report['operation']}",
        f"Source: {report['source']['kind']}",
        f"Label: {report['source']['label']}",
        f"Input format: {report['input_format']}",
        f"Input records: {report['input_record_count']}",
        f"Output records: {report['output_record_count']}",
        f"Output format: {report['output_format']}",
        f"Output path: {destination}",
    ]
    console.print(Panel.fit("\n".join(summary_lines), title="Transform Output"))
    console.print(_transform_parameters_table(report["parameters"]))

    preview = _preview_text(fasta_text, preview_lines)
    if preview:
        console.print(Panel(preview, title="Preview", expand=False))

    return destination


def _run_remote_blast(
    *,
    console: Console,
    records,
    resolved_format: str,
    source_info: dict,
    program: str,
    blast_database: str,
    hitlist_size: int,
    expect: float,
    poll_interval: int,
    timeout_seconds: int,
) -> dict:
    if poll_interval < 60:
        raise ValueError("poll_interval must be at least 60 seconds to respect NCBI guidance.")
    if timeout_seconds < 1:
        raise ValueError("timeout_seconds must be at least 1.")

    query_kind, molecule_types = _resolve_blast_query_kind(records)
    resolved_program = _resolve_blast_program(program, query_kind=query_kind)
    resolved_blast_database = _resolve_blast_database(
        blast_database,
        program=resolved_program,
    )
    query_text = dump_records_to_text(records, output_format="fasta")
    client = _build_ncbi_client()

    with console.status("Submitting remote BLAST to NCBI...") as status:
        submission = client.blast_submit(
            program=resolved_program,
            database=resolved_blast_database,
            query=query_text,
            hitlist_size=hitlist_size,
            expect=expect,
        )
        search_info, elapsed_seconds, poll_count = _wait_for_remote_blast(
            client=client,
            status=status,
            submission=submission,
            poll_interval=poll_interval,
            timeout_seconds=timeout_seconds,
        )
        hits = []
        if search_info.status == "READY" and search_info.there_are_hits is not False:
            status.update(f"RID {submission.rid} is ready. Downloading BLAST results...")
            hits = client.blast_fetch_results(rid=submission.rid)

    query_records = [
        {
            "sequence_id": record.id,
            "description": record.description,
            "molecule_type": detect_molecule_type(record),
            "length": len(record.seq),
        }
        for record in records
    ]

    return {
        "source": source_info,
        "input_format": resolved_format,
        "query": {
            "record_count": len(records),
            "query_kind": query_kind,
            "molecule_types": molecule_types,
            "records": query_records,
        },
        "blast": {
            "rid": submission.rid,
            "program": submission.program,
            "database": submission.database,
            "status": search_info.status,
            "there_are_hits": search_info.there_are_hits,
            "estimated_time_seconds": submission.rtoe_seconds,
            "poll_interval_seconds": poll_interval,
            "timeout_seconds": timeout_seconds,
            "elapsed_seconds": elapsed_seconds,
            "poll_count": poll_count,
        },
        "hit_count": len(hits),
        "hits": blast_hits_to_dict(hits),
    }


def _wait_for_remote_blast(
    *,
    client: NcbiClient,
    status,
    submission,
    poll_interval: int,
    timeout_seconds: int,
) -> tuple[BlastSearchInfo, int, int]:
    start_time = time.monotonic()
    poll_count = 0
    next_poll_at = start_time + max(poll_interval, submission.rtoe_seconds)

    while True:
        now = time.monotonic()
        elapsed_seconds = int(now - start_time)
        if elapsed_seconds >= timeout_seconds:
            raise NcbiError(
                f"Remote BLAST job {submission.rid} did not finish within "
                f"{timeout_seconds} seconds."
            )

        remaining_seconds = max(0, int(next_poll_at - now))
        status.update(
            " | ".join(
                [
                    f"RID {submission.rid}",
                    f"estimated {submission.rtoe_seconds}s",
                    f"next check in {remaining_seconds}s",
                    f"elapsed {elapsed_seconds}s",
                ]
            )
        )

        if remaining_seconds > 0:
            time.sleep(min(1.0, float(remaining_seconds)))
            continue

        poll_count += 1
        search_info = client.blast_check_status(rid=submission.rid)
        if search_info.status == "READY":
            return search_info, elapsed_seconds, poll_count
        if search_info.status == "FAILED":
            raise NcbiError(f"Remote BLAST job {submission.rid} failed on NCBI.")
        if search_info.status == "UNKNOWN":
            raise NcbiError(f"Remote BLAST job {submission.rid} returned UNKNOWN status.")

        next_poll_at = time.monotonic() + poll_interval


def _render_batch_report(
    *,
    console: Console,
    report: dict,
    exported_path: Path | None,
    export_format: str | None,
) -> None:
    summary_lines = [
        f"Mode: {report['mode']}",
        f"Input kind: {report['input_kind']}",
        f"Targets file: {report['targets_file']}",
        f"Items processed: {report['total_items']}",
        f"Succeeded: {report['succeeded']}",
        f"Failed: {report['failed']}",
    ]
    console.print(Panel.fit("\n".join(summary_lines), title="Batch Summary"))

    table = Table(title="Batch Results")
    table.add_column("Item", style="cyan")
    table.add_column("Kind", style="green")
    table.add_column("Status", style="white")
    table.add_column("Result", style="magenta")
    table.add_column("Notes", style="white")

    for item in report["results"]:
        kind = item.get("source_kind", "-")
        status = item["status"]
        result_label = item.get("accession") or item.get("label") or "-"
        if item["operation"] == "analyze" and status == "ok":
            notes = (
                f"{_human_int(item.get('record_count'))} record(s), "
                f"{', '.join(item.get('molecule_types', [])) or '-'}"
            )
        elif item["operation"] == "fetch" and status == "ok":
            notes = item.get("saved_to", "-")
        else:
            notes = item.get("error", "-")

        table.add_row(
            str(item["item"])[:32],
            kind,
            status,
            str(result_label)[:40],
            str(notes)[:56],
        )

    console.print(table)

    if exported_path is not None and export_format is not None:
        console.print(
            f"[green]{export_format.upper()} batch report written to:[/green] {exported_path}"
        )


def _render_blast_report(
    *,
    console: Console,
    report: dict,
    exported_path: Path | None,
    export_format: str | None,
) -> None:
    blast_meta = report["blast"]
    query = report["query"]
    source = report["source"]
    summary_lines = [
        f"RID: {blast_meta['rid']}",
        f"Program: {blast_meta['program']}",
        f"BLAST database: {blast_meta['database']}",
        f"Status: {blast_meta['status']}",
        f"Source: {source['kind']}",
        f"Label: {source['label']}",
        f"Input format: {report['input_format']}",
        f"Query records: {query['record_count']}",
        f"Query kind: {query['query_kind']}",
        f"Elapsed: {blast_meta['elapsed_seconds']}s",
        f"Status checks: {blast_meta['poll_count']}",
    ]
    if blast_meta["estimated_time_seconds"]:
        summary_lines.append(f"NCBI estimate: {blast_meta['estimated_time_seconds']}s")
    console.print(Panel.fit("\n".join(summary_lines), title="Remote BLAST"))

    if report["hit_count"] == 0:
        console.print(
            Panel.fit(
                "BLAST completed successfully but returned no hits for this query.",
                title="BLAST Hits",
            )
        )
    else:
        console.print(_blast_hits_table(report["hits"]))

    if exported_path is not None and export_format is not None:
        console.print(f"[green]{export_format.upper()} export written to:[/green] {exported_path}")


def _blast_hits_table(hits: list[dict]) -> Table:
    table = Table(title="BLAST Hits")
    table.add_column("Query", style="cyan", no_wrap=True)
    table.add_column("Subject", style="green", no_wrap=True)
    table.add_column("% ID", justify="right")
    table.add_column("Align", justify="right")
    table.add_column("E-value", justify="right")
    table.add_column("Bit", justify="right")
    table.add_column("QCov", justify="right")
    table.add_column("Query Range", style="white")
    table.add_column("Subject Range", style="white")

    for hit in hits:
        query_range = f"{hit['query_start']}-{hit['query_end']}"
        subject_range = f"{hit['subject_start']}-{hit['subject_end']}"
        query_coverage = (
            _metric_value(hit["query_coverage"], suffix="%")
            if hit["query_coverage"] is not None
            else "-"
        )
        table.add_row(
            str(hit["query_id"])[:20],
            str(hit["subject_id"])[:20],
            f"{float(hit['percent_identity']):.2f}",
            _human_int(hit["alignment_length"]),
            str(hit["e_value"]),
            _metric_value(hit["bit_score"]),
            query_coverage,
            query_range,
            subject_range,
        )

    return table


def _resolve_blast_export_format(export_format: str, output: Path) -> str:
    normalized = export_format.strip().lower()
    if normalized == "auto":
        suffix = output.suffix.lower()
        if suffix in {".json", ".csv", ".tsv"}:
            return normalize_blast_export_format(suffix[1:])
        return "json"
    return normalize_blast_export_format(normalized)


def _resolve_report_export_format(export_format: str, output: Path) -> str:
    normalized = export_format.strip().lower()
    if normalized == "auto":
        suffix = output.suffix.lower()
        if suffix in {".json", ".csv"}:
            return normalize_report_export_format(suffix[1:])
        return "json"
    return normalize_report_export_format(normalized)


def _resolve_blast_query_kind(records) -> tuple[str, list[str]]:
    molecule_types = sorted({detect_molecule_type(record) for record in records})
    if not molecule_types or "UNKNOWN" in molecule_types:
        raise ValueError("BLAST query type could not be determined from the input records.")
    if set(molecule_types) <= {"DNA", "RNA"}:
        return "nucleotide", molecule_types
    if molecule_types == ["PROTEIN"]:
        return "protein", molecule_types
    raise ValueError("BLAST input cannot mix nucleotide and protein query records.")


def _resolve_blast_program(program: str, *, query_kind: str) -> str:
    normalized = program.strip().lower()
    if normalized in {"", "auto"}:
        return "blastp" if query_kind == "protein" else "blastn"

    allowed_for_query = {
        "protein": {"blastp", "tblastn"},
        "nucleotide": {"blastn", "blastx", "tblastx"},
    }
    if normalized not in allowed_for_query[query_kind]:
        allowed = ", ".join(sorted(allowed_for_query[query_kind]))
        raise ValueError(
            f"Program '{program}' is incompatible with a {query_kind} query. Use one of: {allowed}."
        )
    return normalized


def _resolve_blast_database(blast_database: str, *, program: str) -> str:
    normalized = blast_database.strip()
    if normalized and normalized.lower() != "auto":
        return normalized

    if program in {"blastp", "blastx"}:
        return "swissprot"
    return "core_nt"


def _write_text_export(
    *,
    settings,
    output: Path | None,
    default_output: Path,
    content: str,
) -> Path:
    destination = output or default_output
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination


def _build_analysis_report(
    *,
    records,
    resolved_format: str,
    source_info: dict,
    min_orf_aa: int,
    custom_motifs: list[str] | None = None,
) -> dict:
    analyzed_records = SequenceAnalyzer(
        min_orf_aa=min_orf_aa,
        custom_motifs=custom_motifs,
    ).analyze_records(records)
    _enrich_protein_analysis_records(analyzed_records, source_info)
    return {
        "source": source_info,
        "input_format": resolved_format,
        "record_count": len(analyzed_records),
        "records": analyzed_records,
    }


def _enrich_protein_analysis_records(records: list[dict], source_info: dict) -> None:
    enrichment_cache: dict[str, tuple[dict, dict | None]] = {}
    for record in records:
        if record.get("molecule_type") != "PROTEIN":
            continue

        accession = _protein_enrichment_accession(record, source_info)
        if not accession:
            continue

        if accession not in enrichment_cache:
            try:
                entry = fetch_uniprot_entry(accession)
                protein_context = extract_uniprot_protein_context(entry)
            except UniProtError:
                protein_context = {}

            try:
                alphafold_context = fetch_alphafold_prediction(accession)
            except AlphaFoldError:
                alphafold_context = None

            enrichment_cache[accession] = (protein_context, alphafold_context)

        protein_context, alphafold_context = enrichment_cache[accession]
        analysis = record.setdefault("analysis", {})
        domains = analysis.get("domains")
        if isinstance(domains, dict) and not domains.get("skipped"):
            external_domains = protein_context.get("domains", [])
            merged_domains = _merge_domain_lists(domains.get("all_domains", []), external_domains)
            domains["all_domains"] = merged_domains[:10]
            domains["domains_found"] = len(merged_domains)
            domains["uniprot_domains"] = len(external_domains)

        analysis["external"] = {
            "uniprot": protein_context or None,
            "alphafold": alphafold_context,
        }


def _protein_enrichment_accession(record: dict, source_info: dict) -> str | None:
    candidates = [
        source_info.get("accession"),
        record.get("sequence_id"),
        str(record.get("description", "")).split()[0] if record.get("description") else "",
    ]
    provider = str(source_info.get("provider", "")).strip().lower()

    for candidate in candidates:
        normalized = _normalize_uniprot_candidate(candidate)
        if normalized is not None:
            return normalized

    if provider == "uniprot":
        fallback = str(source_info.get("label") or "").strip()
        if fallback:
            return fallback

    return None


def _normalize_uniprot_candidate(value: object) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None

    token = text.split()[0]
    parts = [token]
    if "|" in token:
        parts.extend(part for part in token.split("|") if part)

    for part in parts:
        candidate = part.strip()
        if is_uniprot_accession(candidate):
            return candidate.upper()

    return None


def _merge_domain_lists(local_domains: list[dict], external_domains: list[dict]) -> list[dict]:
    merged = []
    seen = set()

    for item in local_domains + external_domains:
        key = (
            str(item.get("name")),
            item.get("start_aa"),
            item.get("end_aa"),
            str(item.get("source")),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)

    return merged


def _analyze_fetched_record(
    *,
    console: Console,
    record: FetchResult,
    min_orf_aa: int = 30,
) -> None:
    resolved_input_format = format_from_rettype(record.rettype)
    records, resolved_format = load_records_from_text(
        record.content,
        input_format=resolved_input_format,
    )
    report = _build_analysis_report(
        records=records,
        resolved_format=resolved_format,
        source_info={
            "kind": record.source,
            "label": record.accession,
            "accession": record.accession,
            "database": record.database,
            "provider": record.provider,
            "rettype": record.rettype,
        },
        min_orf_aa=min_orf_aa,
    )
    _render_analysis_report(
        console=console,
        report=report,
        exported_path=None,
        export_format=None,
    )


def _annotate_fetched_record(
    *,
    console: Console,
    record: FetchResult,
    feature_limit: int = 10,
) -> None:
    resolved_input_format = format_from_rettype(record.rettype)
    records, resolved_format = load_records_from_text(
        record.content,
        input_format=resolved_input_format,
    )
    report = build_annotation_report(
        records=records,
        input_format=resolved_format,
        source_info={
            "kind": record.source,
            "label": record.accession,
            "accession": record.accession,
            "database": record.database,
            "provider": record.provider,
            "rettype": record.rettype,
        },
        feature_limit=feature_limit,
    )
    _render_annotation_report(
        console=console,
        report=report,
        exported_path=None,
        export_format=None,
    )


def _blast_fetched_record(*, console: Console, record: FetchResult) -> None:
    resolved_input_format = format_from_rettype(record.rettype)
    records, resolved_format = load_records_from_text(
        record.content,
        input_format=resolved_input_format,
    )
    report = _run_remote_blast(
        console=console,
        records=records,
        resolved_format=resolved_format,
        source_info={
            "kind": record.source,
            "label": record.accession,
            "accession": record.accession,
            "database": record.database,
            "provider": record.provider,
            "rettype": record.rettype,
        },
        program="auto",
        blast_database="auto",
        hitlist_size=10,
        expect=10.0,
        poll_interval=60,
        timeout_seconds=1800,
    )
    _render_blast_report(
        console=console,
        report=report,
        exported_path=None,
        export_format=None,
    )


def _render_alphafold_lookup(console: Console, accession: str) -> None:
    prediction = fetch_alphafold_prediction(accession)
    if prediction is None:
        console.print(
            Panel.fit(
                f"No AlphaFold prediction was found for {accession}.",
                title="AlphaFold",
            )
        )
        return

    lines = [
        f"Accession: {prediction['accession']}",
        f"Model ID: {prediction['model_id']}",
        f"Entry: {prediction['entry_url']}",
    ]
    if prediction.get("avg_plddt") is not None:
        lines.append(f"Average pLDDT: {prediction['avg_plddt']}")
    if prediction.get("sequence_start") is not None and prediction.get("sequence_end") is not None:
        lines.append(
            f"Sequence range: {prediction['sequence_start']} - {prediction['sequence_end']}"
        )

    console.print(Panel.fit("\n".join(lines), title="AlphaFold Model"))


def _compare_records_table(records: list[dict]) -> Table:
    table = Table(title="Compared Records")
    table.add_column("Source", style="cyan")
    table.add_column("ID", style="white", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Length", justify="right")
    table.add_column("GC / MW", justify="right")
    table.add_column("ORFs / pI", justify="right")

    for record in records:
        stats = record["analysis"]["basic_stats"]
        molecule_type = record["molecule_type"]
        source_info = record.get("source", {})

        if molecule_type == "PROTEIN":
            gc_or_mw = _metric_value(stats.get("molecular_weight"), suffix=" Da")
            orf_or_pi = f"pI {_metric_value(stats.get('isoelectric_point'))}"
        else:
            gc_or_mw = _metric_value(stats.get("gc_content"), suffix="%")
            orf_or_pi = _human_int(record["analysis"]["orfs"].get("orfs_found"))

        table.add_row(
            _source_label(source_info),
            str(record["sequence_id"])[:24],
            molecule_type,
            _human_int(stats.get("length")),
            gc_or_mw,
            orf_or_pi,
        )

    return table


def _annotation_summary_table(records: list[dict]) -> Table:
    table = Table(title="Annotation Summary")
    table.add_column("Accession", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Length", justify="right")
    table.add_column("Organism", style="white")
    table.add_column("Genes", style="magenta")
    table.add_column("Features", justify="right")

    for record in records:
        table.add_row(
            str(record["accession"]),
            str(record["molecule_type"]),
            _human_int(record["sequence_length"]),
            str(record["organism"])[:28],
            ", ".join(record["gene_names"][:3]) or "-",
            _human_int(record["feature_count"]),
        )

    return table


def _annotation_metadata_table(record: dict) -> Table:
    table = Table(title=f"Record Metadata: {record['accession']}")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Sequence ID", str(record["sequence_id"]))
    table.add_row("Description", str(record["description"]))
    table.add_row("Molecule Type", str(record["molecule_type"]))
    table.add_row("Length", _human_int(record["sequence_length"]))
    table.add_row("Organism", str(record["organism"]))
    table.add_row("Topology", str(record["topology"]))
    table.add_row("Date", str(record["date"]))
    table.add_row("Keywords", ", ".join(record["keywords"]) or "-")
    table.add_row("Taxonomy", " > ".join(record["taxonomy"][:6]) or "-")
    table.add_row("Genes", ", ".join(record["gene_names"]) or "-")
    table.add_row("Products", ", ".join(record["product_names"][:5]) or "-")
    table.add_row("Feature Counts", _feature_counts_text(record["feature_counts"]) or "-")
    return table


def _annotation_features_table(features: list[dict]) -> Table | None:
    if not features:
        return None

    table = Table(title="Selected Features")
    table.add_column("Type", style="cyan")
    table.add_column("Location", style="white")
    table.add_column("Strand", justify="right")
    table.add_column("Qualifiers", style="magenta")

    for feature in features:
        table.add_row(
            str(feature["type"]),
            str(feature["location"]),
            str(feature["strand"] if feature["strand"] is not None else "-"),
            _feature_qualifiers_text(feature["qualifiers"]) or "-",
        )

    return table


def _comparison_highlights_table(comparison: dict) -> Table | None:
    table = Table(title="Comparison Highlights")
    table.add_column("Metric", style="cyan")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Delta", justify="right")

    rows_added = 0

    length = comparison.get("length")
    if length is not None:
        table.add_row(
            "Length",
            _metric_value(length.get("min")),
            _metric_value(length.get("max")),
            _metric_value(length.get("delta")),
        )
        rows_added += 1

    nucleotide = comparison.get("nucleotide")
    if nucleotide is not None:
        for label, key, suffix in [
            ("GC Content", "gc_content", "%"),
            ("ORF Count", "orf_count", ""),
            ("Restriction Hits", "restriction_site_hits", ""),
            ("CpG Dinucleotides", "cpg_dinucleotides", ""),
        ]:
            metric = nucleotide.get(key)
            if metric is None:
                continue
            table.add_row(
                label,
                _metric_value(metric.get("min"), suffix=suffix),
                _metric_value(metric.get("max"), suffix=suffix),
                _metric_value(metric.get("delta"), suffix=suffix),
            )
            rows_added += 1

    protein = comparison.get("protein")
    if protein is not None:
        for label, key, suffix in [
            ("Molecular Weight", "molecular_weight", " Da"),
            ("Isoelectric Point", "isoelectric_point", ""),
            ("Instability Index", "instability_index", ""),
        ]:
            metric = protein.get(key)
            if metric is None:
                continue
            table.add_row(
                label,
                _metric_value(metric.get("min"), suffix=suffix),
                _metric_value(metric.get("max"), suffix=suffix),
                _metric_value(metric.get("delta"), suffix=suffix),
            )
            rows_added += 1

    return table if rows_added else None


def _transform_parameters_table(parameters: dict) -> Table:
    table = Table(title="Transform Parameters")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="white")

    for key, value in parameters.items():
        if value is None:
            continue
        table.add_row(str(key), str(value))

    return table


def _analysis_summary_table(records: list[dict]) -> Table:
    table = Table(title="Sequence Summary")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Length", justify="right")
    table.add_column("GC / MW", justify="right")
    table.add_column("ORFs / pI", justify="right")
    table.add_column("Description", style="white")

    for record in records:
        stats = record["analysis"]["basic_stats"]
        molecule_type = record["molecule_type"]

        if molecule_type == "PROTEIN":
            gc_or_mw = _metric_value(stats.get("molecular_weight"), suffix=" Da")
            orf_or_pi = f"pI {_metric_value(stats.get('isoelectric_point'))}"
        else:
            gc_or_mw = _metric_value(stats.get("gc_content"), suffix="%")
            orf_or_pi = f"{_human_int(record['analysis']['orfs'].get('orfs_found'))} ORFs"

        table.add_row(
            str(record["sequence_id"])[:24],
            molecule_type,
            _human_int(stats.get("length")),
            gc_or_mw,
            orf_or_pi,
            str(record["description"])[:44],
        )

    return table


def _search_results_table(results, database: str) -> Table:
    table = Table(title=f"Search Results ({database})")
    table.add_column("Accession", style="cyan", no_wrap=True)
    table.add_column("Organism", style="green")
    table.add_column("Source", style="magenta")
    table.add_column("Length", justify="right")
    table.add_column("Title", style="white")

    for item in results:
        table.add_row(
            item.accession,
            item.organism,
            item.source_db,
            _human_int(item.length),
            item.title,
        )

    return table


def _render_single_record_details(console: Console, record: dict) -> None:
    console.print(
        Panel(
            record["description"],
            title=f"Record: {record['sequence_id']}",
            expand=False,
        )
    )
    stats = record["analysis"]["basic_stats"]
    console.print(_metric_table(record["molecule_type"], stats))
    warning_panel = _warnings_panel(record["analysis"].get("warnings", []))
    if warning_panel is not None:
        console.print(warning_panel)
    console.print(_composition_table(record["molecule_type"], stats))
    custom_motif_table = _custom_motif_table(record["analysis"].get("custom_motifs", []))
    if custom_motif_table is not None:
        console.print(custom_motif_table)

    if record["molecule_type"] in {"DNA", "RNA"}:
        console.print(_motif_table(record["analysis"]["motifs"]))
        orf_table = _orf_table(record["analysis"]["orfs"])
        if orf_table is not None:
            console.print(orf_table)
        longest_orf_panel = _longest_orf_panel(record["analysis"]["orfs"])
        if longest_orf_panel is not None:
            console.print(longest_orf_panel)
        codon_usage_table = _codon_usage_table(record["analysis"]["orfs"])
        if codon_usage_table is not None:
            console.print(codon_usage_table)
    else:
        domain_table = _protein_domains_table(record["analysis"].get("domains"))
        if domain_table is not None:
            console.print(domain_table)
        alphafold_panel = _alphafold_panel(record["analysis"].get("external", {}).get("alphafold"))
        if alphafold_panel is not None:
            console.print(alphafold_panel)


def _metric_table(molecule_type: str, stats: dict) -> Table:
    table = Table(title="Key Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Molecule Type", molecule_type)
    table.add_row("Length", _human_int(stats.get("length")))

    if molecule_type == "PROTEIN":
        for key in [
            "molecular_weight",
            "isoelectric_point",
            "instability_index",
            "gravy",
            "aromaticity",
            "is_stable",
        ]:
            if key in stats:
                suffix = " Da" if key == "molecular_weight" else ""
                table.add_row(key, _metric_value(stats[key], suffix=suffix))
    else:
        table.add_row("GC Content", _metric_value(stats.get("gc_content"), suffix="%"))
        table.add_row("AT Content", _metric_value(stats.get("at_content"), suffix="%"))
        table.add_row("N Count", _human_int(stats.get("n_count")))
        table.add_row("Ambiguous Bases", _human_int(stats.get("ambiguous_count")))
        table.add_row(
            "Ambiguous Content",
            _metric_value(stats.get("ambiguous_content"), suffix="%"),
        )
        if "melting_temp_tm" in stats:
            table.add_row("Melting Temp (Tm)", _metric_value(stats["melting_temp_tm"], suffix=" C"))

    return table


def _warnings_panel(warnings: list[str]) -> Panel | None:
    if not warnings:
        return None

    lines = "\n".join(f"- {warning}" for warning in warnings)
    return Panel.fit(lines, title="Warnings", border_style="yellow")


def _composition_table(molecule_type: str, stats: dict) -> Table:
    table = Table(title="Composition")
    table.add_column("Residue", style="magenta")
    table.add_column("Count", justify="right")

    composition = (
        stats.get("amino_acid_count", {})
        if molecule_type == "PROTEIN"
        else stats.get("base_composition", {})
    )
    for residue, count in composition.items():
        table.add_row(str(residue), _human_int(count))

    return table


def _motif_table(motifs: dict) -> Table:
    table = Table(title="Motif Review")
    table.add_column("Feature", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Restriction Sites Found", _human_int(len(motifs.get("restriction_sites", []))))
    table.add_row("Kozak Sequences", _human_int(len(motifs.get("kozak_sequences", []))))
    table.add_row("CpG Dinucleotides", _human_int(motifs.get("cpg_dinucleotides")))
    table.add_row("Approx. CpG Islands", _human_int(motifs.get("cpg_islands_approx")))

    restriction_sites = motifs.get("restriction_sites", [])
    if restriction_sites:
        top_hits = ", ".join(
            f"{item['enzyme']}({item['count']})" for item in restriction_sites[:5]
        )
        table.add_row("Top Restriction Hits", top_hits)

    return table


def _custom_motif_table(custom_motifs: list[dict]) -> Table | None:
    if not custom_motifs:
        return None

    table = Table(title="Custom Motifs")
    table.add_column("Motif", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Hits", justify="right")
    table.add_column("Positions", style="white")

    for item in custom_motifs:
        table.add_row(
            str(item["label"]),
            str(item["match_type"]),
            _human_int(item["count"]),
            _positions_preview(item.get("positions", [])),
        )

    return table


def _orf_table(orfs: dict) -> Table | None:
    all_orfs = orfs.get("all_orfs", [])
    if not all_orfs:
        return None

    table = Table(title=f"Top ORFs (min {orfs.get('min_orf_aa', '-')} aa)")
    table.add_column("Frame", style="cyan")
    table.add_column("Start", justify="right")
    table.add_column("End", justify="right")
    table.add_column("AA Length", justify="right")
    table.add_column("Preview", style="white")

    for item in all_orfs[:5]:
        table.add_row(
            str(item["frame"]),
            _human_int(item["start_nt"]),
            _human_int(item["end_nt"]),
            _human_int(item["length_aa"]),
            str(item["protein_preview"]),
        )

    return table


def _longest_orf_panel(orfs: dict) -> Panel | None:
    longest_orf = orfs.get("longest_orf")
    if not longest_orf:
        return None

    protein_sequence = str(longest_orf.get("protein_sequence", ""))
    preview = protein_sequence[:120] + ("..." if len(protein_sequence) > 120 else "")
    lines = [
        f"Frame: {longest_orf.get('frame', '-')}",
        f"Length: {_human_int(longest_orf.get('length_aa'))} aa",
        (
            f"Coords: {_human_int(longest_orf.get('start_nt'))} - "
            f"{_human_int(longest_orf.get('end_nt'))}"
        ),
        f"Translation: {preview or '-'}",
    ]
    return Panel.fit("\n".join(lines), title="Longest ORF Translation")


def _codon_usage_table(orfs: dict) -> Table | None:
    longest_orf = orfs.get("longest_orf")
    if not longest_orf:
        return None

    codon_usage = longest_orf.get("codon_usage") or {}
    if not codon_usage:
        return None

    table = Table(title="Longest ORF Codon Usage")
    table.add_column("Codon", style="cyan")
    table.add_column("Count", justify="right")

    for codon, count in list(codon_usage.items())[:8]:
        table.add_row(str(codon), _human_int(count))

    return table


def _positions_preview(positions: list[int]) -> str:
    if not positions:
        return "-"
    preview = ", ".join(str(position) for position in positions[:5])
    if len(positions) > 5:
        return f"{preview}, ..."
    return preview


def _protein_domains_table(domains: dict | None) -> Table | None:
    if not domains or domains.get("skipped"):
        return None

    all_domains = domains.get("all_domains", [])
    if not all_domains:
        return None

    table = Table(title="Protein Domains")
    table.add_column("Name", style="cyan")
    table.add_column("Start", justify="right")
    table.add_column("End", justify="right")
    table.add_column("Source", style="magenta")
    table.add_column("Evidence", style="white")

    for item in all_domains[:8]:
        table.add_row(
            str(item.get("name", "-")),
            _human_int(item.get("start_aa")),
            _human_int(item.get("end_aa")),
            str(item.get("source", "-")),
            str(item.get("evidence", "-")),
        )

    return table


def _alphafold_panel(prediction: dict | None) -> Panel | None:
    if not prediction:
        return None

    lines = [
        f"Model ID: {prediction.get('model_id', '-')}",
        f"Entry: {prediction.get('entry_url', '-')}",
    ]
    if prediction.get("avg_plddt") is not None:
        lines.append(f"Average pLDDT: {prediction['avg_plddt']}")
    if prediction.get("sequence_start") is not None and prediction.get("sequence_end") is not None:
        lines.append(
            f"Sequence range: {prediction['sequence_start']} - {prediction['sequence_end']}"
        )

    return Panel.fit("\n".join(lines), title="AlphaFold")


def _interactive_fetch_rettype(action: str, result) -> str:
    provider = str(getattr(result, "provider", "ncbi")).strip().lower()
    if provider == "ncbi" and action == "annotate":
        return "gb"
    return "fasta"


def _fetch_interactive_result(
    *,
    console: Console,
    settings,
    result,
    database: str,
    action: str,
) -> tuple[CacheStore | None, object | None, FetchResult]:
    provider = str(getattr(result, "provider", "ncbi")).strip().lower()
    rettype = _interactive_fetch_rettype(action, result)

    if provider == "ncbi":
        return _resolve_fetch(
            console=console,
            settings=settings,
            accession=result.accession,
            database=database,
            rettype=rettype,
            use_cache=True,
            refresh=False,
            save_cache=True,
        )

    if provider == "uniprot":
        return None, None, fetch_uniprot_fasta(result.accession)

    return None, None, fetch_kegg_sequence(result.accession)


def _run_interactive_search_flow(
    *,
    console: Console,
    settings,
    database: str,
    results,
) -> None:
    try:
        selected_result = pick_search_result(results)
        action = pick_post_search_action(selected_result)
    except InteractivePickerCancelled:
        console.print("[yellow]Interactive selection cancelled.[/yellow]")
        return
    except InteractivePickerError as exc:
        _fail(console, str(exc))
        return

    if action == "print_accession":
        console.print(selected_result.accession)
        return

    try:
        ensure_runtime_dirs(settings)
        cache_store, cache_record, record = _fetch_interactive_result(
            console=console,
            settings=settings,
            result=selected_result,
            database=database,
            action=action,
        )
    except (
        CacheError,
        KeggError,
        NcbiConfigurationError,
        NcbiError,
        UniProtError,
        ValueError,
    ) as exc:
        _fail(console, str(exc))
        return

    if action in {"fetch", "fetch_analyze"}:
        _render_fetch_output(
            console=console,
            settings=settings,
            cache_store=cache_store,
            cache_record=cache_record,
            record=record,
            accession=selected_result.accession,
            rettype=record.rettype,
            output=None,
            stdout=False,
            preview_lines=6,
        )

    if action in {"analyze", "fetch_analyze"}:
        _analyze_fetched_record(console=console, record=record, min_orf_aa=30)
        return

    if action == "annotate":
        _annotate_fetched_record(console=console, record=record, feature_limit=10)
        return

    if action == "blast":
        _blast_fetched_record(console=console, record=record)
        return

    if action == "alphafold":
        _render_alphafold_lookup(console, selected_result.accession)


def _source_label(source_info: dict) -> str:
    label = str(source_info.get("label", "-"))
    kind = str(source_info.get("kind", "")).lower()
    if kind == "file":
        return Path(label).name
    return label


def _transform_output_label(source_info: dict) -> str:
    label = str(source_info.get("label", "transformed"))
    kind = str(source_info.get("kind", "")).lower()
    if kind == "file":
        return Path(label).stem
    return label


def _annotation_output_label(source_info: dict) -> str:
    label = str(source_info.get("label", "annotation"))
    kind = str(source_info.get("kind", "")).lower()
    if kind == "file":
        return Path(label).stem
    return label


def _feature_counts_text(feature_counts: dict[str, int]) -> str:
    return ", ".join(f"{name}:{count}" for name, count in feature_counts.items())


def _feature_qualifiers_text(qualifiers: dict[str, str]) -> str:
    return "; ".join(f"{key}={value}" for key, value in qualifiers.items())


def _human_int(value) -> str:
    if value in (None, "-"):
        return "-"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def _metric_value(value, *, suffix: str = "") -> str:
    if value in (None, "-"):
        return "-"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}{suffix}"
    if isinstance(value, float):
        return f"{value:,.2f}{suffix}"
    return f"{value}{suffix}"


def _human_size(size_bytes: int | None) -> str:
    if size_bytes in (None, 0):
        return "0 B" if size_bytes == 0 else "-"

    units = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size_bytes} B"
