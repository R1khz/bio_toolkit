from __future__ import annotations

from pathlib import Path

import typer

from bio_toolkit.config import refresh_settings
from bio_toolkit.exporters import render_blast_export
from bio_toolkit.services.blast import BlastRequest, run_blast

from ..completions import complete_cached_accession
from ..presenters.blast_presenter import render_blast_response
from ..presenters.common import resolve_blast_export_format, write_text_export
from .common import fail, get_console

BLAST_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional export file path for BLAST output.",
)


def register(app: typer.Typer) -> None:
    @app.command(help="Run remote BLAST searches from local or cached queries.")
    def blast(
        ctx: typer.Context,
        target: str = typer.Argument(
            ...,
            help="Local sequence file path or cached accession to submit as the BLAST query.",
            autocompletion=complete_cached_accession,
        ),
        source: str = typer.Option(
            "auto", "--source", "-s", help="Input source: auto, file, or cache."
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
            help="Remote BLAST database. Defaults to core_nt or swissprot based on query type.",
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
        console = get_console(ctx)
        try:
            settings = refresh_settings()
            if output is None and export_format.strip().lower() != "auto":
                fail(console, "Use --output together with --export-format.")
                return

            with console.status("Submitting remote BLAST to NCBI...") as status:
                response = run_blast(
                    BlastRequest(
                        target=target,
                        source=source,
                        input_format=input_format,
                        cache_database=cache_database,
                        cache_rettype=cache_rettype,
                        program=program,
                        blast_database=blast_database,
                        hitlist_size=hitlist_size,
                        expect=expect,
                        poll_interval=poll_interval,
                        timeout_seconds=timeout_seconds,
                    ),
                    settings=settings,
                    status=status,
                )
        except Exception as exc:
            fail(console, str(exc))
            return

        normalized_export_format = None
        exported_path = None
        if output is not None:
            normalized_export_format = resolve_blast_export_format(export_format, output)
            exported_path = write_text_export(
                output=output,
                default_output=output,
                content=render_blast_export(response.model_dump(), normalized_export_format),
            )

        render_blast_response(
            console=console,
            response=response,
            as_json=as_json,
            exported_path=exported_path,
            export_format=normalized_export_format,
        )
