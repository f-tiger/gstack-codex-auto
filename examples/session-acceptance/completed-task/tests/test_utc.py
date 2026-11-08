import unittest

from utc import to_utc


class ConversionTests(unittest.TestCase):
    def test_offset_and_rollover(self):
        self.assertEqual(to_utc("2026-01-01T00:30:00+01:00"), "2025-12-31T23:30:00Z")

    def test_utc_is_idempotent(self):
        value = "2026-11-07T04:00:00.123456Z"
        self.assertEqual(to_utc(to_utc(value)), value)

    def test_fraction_value_preserved(self):
        self.assertEqual(to_utc("2026-11-07T12:00:00.1+08:00"), "2026-11-07T04:00:00.100000Z")

    def test_bad_offset_is_not_normalized(self):
        with self.assertRaises(ValueError):
            to_utc("2026-11-07T12:00:00+08:60")

    def test_timezone_required(self):
        with self.assertRaises(ValueError):
            to_utc("2026-11-07T12:00:00")

    def test_utc_underflow_is_useful_error(self):
        with self.assertRaisesRegex(ValueError, "outside years"):
            to_utc("0001-01-01T00:00:00+01:00")
