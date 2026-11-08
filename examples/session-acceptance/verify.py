"""External functional acceptance. Run from the target containing utc.py.

No model fixtures: every probe executes the real target CLI with synthetic data.
The current assistant authors the task and harness; this is not an independent audit.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import random
import subprocess
import sys
import unittest


class UTCContract(unittest.TestCase):
    def invoke(self, *arguments, tz="UTC"):
        return subprocess.run([sys.executable, "utc.py", *arguments],
                              capture_output=True, text=True, timeout=5,
                              env={**os.environ, "TZ": tz, "PYTHONDONTWRITEBYTECODE": "1"})

    def assert_conversion(self, value, expected, tz="UTC"):
        result = self.invoke(value, tz=tz)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, expected + "\n")
        self.assertEqual(result.stderr, "")

    def test_basic_offsets(self):
        for value, expected in [
            ("2026-11-07T12:00:00+08:00", "2026-11-07T04:00:00Z"),
            ("2026-11-07T04:00:00Z", "2026-11-07T04:00:00Z"),
            ("2026-11-07T04:00:00-03:30", "2026-11-07T07:30:00Z"),
            ("2026-11-07T04:00:00+00:00", "2026-11-07T04:00:00Z"),
        ]:
            with self.subTest(value=value):
                self.assert_conversion(value, expected)

    def test_calendar_boundaries(self):
        for value, expected in [
            ("2024-03-01T00:15:00+01:00", "2024-02-29T23:15:00Z"),
            ("2026-01-01T00:00:00+01:00", "2025-12-31T23:00:00Z"),
            ("2026-12-31T23:30:00-01:00", "2027-01-01T00:30:00Z"),
            ("0001-01-01T00:00:00Z", "0001-01-01T00:00:00Z"),
            ("9999-12-31T23:59:59Z", "9999-12-31T23:59:59Z"),
        ]:
            with self.subTest(value=value):
                self.assert_conversion(value, expected)

    def test_fractional_seconds(self):
        for value, expected in [
            ("2026-11-07T12:00:00.123456+08:00", "2026-11-07T04:00:00.123456Z"),
            ("2026-11-07T12:00:00.1+08:00", "2026-11-07T04:00:00.100000Z"),
            ("2026-11-07T12:00:00.000000+08:00", "2026-11-07T04:00:00Z"),
        ]:
            with self.subTest(value=value):
                self.assert_conversion(value, expected)

    def test_rejects_invalid_input(self):
        values = ["not-a-date", "", "2026-11-07T04:00:00", "2026-02-30T00:00:00Z",
                  "2026-11-07T04:00:60Z", "2026-11-07T24:00:00Z",
                  "2026-11-07T04:00:00+24:00", "2026-11-07T04:00:00+08:60",
                  "2026-11-07T04:00:00+00:00:30", "2026-11-07T04:00:00.1234567Z",
                  "2026-11-07 04:00:00Z", "2026-11-07T04:00:00z",
                  "２０２６-11-07T04:00:00Z", "2026-11-07T04:00:00Z\n",
                  "0001-01-01T00:00:00+01:00", "9999-12-31T23:59:59-01:00"]
        for value in values:
            with self.subTest(value=value):
                result = self.invoke(value)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.strip())
                self.assertNotIn("Traceback", result.stderr)

    def test_argument_contract(self):
        for arguments in [(), ("a", "b"), ("--unknown",)]:
            with self.subTest(arguments=arguments):
                result = self.invoke(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("Traceback", result.stderr)

    def test_help(self):
        result = self.invoke("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage", result.stdout.lower())
        self.assertEqual(result.stderr, "")

    def test_host_timezone_independence(self):
        for tz in ["UTC", "America/Los_Angeles", "Asia/Shanghai"]:
            with self.subTest(tz=tz):
                self.assert_conversion("2026-11-07T12:00:00+08:00", "2026-11-07T04:00:00Z", tz)

    def test_deterministic_offset_sweep(self):
        rng = random.Random(20261108)
        for i in range(40):
            utc = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=rng.randrange(90_000_000))
            minutes = rng.randrange(-1439, 1440)
            local = utc.astimezone(timezone(timedelta(minutes=minutes)))
            with self.subTest(case=i, offset_minutes=minutes):
                self.assert_conversion(local.isoformat(), utc.isoformat().replace("+00:00", "Z"))

    def test_no_filesystem_writes(self):
        def snapshot():
            return {str(p): p.read_bytes() for p in Path('.').rglob('*')
                    if p.is_file() and '.git' not in p.parts}
        before = snapshot()
        self.assert_conversion("2026-11-07T12:00:00+08:00", "2026-11-07T04:00:00Z")
        self.invoke("invalid")
        self.assertEqual(snapshot(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
