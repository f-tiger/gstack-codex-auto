# Changelog

## Conversation skill — main branch

- Add an installable skill that executes in the current assistant conversation by default, without launching another Codex CLI or requiring its separate login.
- Add a portable installer with existing-file protection and explicit replacement.
- Make conversation mode the recommended English/Chinese README entry point; retain independent CLI mode as optional.
- The new skill is distributed from main. The existing v0.1.1 tag remains the historical CLI release; its tests do not certify conversation-mode task performance.

## 0.1.1 — 2026-11-07

Two adversarial review passes against the initial preview; see [the review record](docs/adversarial-review.md).

- Bound interrupted phases to their previous HEAD/branch; prohibit changes after interrupted read-only work.
- Retry blocked model responses on resume without resetting the invocation budget.
- Include logical Git index and branch in fingerprints; reject hidden index flags, unmerged indexes and submodules.
- Revalidate final review/QA/score, gate receipts and committed tree before winner reuse or publication.
- Lock publication, check every resolved push URL, disable implicit tag following and controller Git hooks.
- Clean up process groups after success/timeout; propagate Ctrl+C to active Codex/gate workers.
- Read captured command output and gate tails with bounded memory.

Checkpoint schema is now 2. Start a new run instead of reusing v0.1.0 state. Live-model acceptance remains unresolved; release and CI status are available on GitHub.

## 0.1.0 — 2026-11-07

Initial experimental release.

- Original Python controller using Codex CLI structured output and per-phase sandboxes.
- Thirteen development phase roles, local gstack skill loading and explicit built-in mode.
- Parallel Git worktree candidates, bounded repair loops, multiple rounds and winner selection.
- Objective command gates, atomic checkpoints, resume, STOP, timeouts and invocation budgets.
- JSON status/report commands and explicit draft-PR publishing.
- English/Chinese documentation, examples and offline regression tests.

Live model end-to-end validation is outstanding: the release environment's Codex smoke request was rejected with HTTP 401. Offline tests do not establish live model quality or upstream gstack runtime compatibility.
