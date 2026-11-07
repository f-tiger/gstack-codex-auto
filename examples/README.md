# First live trial

The example spec is for a small Python CLI with an external acceptance harness.
It intentionally uses `builtin` mode to test Codex orchestration before adding
gstack's optional dependencies. Change `skill_mode` to `gstack` to test the local
skill integration separately.

1. Create a separate target directory, initialize Git, add a README and commit.
2. Copy `gca.json` and `SPEC.md` to a separate configuration directory.
3. Set `repo` to the target's absolute path and replace the gate's placeholder
   with the absolute path to this directory's `acceptance.py`.
4. Run `gstack-codex-auto doctor --config /path/to/gca.json`.
5. Run `gstack-codex-auto run --config /path/to/gca.json --run-dir /new/path/outside/target`.
6. Inspect the JSON report, candidate diff and gate logs. A failed Codex login
   is a blocked run, not a successful trial. No GitHub publishing is necessary.

Dependencies are only Python and Git, apart from Codex itself. The gate is kept
outside the target repository so ordinary candidate changes cannot rewrite it.
