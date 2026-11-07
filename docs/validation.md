# v0.1.0 validation record

Recorded on 2026-11-07. This separates controller evidence from model behavior.

## Offline controller verification

Local environment: Linux, Python 3.12.14. Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

30 tests passed during release preparation. They exercise temporary real Git
repositories, worktrees, subprocesses and deterministic model fixtures:

- Repairing a failed objective test, while preserving the original checkout.
- Rejecting failing gates, malformed responses, invalid scores and source changes by read-only phases.
- Parallel candidate selection and chaining the winning commit across rounds.
- Resume, artifact/source tampering, invocation budget, STOP, timeouts and locks.
- Checking documentation before selecting a winner.
- A complete 13-call CLI run through the production Codex adapter using a fake
  executable that obeys its stdin/argv/JSON-output contract.
- Exact-SHA draft-PR publishing, duplicate-PR reuse and refusal of an incorrect
  origin, changed winning branch or incomplete run, with GitHub calls mocked.

The fake executable is test-only. Production does not contain a mock-provider
fallback. These tests verify orchestration; they do not evaluate generated code
quality or prove that the real Codex API accepts every request.

GitHub Actions is configured to run this suite and installation/entrypoint
checks on Python 3.11, 3.12 and 3.13. Its actual result is visible in the repository
Actions tab; configuration alone is not a passing result.

## Real Codex smoke attempt

Installed CLI: `codex-cli 0.167.0-alpha.4`. A minimal `codex exec` request using
a read-only sandbox was attempted. The service rejected authentication with
HTTP 401, and the CLI reported that its access token could not be refreshed.
The smoke request did not successfully complete, so a real 13-phase run was
not attempted. No model-generated acceptance result is claimed.

Local gstack Codex skill files were found, but successful execution of their
helpers, browser behavior and workflows through this controller remains
unverified. This is an experimental release, not host certification.

## Reproduce a live acceptance trial

1. Authenticate your Codex CLI and verify a minimal live call works.
2. Follow [the example](../examples/README.md) in a disposable Git repository,
   initially with one candidate, one round and `skill_mode: builtin`.
3. Inspect the candidate diff, real CLI event files, objective test logs and
   selected SHA. Confirm all acceptance criteria with the external harness.
4. Repeat using `skill_mode: gstack` and record the exact upstream version.
5. For UI projects, additionally configure browser access and retain actual
   browser evidence. Do not substitute a model's claim for executed checks.

Keep private prompts and event files local. A useful public result contains
tool versions, an openly shareable spec, test commands, final commit and result.
