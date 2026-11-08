# Validation record

## Conversation skill acceptance — 2026-11-08

The default conversation skill passed one real UTC CLI development task using
the current assistant and actual terminal tools. Planning, implementation,
documentation, review, functional checks, controlled fault repair and same-session
checkpoint replay were exercised. All 6 unit + 9 external + 4 original acceptance
tests passed after repair; unrelated edits and the external harness were preserved.
See [the scoped report and raw evidence](session-acceptance.md). This does not
validate cross-session persistence or the independent CLI described below.

## v0.1.1 adversarial follow-up

Two sequential adversarial reviews added 14 regression tests to the original
31. See [the review record](adversarial-review.md) for reproducible scenarios,
the fixes, state-format compatibility and remaining limitations. The final
source suite and the suite run against the installed v0.1.1 wheel both passed
all 45 tests locally on Python 3.12.14. Both suites were rerun successfully
before the main-branch upload, including a fresh installation of the wheel.
Live model acceptance of the independent CLI remains outstanding. Public release assets and remote
CI results are tracked on the repository's Releases and Actions pages.

## v0.1.0 baseline

Recorded on 2026-11-07. This separates controller evidence from model behavior.

## Offline controller verification

Local environment: Linux, Python 3.12.14. Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

31 tests passed during release preparation. They exercise temporary real Git
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
- Loading the current gstack layout where the engineering methodology is
  embedded in `gstack-autoplan/plan-eng-review.md`.

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

Local gstack Codex skill files (including the embedded engineering methodology)
were checked with `doctor`, but successful execution of their
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
