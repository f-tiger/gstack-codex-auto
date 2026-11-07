# Security and execution boundaries

GCA is a local automation tool for **trusted repositories and trusted commands**.
Do not use it as a sandbox for malicious source code or a hosted multi-tenant service.

- Codex phases request read-only or workspace-write sandboxing, with approvals set to never. GCA does not use Codex's dangerous sandbox bypass flag. The effective boundary depends on Codex, the OS and your configuration.
- Configured gates, Git and GitHub CLI run directly as your current user. Gates can execute arbitrary code, access the network and read credentials available to that account. Supplying argv avoids implicit shell expansion; it does not make a command safe.
- Candidate worktrees share a Git repository and user account. They are separate checkouts, not containers. MCP tools, skill helpers and configured Codex features can have their own privileges. Configure those externally before running.
- Instructions prohibit publishing, credential access, nested model calls and external notifications inside agent phases. Prompts and skills are not an authorization boundary; a hostile repository can attempt prompt injection. External sandbox/container controls are needed for stronger isolation.
- GCA stores spec text, source-derived prompts, model events and gate output in a private run directory. Logs are not automatically scrubbed. Never publish the run directory or include secret values in specs or fixtures.
- Skill file hashes detect changes to each loaded `SKILL.md`. They do not pin referenced resources, helper binaries, Codex configuration or the model. Checkpoints are not signed against an attacker with access to the state directory.
- Source fingerprints detect changes to tracked and non-ignored files, including symlink targets and HEAD. They exclude ignored artifacts, Git metadata beyond HEAD, and nested repository contents. Interrupted write phases allow resuming partial agent changes. Do not manually edit an interrupted candidate.
- A gate's argv is snapshotted outside the candidate, but scripts/tests in the candidate can change. Keep critical acceptance tests in an external trusted harness. A successful test exit is only as meaningful as the test itself.
- Publishing is an explicit command, verifies the target origin and winning branch, pushes an exact SHA, and creates a draft PR. It does not scan all generated content for secrets, merge, deploy or bypass repository protections. Inspect the diff and use CI/secret scanning before publication or merge.
- Candidate commits disable repository hooks. GCA does not execute deployment hooks implicitly; use configured verification gates for checks you need.

For a vulnerability, use the repository's private vulnerability reporting feature if available. Do not post credentials or private run artifacts in a public issue. If private reporting is unavailable, open a public issue asking for a private reporting channel without exploit details or secrets.
