import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.exporters import (  # noqa: E402
    render_analysis_export,
    render_annotation_export,
    render_batch_export,
    render_blast_export,
)

ANALYSIS_REPORT = {
    "source": {"kind": "file", "label": "/tmp/example.fasta"},
    "input_format": "fasta",
    "record_count": 1,
    "records": [
        {
            "sequence_id": "seqA",
            "description": "Example sequence",
            "molecule_type": "DNA",
            "analysis": {
                "basic_stats": {
                    "length": 18,
                    "gc_content": 50.0,
                    "at_content": 50.0,
                    "n_count": 0,
                    "ambiguous_count": 0,
                    "ambiguous_content": 0.0,
                    "melting_temp_tm": 54.0,
                },
                "motifs": {
                    "restriction_sites": [{"enzyme": "EcoRI", "count": 1}],
                    "kozak_sequences": [{"position": 0, "sequence": "GCCACCATGG"}],
                    "cpg_dinucleotides": 2,
                },
                "orfs": {
                    "orfs_found": 1,
                    "longest_orf": {
                        "frame": "+1",
                        "length_aa": 5,
                        "protein_sequence": "MELKI",
                        "codon_usage": {"ATG": 1, "GAA": 1},
                    },
                },
                "domains": {
                    "domains_found": 2,
                    "all_domains": [
                        {"name": "Example domain", "start_aa": 2, "end_aa": 14},
                        {"name": "UniProt repeat", "start_aa": 20, "end_aa": 30},
                    ],
                },
                "external": {
                    "alphafold": {
                        "model_id": "AF-P69905-F1",
                        "avg_plddt": 91.2,
                    }
                },
                "custom_motifs": [{"label": "GAATTC", "count": 1}],
                "warnings": ["Sequence is short; motif and ORF signals may be limited."],
            },
        }
    ],
}

ANNOTATION_REPORT = {
    "source": {"kind": "file", "label": "/tmp/example.gb"},
    "input_format": "genbank",
    "record_count": 1,
    "feature_limit": 5,
    "records": [
        {
            "sequence_id": "gb1",
            "accession": "ABC123",
            "description": "Example GenBank record",
            "input_format": "genbank",
            "molecule_type": "DNA",
            "sequence_length": 39,
            "organism": "Bacillus subtilis",
            "taxonomy": ["Bacteria", "Firmicutes"],
            "keywords": ["sporulation"],
            "topology": "linear",
            "date": "19-APR-2026",
            "source": "Bacillus subtilis",
            "gene_names": ["spoIIIAA"],
            "product_names": ["stage III sporulation protein AA"],
            "feature_count": 3,
            "feature_counts": {"CDS": 1, "gene": 1, "source": 1},
            "selected_features": [
                {
                    "type": "gene",
                    "location": "[0:39]",
                    "strand": 1,
                    "qualifiers": {"gene": "spoIIIAA"},
                }
            ],
        }
    ],
}

BLAST_REPORT = {
    "source": {"kind": "file", "label": "/tmp/query.fasta"},
    "input_format": "fasta",
    "query": {
        "record_count": 1,
        "query_kind": "protein",
        "molecule_types": ["PROTEIN"],
        "records": [
            {
                "sequence_id": "queryA",
                "description": "Example",
                "molecule_type": "PROTEIN",
                "length": 147,
            }
        ],
    },
    "blast": {
        "rid": "TEST-RID-001",
        "program": "blastp",
        "database": "swissprot",
        "status": "READY",
        "there_are_hits": True,
        "estimated_time_seconds": 24,
        "poll_interval_seconds": 60,
        "timeout_seconds": 1800,
        "elapsed_seconds": 60,
        "poll_count": 1,
    },
    "hit_count": 1,
    "hits": [
        {
            "query_id": "queryA",
            "subject_id": "P68871.2",
            "percent_identity": 100.0,
            "alignment_length": 147,
            "mismatches": 0,
            "gap_opens": 0,
            "query_start": 1,
            "query_end": 147,
            "subject_start": 1,
            "subject_end": 147,
            "e_value": "5.82e-106",
            "bit_score": 301.0,
            "query_coverage": 100.0,
        }
    ],
}

BATCH_REPORT = {
    "mode": "analyze",
    "input_kind": "files",
    "targets_file": "/tmp/targets.txt",
    "database": "nucleotide",
    "rettype": "fasta",
    "total_items": 1,
    "succeeded": 1,
    "failed": 0,
    "results": [
        {
            "item": "seq_a.fasta",
            "status": "ok",
            "operation": "analyze",
            "source_kind": "file",
            "label": "/tmp/seq_a.fasta",
            "input_format": "fasta",
            "record_count": 1,
            "molecule_types": ["DNA"],
            "analysis": ANALYSIS_REPORT,
        }
    ],
}


class ExporterTests(unittest.TestCase):
    def test_renders_analysis_csv(self) -> None:
        csv_text = render_analysis_export(ANALYSIS_REPORT, "csv")
        self.assertIn("source_kind,source_label,input_format,sequence_id", csv_text)
        self.assertIn("ambiguous_count", csv_text)
        self.assertIn("custom_motifs", csv_text)
        self.assertIn("domains_found", csv_text)
        self.assertIn("alphafold_model_id", csv_text)
        self.assertIn("seqA", csv_text)
        self.assertIn("GAATTC(1)", csv_text)
        self.assertIn("ATG:1; GAA:1", csv_text)
        self.assertIn("Example domain", csv_text)
        self.assertIn("AF-P69905-F1", csv_text)

    def test_renders_csv(self) -> None:
        csv_text = render_annotation_export(ANNOTATION_REPORT, "csv")
        self.assertIn("accession,sequence_id,description", csv_text)
        self.assertIn("ABC123", csv_text)
        self.assertIn("spoIIIAA", csv_text)

    def test_renders_markdown(self) -> None:
        markdown = render_annotation_export(ANNOTATION_REPORT, "markdown")
        self.assertIn("# Annotation Report", markdown)
        self.assertIn("## ABC123", markdown)
        self.assertIn("spoIIIAA", markdown)

    def test_renders_html(self) -> None:
        html = render_annotation_export(ANNOTATION_REPORT, "html")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Annotation Report", html)
        self.assertIn("ABC123", html)

    def test_renders_blast_csv(self) -> None:
        csv_text = render_blast_export(BLAST_REPORT, "csv")
        self.assertIn("rid,program,blast_database", csv_text)
        self.assertIn("TEST-RID-001", csv_text)
        self.assertIn("P68871.2", csv_text)

    def test_renders_blast_tsv(self) -> None:
        tsv_text = render_blast_export(BLAST_REPORT, "tsv")
        self.assertIn("rid\tprogram\tblast_database", tsv_text)
        self.assertIn("queryA\tP68871.2", tsv_text)

    def test_renders_batch_csv(self) -> None:
        csv_text = render_batch_export(BATCH_REPORT, "csv")
        self.assertIn("item,operation,status,source_kind,source_label", csv_text)
        self.assertIn("warning_count", csv_text)
        self.assertIn("seq_a.fasta", csv_text)
        self.assertIn("seqA", csv_text)


if __name__ == "__main__":
    unittest.main()
