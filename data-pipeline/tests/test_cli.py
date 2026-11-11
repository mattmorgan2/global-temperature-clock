"""Verify the installed entry point clearly reports its unfinished status."""

import subprocess
import sys
import unittest


class CliTests(unittest.TestCase):
    def test_status_does_not_claim_to_calculate_temperatures(self):
        result = subprocess.run(
            [sys.executable, "-m", "temperature_pipeline", "--status"],
            check=True, capture_output=True, text=True,
        )
        self.assertIn("Scaffold only", result.stdout)
        self.assertIn("methodology are pending", result.stdout)


if __name__ == "__main__":
    unittest.main()
