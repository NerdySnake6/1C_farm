"""Check that the runner cannot accept missing, duplicated or failed assertions."""
import unittest
from run_defense_tests import validate_report


class ReportValidationTests(unittest.TestCase):
    expected = {'B01', 'B02'}
    valid = 'PASS | B01 first\nPASS | B02 second\nCOMPLETE\n'

    def test_complete_report(self):
        self.assertEqual(validate_report('\ufeff' + self.valid, self.expected)['passed'], 2)

    def test_rejects_broken_reports(self):
        cases = {
            'empty': '',
            'missing_complete': self.valid.replace('COMPLETE', ''),
            'missing_assertion': self.valid.replace('PASS | B02 second\n', ''),
            'duplicate': 'PASS | B01 again\n' + self.valid,
            'unexpected': 'PASS | B03 extra\n' + self.valid,
            'failure': self.valid.replace('PASS | B02', 'FAIL | B02'),
            'cleanup_error': self.valid + 'ERROR | cleanup failed\n',
            'double_complete': self.valid + 'COMPLETE\n',
            'garbage': 'broken\n' + self.valid,
        }
        for name, body in cases.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_report(body, self.expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
