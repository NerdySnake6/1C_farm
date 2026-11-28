"""Fail-closed validation of Vanessa's JUnit evidence, without launching 1C."""
from pathlib import Path
import tempfile
import json
import subprocess
import sys
import unittest

from run_vanessa_tests import ROOT, validate_reports, scenario_results


class VanessaReportsTest(unittest.TestCase):
    def test_table_preserves_individual_results_and_failure_reason(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / "suite.xml").write_text(
                '<testsuite><testcase name="VA01 Ready" time="1.5"/>'
                '<testcase name="VA02 Repeat"><failure message="Expected 41">Got 40</failure></testcase>'
                '<testcase name="VA03 Reset"><skipped message="No client"/></testcase></testsuite>',
                encoding="utf-8")
            results = scenario_results(path)
            self.assertEqual([row["status"] for row in results], ["passed", "failed", "skipped"])
            self.assertEqual(results[0]["code"], "VA01")
            self.assertEqual(results[0]["duration"], "1.5")
            self.assertIn("Got 40", results[1]["detail"])
            self.assertIn("Expected 41", results[1]["detail"])
            self.assertEqual(results[2]["detail"], "No client")
            with self.assertRaises(RuntimeError):
                validate_reports(path)

    def test_expanded_suite_cannot_pass_with_only_old_scenarios(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            report = path / "suite.xml"
            for count in (3, 6, 10, 14):
                report.write_text('<testsuite>' + ''.join(
                    f'<testcase name="VA{index:02d}"/>' for index in range(1, count + 1)) + '</testsuite>', encoding="utf-8")
                with self.assertRaises(RuntimeError):
                    validate_reports(path, expected=18)
            report.write_text('<testsuite>' + ''.join(
                f'<testcase name="VA{index:02d}"/>' for index in range(1, 19)) + '</testsuite>', encoding="utf-8")
            self.assertEqual(len(validate_reports(path, expected=18)), 18)

    def test_native_launcher_receives_preflight_failure(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as folder:
            result = Path(folder) / "result.json"
            process = subprocess.run([sys.executable, str(ROOT / "scripts/run_vanessa_tests.py"),
                                      "--app", str(Path(folder) / "missing.exe"),
                                      "--ui-result", str(result)], capture_output=True, timeout=10)
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual(json.loads(result.read_text(encoding="utf-8"))["status"], "failed")

    def test_complete_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / "suite.xml").write_text(
                '<testsuite><testcase name="VA01"/><testcase name="VA02"/>'
                '<testcase name="VA03"/></testsuite>', encoding="utf-8")
            self.assertEqual(validate_reports(path), ["VA01", "VA02", "VA03"])

    def test_reject_incomplete_or_failed_evidence(self):
        reports = ["<testsuite/>", '<testsuite><testcase name="VA01"/></testsuite>',
                   '<testsuite><testcase name="VA01"/><testcase name="VA01"/>'
                   '<testcase name="VA03"/></testsuite>']
        for status in ("failure", "error", "skipped"):
            reports.append(f'<testsuite><testcase name="VA01"><{status}/></testcase>'
                           '<testcase name="VA02"/><testcase name="VA03"/></testsuite>')
        for body in reports:
            with self.subTest(body=body), tempfile.TemporaryDirectory() as folder:
                path = Path(folder)
                (path / "suite.xml").write_text(body, encoding="utf-8")
                with self.assertRaises(RuntimeError):
                    validate_reports(path)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuntimeError):
                validate_reports(Path(folder))


if __name__ == "__main__":
    unittest.main()
