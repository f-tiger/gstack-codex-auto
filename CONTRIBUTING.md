# Contributing

Requires Python 3.11+, Git and a POSIX host. No model account is needed for tests.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Keep the controller independent of any single web framework or target project.
Use Python's standard library unless a dependency has a concrete benefit.

Changes to orchestration must preserve these contracts:

1. A failed or missing review, QA result, gate receipt or valid score cannot produce a winner.
2. Final checks certify the tree that is selected, including documentation changes.
3. No target source checkout changes, automatic push, merge or deployment during `run`.
4. Call budgets apply across candidates and resumed runs. Invocation failure is not free.
5. Config gate commands use argv, never implicit shell interpolation.
6. Resume does not trust altered source or altered cached artifacts. Interrupted write phases are explicitly documented exceptions for partial edits.
7. Test fixtures cannot become a production fallback that pretends a model ran.

Include regression tests for changes to these contracts. Tests use temporary Git repositories and a fake Codex executable; they must not send real prompts or require network access. A live model acceptance result should separately record CLI version, model, skill versions, input spec, gates, commit and observed result, without uploading private logs.

Please open a focused PR with the behavior change and validation. Contributions must be original or properly licensed; do not copy upstream prompt files into this package.
