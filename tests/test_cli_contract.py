import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLI_FILE = ROOT / "src" / "bio_toolkit" / "cli.py"


class CliContractTests(unittest.TestCase):
    def test_cli_registers_expected_commands(self) -> None:
        module = ast.parse(CLI_FILE.read_text())
        commands = set()

        for node in module.body:
            if not isinstance(node, ast.FunctionDef):
                continue

            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if isinstance(decorator.func.value, ast.Name) and decorator.func.value.id == "app":
                        if decorator.func.attr == "command":
                            commands.add(node.name)

        self.assertEqual(
            commands,
            {"doctor", "search", "fetch", "batch", "analyze", "annotate", "compare", "transform", "blast", "cache"},
        )

    def test_cli_has_plain_option_in_callback(self) -> None:
        source = CLI_FILE.read_text()
        self.assertIn("--plain", source)
        self.assertIn("--pick", source)


if __name__ == "__main__":
    unittest.main()
