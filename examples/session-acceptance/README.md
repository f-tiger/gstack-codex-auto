# Conversation-mode acceptance example

This directory contains the actual result of the 2026-11-08 in-session acceptance
task, not a fake model response. The current assistant read the installed
`gstack-codex-auto` skill, planned and implemented a UTC conversion CLI in a
separate Git repository, exercised it with subprocess tests, and repaired an
explicitly injected fractional-precision fault. No nested model CLI was used.

`completed-task/` is a snapshot of the resulting code, documentation and unit
tests. `verify.py` is the external harness written and hashed before the
implementation. It was not changed to make the implementation pass. Both were
authored in the same assistant session; this is not independent verification.

## Replay the final functional checks

From the repository root:

```bash
cd examples/session-acceptance/completed-task
python3 -m unittest discover -s tests -v
python3 ../verify.py
python3 ../../acceptance.py
```

Expected: six unit tests, nine external contract test methods (including a
40-case deterministic offset sweep), and four original acceptance tests pass.
Python 3.11+ is required; no dependencies, network or Codex CLI are needed to
replay these product tests. Replaying them does not rerun an AI development task.

For a new live skill trial, use a separate target repository containing only a
README and unrelated draft, and ask the assistant to implement the task described
in `../SPEC.md`. The acceptance extension for this recorded trial is strict ASCII
`YYYY-MM-DDTHH:MM:SS[.1–6 digits](Z|±HH:MM)` input; validate offset hour/minute
bounds, reject UTC year overflow, normalize nonzero fractions to six digits, and
return exit 2 with stderr/no stdout for invalid input. Keep this harness outside
the target and preserve its hash. Do not provide the completed solution as input.

See [the acceptance report](../../docs/session-acceptance.md) for the observed
failure, repair, checkpoint replay, preserved unrelated edit and limitations.
