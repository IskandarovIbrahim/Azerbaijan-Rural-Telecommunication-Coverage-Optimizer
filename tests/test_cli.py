"""Offline smoke tests for the installed CLI."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from coverage_optimizer.cli import main


class CheckConfigTests(unittest.TestCase):
    def test_loads_provisional_pilot(self) -> None:
        path = Path(__file__).resolve().parents[1] / "config" / "quba-pilot.json"
        output = StringIO()

        with redirect_stdout(output):
            exit_code = main(["check-config", str(path)])

        self.assertEqual(exit_code, 0)
        self.assertIn("Xınalıq, Quba District, Azerbaijan", output.getvalue())
        self.assertIn("Study area center is unverified.", output.getvalue())
        self.assertIn("Radio assumptions are unverified.", output.getvalue())

    def test_invalid_config_reports_error(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-invalid.json"
            path.write_text('{"schema_version": 1}', encoding="utf-8")
            errors = StringIO()

            with redirect_stderr(errors), self.assertRaises(SystemExit) as raised:
                main(["check-config", str(path)])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("study_area and scenario must be JSON objects", errors.getvalue())
