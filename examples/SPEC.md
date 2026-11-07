# UTC timestamp utility

Build a Python command-line utility, `utc.py`, that converts an ISO 8601
timestamp with an explicit UTC offset to UTC. The target is a small existing
Git repository; use only the Python standard library.

## Acceptance criteria

- `python3 utc.py 2026-11-07T12:00:00+08:00` prints exactly
  `2026-11-07T04:00:00Z` followed by a newline and exits 0.
- `python3 utc.py 2026-11-07T04:00:00Z` preserves that UTC value and exits 0.
- A timestamp without a time zone is rejected with a useful stderr message
  and nonzero exit status.
- Invalid input is rejected without a Python traceback.
- `--help` describes usage and exits 0.
- Document installation, usage and unsupported input forms.

Do not add network requests, runtime dependencies, deployment, secrets or
changes to the external acceptance harness. Add appropriate project tests.
CLI subprocess evidence is sufficient; this task has no graphical interface.
