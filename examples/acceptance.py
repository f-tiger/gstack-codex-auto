"""Run from a candidate worktree; keep this trusted harness outside it."""
import subprocess
import sys
import unittest


class Acceptance(unittest.TestCase):
    def invoke(self, value):
        return subprocess.run([sys.executable, "utc.py", value], capture_output=True,
                              text=True, timeout=10)

    def test_offset(self):
        result = self.invoke("2026-11-07T12:00:00+08:00")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "2026-11-07T04:00:00Z\n")

    def test_utc(self):
        result = self.invoke("2026-11-07T04:00:00Z")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "2026-11-07T04:00:00Z\n")

    def test_bad_input(self):
        for value in ("2026-11-07T04:00:00", "not-a-date"):
            result = self.invoke(value)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(result.stderr.strip())
            self.assertNotIn("Traceback", result.stderr)

    def test_help(self):
        result = self.invoke("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
