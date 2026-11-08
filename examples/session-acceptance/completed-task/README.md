# UTC utility

Convert an offset-aware timestamp to UTC with Python 3.11+ and no dependencies.

```bash
python3 utc.py 2026-11-07T12:00:00+08:00
# 2026-11-07T04:00:00Z
python3 utc.py --help
python3 -m unittest discover -s tests -v
```

Accepted syntax: `YYYY-MM-DDTHH:MM:SS[.fraction](Z|±HH:MM)` using ASCII digits,
uppercase T/Z, and one to six optional fractional digits. Offsets must have
hours 00–23 and minutes 00–59; the date/time and resulting UTC year must be valid.
Naive timestamps, space separators, leap seconds, offset seconds, lowercase z,
more than six fractional digits and values outside years 0001–9999 are rejected.

Successful conversion writes one UTC timestamp plus a newline to stdout and
exits 0. Nonzero fractions are normalized to six digits; zero fractions are
omitted. Invalid input writes a useful error to stderr, leaves stdout empty and
exits 2 without a traceback. `--help` exits 0. The tool uses no network and writes
no files. Results do not depend on the host timezone.
