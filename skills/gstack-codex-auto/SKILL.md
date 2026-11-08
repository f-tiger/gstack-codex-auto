---
name: gstack-codex-auto
description: Automatically carry a development task through planning, implementation, review, testing and repair within the current Codex conversation. Use when asked to run gstack-codex-auto or complete a gstack development workflow continuously. No separate Codex CLI login is required for this default mode.
---

# Automatic development in the current session

Execute the user's task using the current assistant and its available tools.
The default is NOT a launcher for another model process. Do not run `codex exec`,
`gca-start`, or the Python pipeline, request a new API key, or require CLI login
unless the user explicitly chooses the optional independent CLI/background mode.
The current host still requires its own normal authentication and tool access.

## Establish the task

- Identify the target repository and user goal from the conversation. Read repository instructions and inspect existing changes. Preserve unrelated work; do not automatically stash, discard or commit it.
- Infer routine choices from the repository. Ask only for genuinely missing information that blocks progress. A supplied requirement is sufficient input: do not require gca.json or a prewritten SPEC.md.
- Turn the requirement into concrete acceptance criteria and executable verification commands. Identify dependencies and required runtime/browser evidence. Never substitute an always-successful command for a meaningful test.
- Use a private checkpoint directory outside the target repository when the host permits. Record target path, initial commit, existing changes, acceptance criteria, phase progress, commands/results and outstanding blockers in progress.md. Do not store credentials. If durable storage is unavailable, explain the recovery limitation.

## Execute without routine handoffs

1. Product plan: establish the user problem, valuable scope and risks; challenge assumptions against the request.
2. Engineering plan: inspect affected code, design interfaces and tests; challenge failure modes and compatibility.
3. Design plan: consider UI accessibility and interaction, or CLI/API ergonomics; challenge error handling and usability.
4. Reconcile the plans and resolve contradictions before implementation.
5. Implement the agreed behavior in the target workspace, preserving unrelated edits. Run appropriate checks as you work.
6. Update documentation for the actual behavior before the final checks.
7. Review the resulting diff, exercise the acceptance criteria and run the real test/build commands. For UI tasks use actual browser evidence when available. Missing required evidence is a blocker, not a passing result.
8. Repair failures and repeat the affected checks. Default to at most three repair cycles per invocation, unless the user specifies another finite limit. If blocked or the limit is reached, record evidence and explain the remaining issue. Never weaken acceptance tests to obtain a pass.
9. Recheck the final changed files, report what passed and what remains unverified, and identify the resulting branch/files. Publish, merge or deploy only within the user's existing authorization and host permissions.

Continue from phase to phase without asking the user to approve routine transitions.
Keep concise progress updates. Review passes here are self-review by the current
assistant, not independent model audits. Do not claim fresh-session isolation,
controller-enforced budgets, signed evidence or background persistence.

## Reuse installed gstack methodology

When available, read the relevant locally installed gstack skills for the current
phase: plan-ceo-review, plan-eng-review, plan-design-review, review, qa,
document-release and retro. Codex installations commonly use gstack-prefixed
names under the host's skills directory. Newer engineering guidance may be in
`gstack-autoplan/plan-eng-review.md`. Load only relevant methodology, not every
skill at once. Respect the user's authorized scope and the host's instructions.
Do not invoke another agent/model CLI merely because a referenced skill suggests
outside review. If an upstream dependency is unavailable, state that the original
workflow above is being used; do not pretend upstream tools or browser QA ran.
No upstream skills or binaries are bundled with this skill.

## Continuation and optional background mode

On a later "continue" request, read progress.md, recheck the target repository and
current diff, and rerun checks invalidated by subsequent edits. Do not treat an
old success entry as verification of new code. The assistant cannot guarantee
execution after the conversation or host environment stops.

Only when the user explicitly requests an independent CLI/background run, use the
repository's documented Python CLI workflow. That mode requires an installed,
authenticated Codex CLI and its JSON config; it may fail independently of the
current chat's login. Explain that distinction. Never silently switch modes after
a failure or claim an active process means the task succeeded.
