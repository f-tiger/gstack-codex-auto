"""Two-pass adversarial regressions; real Git and subprocesses, no model calls."""
import json
import argparse
import os
import signal
import shlex
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import test_pipeline as fixtures
from test_pipeline import FixtureRunner, response
from gstack_codex_auto.engine import new_run, run
from gstack_codex_auto.cli import publish
from gstack_codex_auto.runtime import PipelineError, git, lock, process


class AdversarialTests(unittest.TestCase):
    setUp = fixtures.PipelineTests.setUp
    persist = fixtures.PipelineTests.persist
    start = fixtures.PipelineTests.start

    def test_readonly_interruption_does_not_allow_external_edits(self):
        self.start(FixtureRunner(fail_phase="01-ceo"))
        worktree = self.run_dir / "round-1/candidate-1/worktree"
        (worktree / "README.md").write_text("unreviewed external edit")
        state = run(self.run_dir, FixtureRunner())
        self.assertEqual(state["status"], "blocked")

    def test_write_interruption_does_not_allow_external_commit(self):
        self.start(FixtureRunner(fail_phase="09-implement"))
        worktree = self.run_dir / "round-1/candidate-1/worktree"
        (worktree / "README.md").write_text("external commit")
        git(worktree, "add", ".")
        git(worktree, "commit", "-qm", "unverified history")
        self.assertEqual(run(self.run_dir, FixtureRunner())["status"], "blocked")

    def test_blocked_result_can_retry_after_environment_recovery(self):
        class BlockedRunner(FixtureRunner):
            def run(self, phase, prompt, worktree, artifact):
                if phase.id == "09-implement":
                    return response(blocked=True)
                return super().run(phase, prompt, worktree, artifact)
        self.assertEqual(self.start(BlockedRunner())["status"], "blocked")
        self.assertEqual(run(self.run_dir, FixtureRunner())["status"], "complete")

    def test_readonly_index_changes_are_rejected(self):
        class IndexRunner(FixtureRunner):
            def run(self, phase, prompt, worktree, artifact):
                git(worktree, "update-index", "--assume-unchanged", "README.md")
                return response()
        state = self.start(IndexRunner())
        self.assertEqual(state["status"], "blocked")
        self.assertIn("Hidden index", state["errors"][0])

    def test_hidden_dirty_source_is_not_a_clean_start(self):
        git(self.repo, "update-index", "--assume-unchanged", "README.md")
        (self.repo / "README.md").write_text("hidden dirty source")
        with self.assertRaises(PipelineError):
            new_run(self.config, self.run_dir)

    def test_tested_tree_cannot_differ_from_winning_commit(self):
        class HiddenEditRunner(FixtureRunner):
            def run(self, phase, prompt, worktree, artifact):
                if phase.id == "12-document":
                    git(worktree, "update-index", "--assume-unchanged", "answer.txt")
                    (worktree / "answer.txt").write_text("42")
                    return response()
                return super().run(phase, prompt, worktree, artifact)
        self.assertEqual(self.start(HiddenEditRunner())["status"], "blocked")

    def test_completed_run_rechecks_evidence(self):
        self.start()
        score = self.run_dir / "round-1/candidate-1/13-score.result.json"
        score.write_text(json.dumps(response(blocked=True)))
        with self.assertRaises(PipelineError):
            run(self.run_dir, FixtureRunner())

    def publish_args(self):
        return argparse.Namespace(run_dir=str(self.run_dir), github_repo="owner/repo",
                                  base="main", title="candidate")

    def refuse_network(self, repo, *args, **kwargs):
        if args[0] == "push":
            raise AssertionError("Unsafe push reached before validation")
        return git(repo, *args, **kwargs)

    def test_publish_rejects_different_push_url(self):
        self.start()
        git(self.repo, "remote", "add", "origin", "https://github.com/owner/repo.git")
        git(self.repo, "config", "remote.origin.pushurl", "https://github.com/other/repo.git")
        with patch("gstack_codex_auto.cli.git", side_effect=self.refuse_network):
            with self.assertRaises(PipelineError):
                publish(self.publish_args())

    def test_publish_rechecks_gate_evidence(self):
        self.start()
        git(self.repo, "remote", "add", "origin", "https://github.com/owner/repo.git")
        receipt = self.run_dir / "round-1/candidate-1/verify-1-gates.json"
        receipt.write_text("[]")
        with patch("gstack_codex_auto.cli.git", side_effect=self.refuse_network):
            with self.assertRaises(PipelineError):
                publish(self.publish_args())

    def test_publish_cannot_race_active_runner(self):
        self.start()
        git(self.repo, "remote", "add", "origin", "https://github.com/owner/repo.git")
        with lock(self.run_dir / "run.lock"):
            with patch("gstack_codex_auto.cli.git", side_effect=self.refuse_network):
                with self.assertRaises(PipelineError):
                    publish(self.publish_args())

    def test_worktree_creation_does_not_execute_repository_hooks(self):
        marker = self.root / "hook-ran"
        hook = self.repo / ".git/hooks/post-checkout"
        hook.write_text("#!/bin/sh\ntouch " + shlex.quote(str(marker)) + "\n")
        hook.chmod(0o755)
        self.start()
        self.assertFalse(marker.exists())

    def child_process_script(self):
        marker = self.root / "orphan-ran"
        child = ("import signal,time; from pathlib import Path; "
                 "signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(.7); "
                 f"Path({str(marker)!r}).touch()")
        script = ("import subprocess,sys,time; "
                  f"subprocess.Popen([sys.executable,'-c',{child!r}]); time.sleep(.1)")
        return marker, script

    def test_timeout_kills_child_even_after_parent_exits(self):
        marker, script = self.child_process_script()
        with self.assertRaises(PipelineError):
            process([sys.executable, "-c", script + "; time.sleep(10)"],
                    self.repo, .3, log=self.root / "timeout.log")
        time.sleep(.8)
        self.assertFalse(marker.exists())

    def test_successful_command_does_not_leave_background_writers(self):
        marker, script = self.child_process_script()
        process([sys.executable, "-c", script], self.repo, 3, log=self.root / "success.log")
        time.sleep(.8)
        self.assertFalse(marker.exists())

    def test_cli_interrupt_stops_active_codex_process(self):
        ready = self.root / "codex.pid"
        executable = self.root / "fake-codex"
        executable.write_text("#!/usr/bin/env python3\nimport os,time\nfrom pathlib import Path\n"
                              f"Path({str(ready)!r}).write_text(str(os.getpid()))\n"
                              "time.sleep(30)\n")
        executable.chmod(0o755)
        self.c["codex"] = str(executable)
        self.persist()
        with (self.root / "cli.log").open("w") as log:
            cli = subprocess.Popen([sys.executable, "-m", "gstack_codex_auto", "run",
                                    "--config", str(self.config), "--run-dir", str(self.run_dir)],
                                   stdout=log, stderr=log, start_new_session=True)
            try:
                deadline = time.monotonic() + 5
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertTrue(ready.exists())
                cli.send_signal(signal.SIGINT)
                self.assertEqual(cli.wait(timeout=5), 2)
            finally:
                for pid in [cli.pid] + ([int(ready.read_text())] if ready.exists() else []):
                    try:
                        os.killpg(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                cli.wait()
