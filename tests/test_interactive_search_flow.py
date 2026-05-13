from types import SimpleNamespace
from unittest.mock import patch

from rich.console import Console

from bio_toolkit.cli.interactive.search_flow import run_interactive_search_flow
from bio_toolkit.contracts.fetch.models import FetchedRecord
from bio_toolkit.services.fetch.response import FetchResponse


def test_interactive_search_flow_can_analyze_ncbi_fetch_response() -> None:
    result = SimpleNamespace(
        accession="NM_001284353",
        title="Example transcript",
        organism="Homo sapiens",
        source_db="NCBI:nucleotide",
        uid="NM_001284353",
        length=100,
        provider="ncbi",
        database="nucleotide",
    )
    response = FetchResponse(
        accession="NM_001284353",
        cache_hit=False,
        record=FetchedRecord(
            accession="NM_001284353",
            database="nucleotide",
            rettype="fasta",
            source="ncbi",
            provider="ncbi",
            content=">NM_001284353\nATGAAATAGAAA\n",
        ),
        cache_path=None,
    )
    console = Console(record=True)

    with patch(
        "bio_toolkit.cli.interactive.search_flow.pick_search_result",
        return_value=result,
    ):
        with patch(
            "bio_toolkit.cli.interactive.search_flow.pick_post_search_action",
            return_value="analyze",
        ):
            with patch("bio_toolkit.cli.interactive.search_flow.ensure_runtime_dirs"):
                with patch(
                    "bio_toolkit.cli.interactive.search_flow.run_fetch",
                    return_value=response,
                ):
                    with patch(
                        "bio_toolkit.cli.interactive.search_flow.render_analysis_response"
                    ) as render_analysis:
                        run_interactive_search_flow(
                            console=console,
                            settings=SimpleNamespace(),
                            database="nucleotide",
                            results=[result],
                        )

    render_analysis.assert_called_once()
