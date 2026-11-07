# Two adversarial review passes — v0.1.1

Date: 2026-11-07. Baseline: local v0.1.0 commit `ab80637`.
These are two sequential reviews by the same coding agent, with executable
failure injection, not independent-model audits or live Codex evaluations.
No external GitHub push occurred during the tests.

## Pass 1: recovery, evidence and commit consistency

Seven adversarial tests were introduced. Six failed against the baseline;
the index-only negative control was subsequently strengthened to require the
specific integrity error rather than accepting an unrelated blocked outcome.

| Scenario | Baseline observation | Fix |
| --- | --- | --- |
| Edit a candidate after interrupting a read-only phase | Resume accepted the external edit | Store phase mode/tree/HEAD/branch; reject read-only drift |
| Commit externally after interrupting an implementation phase | Resume accepted changed history | Require unchanged interrupted HEAD and branch |
| Retry a blocked implementation after environment recovery | Cached blocked response prevented retry | Reuse successful results only; budget still counts retries |
| Hide dirty tracked files using assume-unchanged | A dirty source could pass the clean-start check | Reject hidden index flags and unsupported submodule indexes |
| Test a file that differs from the committed blob using hidden index flags | Candidate could win while its commit contained the wrong value | Fingerprint logical index and branch; require a clean committed winner |
| Change scoring evidence after completion | Resume trusted the saved complete label | Revalidate final artifacts, receipt hashes and tree before reuse |

Result after fixes: all seven pass-1 regressions passed, followed by the
38-test suite then available.

## Pass 2: execution and publication boundaries

Seven additional failures were reproduced after the first pass:

| Scenario | Observation before fix | Fix |
| --- | --- | --- |
| Set a different `origin.pushurl` | Publication reached push despite validating only the fetch URL | Check every resolved push URL against the requested repository |
| Alter objective gate receipts before publication | Publication reached push without revalidating evidence | Verify final candidate evidence before any push |
| Publish while another process holds the run lock | Publication ignored the active run lock | Share the exclusive lock between run/resume/publish |
| Install a `post-checkout` hook | Creating candidate worktrees executed it | Disable hooks on all controller Git commands |
| Parent exits after timeout, child ignores SIGTERM | Child survived and wrote after the check | Always terminate the remaining process group, including SIGKILL |
| Successful command leaves a background child | Background child wrote after command completion | Clean up the original process group on success too |
| Send Ctrl+C while a Codex worker runs | CLI did not exit within the test's five-second bound | Propagate a cancellation event to active Codex/gate subprocesses |

Additional hardening: prevent implicit tag following during push; spool captured
stdout to a temporary file before a bounded read; read only the requested gate
log tail. Existing tests retain argv-only execution, failed-gate exclusion,
timeout behavior, exact-commit draft PRs and simulated full CLI execution.

## Acceptance and remaining limits

The final suite includes 45 tests (31 original plus 14 adversarial regressions).
Run it from source with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The package is versioned 0.1.1, and state schema 2 deliberately rejects older
run directories. Artifacts and the candidate worktree must remain available
for final evidence revalidation. Do not migrate old state by changing a number.

This does not establish the absence of defects. Processes that deliberately
escape their process group, malicious gate commands, private-state tampering,
Git filters and external services require stronger host controls. Worktrees
are not security isolation. See [SECURITY.md](../SECURITY.md).

Live Codex/gstack workflow acceptance remains outstanding because the previous
real CLI request returned HTTP 401. GitHub creation/publishing remains blocked
by the connection's missing repository-creation permission (HTTP 403). Those
external failures are not reclassified as passing tests by this review.
