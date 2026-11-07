import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gstack_codex_auto.engine import load_config, new_run, run, report
from gstack_codex_auto.phases import PHASES
from gstack_codex_auto.runtime import (CodexRunner, PipelineError, atomic_json, git,
                                       fingerprint, lock, process, validate_response)


def response(score=8, blocked=False):
    return {"status": "blocked" if blocked else "pass", "summary": "test fixture",
            "findings": [{"severity": "blocker", "detail": "fixture failure"}] if blocked else [],
            "scores": dict.fromkeys(["functionality", "correctness", "maintainability", "usability", "spec_adherence"], score)}


class FixtureRunner:
    """No model calls. Test fixture, never used by production CLI."""
    def __init__(self, fail_phase=None, malformed=False):
        self.calls = []
        self.fail_phase = fail_phase
        self.malformed = malformed

    def run(self, phase, prompt, worktree, artifact):
        self.calls.append(phase.id)
        if phase.id == self.fail_phase:
            raise PipelineError("fixture interrupted")
        if self.malformed:
            return {"status": "pass"}
        if phase.id == "09-implement":
            (worktree / "answer.txt").write_text("41")
        if phase.id == "repair":
            (worktree / "answer.txt").write_text("42")
        return response()


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], check=True)
        git(self.repo, "config", "user.name", "Fixture")
        git(self.repo, "config", "user.email", "fixture@localhost")
        (self.repo / "README.md").write_text("fixture\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "initial")
        self.base = git(self.repo, "rev-parse", "HEAD")
        self.spec = self.root / "SPEC.md"
        self.spec.write_text("Write answer.txt with 42.")
        self.config = self.root / "config.json"
        self.c = {"repo": str(self.repo), "spec": str(self.spec), "skill_mode": "builtin",
                  "gates": [["python3", "-c", "from pathlib import Path; assert Path('answer.txt').read_text() == '42'"]]}
        self.persist()
        self.run_dir = self.root / "state"

    def persist(self):
        atomic_json(self.config, self.c)

    def start(self, runner=None):
        new_run(self.config, self.run_dir)
        return run(self.run_dir, runner or FixtureRunner())

    def test_complete_repairs_and_preserves_source(self):
        runner = FixtureRunner()
        state = self.start(runner)
        self.assertEqual(state["status"], "complete")
        self.assertIn("repair", runner.calls)
        self.assertEqual(state["winners"][0]["fixes"], 1)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)
        self.assertFalse((self.repo / "answer.txt").exists())
        self.assertEqual(git(self.repo, "show", state["winners"][0]["sha"] + ":answer.txt"), "42")

    def test_gate_failure_never_wins(self):
        self.c["max_fixes"] = 0
        self.persist()
        self.assertEqual(self.start()["status"], "blocked")
        self.assertEqual(report(self.run_dir)["winners"], [])

    def test_resume_skips_completed_planning(self):
        self.assertEqual(self.start(FixtureRunner(fail_phase="09-implement"))["status"], "blocked")
        resumed = FixtureRunner()
        self.assertEqual(run(self.run_dir, resumed)["status"], "complete")
        self.assertNotIn("01-ceo", resumed.calls)

    def test_parallel_rounds_chain_winning_commit(self):
        self.c.update(candidates=2, parallel=2, rounds=2)
        self.persist()
        state = self.start()
        self.assertEqual(state["status"], "complete")
        self.assertEqual(len(state["winners"]), 2)
        self.assertEqual([w["candidate"] for w in state["winners"]], [1, 1])
        child = json.loads((self.run_dir / "round-2/candidate-1/candidate.json").read_text())
        self.assertEqual(child["base"], state["winners"][0]["sha"])

    def test_stop_file_blocks(self):
        new_run(self.config, self.run_dir)
        (self.run_dir / "STOP").touch()
        self.assertEqual(run(self.run_dir, FixtureRunner())["status"], "blocked")
        self.assertEqual(report(self.run_dir)["calls"], 0)

    def test_budget_is_enforced(self):
        self.c["max_calls"] = 2
        self.persist()
        self.assertEqual(self.start()["status"], "blocked")
        self.assertEqual(report(self.run_dir)["calls"], 2)

    def test_malformed_output_cannot_pass(self):
        self.assertEqual(self.start(FixtureRunner(malformed=True))["status"], "blocked")

    def test_external_tree_edit_rejected_on_resume(self):
        self.c["max_fixes"] = 0
        self.persist()
        self.start()
        (self.run_dir / "round-1/candidate-1/worktree/answer.txt").write_text("external")
        state = run(self.run_dir, FixtureRunner())
        self.assertEqual(state["status"], "blocked")
        self.assertIn("outside", state["errors"][0])

    def test_tampered_artifact_rejected(self):
        self.start(FixtureRunner(fail_phase="09-implement"))
        (self.run_dir / "round-1/candidate-1/01-ceo.result.json").write_text("{}")
        self.assertEqual(run(self.run_dir, FixtureRunner())["status"], "blocked")

    def test_nonfinite_and_boolean_scores_rejected(self):
        for invalid in (float("nan"), True, 11, 10 ** 1000):
            r = response()
            r["scores"]["correctness"] = invalid
            with self.assertRaises(PipelineError):
                validate_response(r)

    def test_dirty_repo_rejected(self):
        (self.repo / "README.md").write_text("changed")
        with self.assertRaises(PipelineError):
            new_run(self.config, self.run_dir)

    def test_shell_strings_rejected(self):
        self.c["gates"] = ["python3 test.py; echo done"]
        self.persist()
        with self.assertRaises(PipelineError):
            load_config(self.config)

    def test_run_directory_cannot_be_in_repo(self):
        with self.assertRaises(PipelineError):
            new_run(self.config, self.repo / "state")

    def test_missing_gstack_is_not_silently_downgraded(self):
        self.c.update(skill_mode="gstack", skills_dir=str(self.root / "missing"))
        self.persist()
        with self.assertRaises(PipelineError):
            new_run(self.config, self.run_dir)

    def test_timeout(self):
        with self.assertRaises(PipelineError):
            process(["python3", "-c", "import time; time.sleep(5)"], self.repo, .05)

    def test_exclusive_lock(self):
        with lock(self.root / "lock"):
            with self.assertRaises(PipelineError):
                with lock(self.root / "lock"):
                    pass

    def test_readonly_mutation_blocked(self):
        class BadRunner(FixtureRunner):
            def run(self, phase, prompt, worktree, artifact):
                (worktree / "README.md").write_text("unauthorized")
                return response()
        state = self.start(BadRunner())
        self.assertEqual(state["status"], "blocked")
        self.assertIn("Read-only", state["errors"][0])
        self.assertEqual(run(self.run_dir, FixtureRunner())["status"], "blocked")

    def test_failed_response_cannot_hide_readonly_changes(self):
        class BadRunner(FixtureRunner):
            def run(self, phase, prompt, worktree, artifact):
                (worktree / "README.md").write_text("unauthorized")
                return {"bad": "response"}
        state = self.start(BadRunner())
        self.assertEqual(state["status"], "blocked")
        self.assertIn("Read-only", state["errors"][0])
        self.assertIn("integrity", run(self.run_dir, FixtureRunner())["errors"][0])

    def test_gate_cannot_modify_source(self):
        self.c["gates"] = [["python3", "-c", "from pathlib import Path; Path('README.md').write_text('changed')"]]
        self.persist()
        state = self.start()
        self.assertEqual(state["status"], "blocked")
        self.assertIn("Gate changed", state["errors"][0])

    def test_whitespace_filename_is_fingerprinted(self):
        path = self.repo / " leading and trailing "
        path.write_text("a")
        before = fingerprint(self.repo)
        path.write_text("b")
        self.assertNotEqual(before, fingerprint(self.repo))

    def test_failed_plan_revision_cannot_pass(self):
        class PlanningRunner(FixtureRunner):
            def run(self, phase, prompt, worktree, artifact):
                if phase.id == "02-challenge-ceo" or "revise-" in artifact.name:
                    return response(blocked=True)
                return super().run(phase, prompt, worktree, artifact)
        state = self.start(PlanningRunner())
        self.assertEqual(state["status"], "blocked")
        self.assertIn("revision blocked", state["errors"][0])

    def test_completed_run_is_idempotent(self):
        self.start()
        calls = report(self.run_dir)["calls"]
        runner = FixtureRunner()
        self.assertEqual(run(self.run_dir, runner)["status"], "complete")
        self.assertEqual(runner.calls, [])
        self.assertEqual(report(self.run_dir)["calls"], calls)

    def test_documentation_is_checked_before_selection(self):
        class BadDocs(FixtureRunner):
            def run(self, phase, prompt, worktree, artifact):
                if phase.id == "12-document":
                    (worktree / "answer.txt").write_text("broken")
                    return response()
                return super().run(phase, prompt, worktree, artifact)
        self.c["max_fixes"] = 0
        self.persist()
        self.assertEqual(self.start(BadDocs())["status"], "blocked")

    def test_codex_subprocess_contract(self):
        executable = self.root / "fake-codex"
        executable.write_text("#!/usr/bin/env python3\nimport sys,json\nfrom pathlib import Path\n"
                              "args=sys.argv[1:]; assert args[0]=='exec'\n"
                              "assert args[args.index('--sandbox')+1]=='read-only'\n"
                              "assert sys.stdin.read()=='test prompt'\n"
                              "assert '--dangerously-bypass-approvals-and-sandbox' not in args\n"
                              f"Path(args[args.index('--output-last-message')+1]).write_text({json.dumps(json.dumps(response()))})\n")
        executable.chmod(0o755)
        runner = CodexRunner({"codex": str(executable), "timeout": 5})
        result = runner.run(PHASES[0], "test prompt", self.repo, self.root / "phase")
        self.assertEqual(result["status"], "pass")

    def test_full_cli_flow_with_fake_codex_executable(self):
        executable = self.root / "fake-codex"
        executable.write_text("#!/usr/bin/env python3\nimport sys,json\nfrom pathlib import Path\n"
                              "args=sys.argv[1:]; prompt=sys.stdin.read()\n"
                              "assert args[0]=='exec' and args[-1]=='-'\n"
                              "assert 'approval_policy=\"never\"' in args\n"
                              "if prompt.startswith('GCA phase 09-implement,'):\n"
                              "    assert args[args.index('--sandbox')+1]=='workspace-write'\n"
                              "    Path('answer.txt').write_text('42')\n"
                              f"Path(args[args.index('--output-last-message')+1]).write_text({json.dumps(json.dumps(response()))})\n")
        executable.chmod(0o755)
        self.c["codex"] = str(executable)
        self.persist()
        result = process([sys.executable, "-m", "gstack_codex_auto", "run",
                          "--config", str(self.config), "--run-dir", str(self.run_dir)],
                         Path(__file__).resolve().parents[1], 60)
        self.assertEqual(result["returncode"], 0, result["output"])
        result = report(self.run_dir)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["calls"], 13)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)


if __name__ == "__main__":
    unittest.main()
