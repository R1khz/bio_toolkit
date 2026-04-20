import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.interactive_picker import format_search_choice  # noqa: E402
from bio_toolkit.ncbi import SearchResult  # noqa: E402


class InteractivePickerTests(unittest.TestCase):
    def test_format_search_choice_is_readable(self) -> None:
        result = SearchResult(
            accession="NP_123456.1",
            title="Example sporulation protein",
            organism="Bacillus subtilis",
            source_db="refseq",
            uid="1",
            length=742,
        )

        rendered = format_search_choice(result)

        self.assertIn("NP_123456.1", rendered)
        self.assertIn("Bacillus subtilis", rendered)
        self.assertIn("742", rendered)
        self.assertIn("Example sporulation protein", rendered)


if __name__ == "__main__":
    unittest.main()
