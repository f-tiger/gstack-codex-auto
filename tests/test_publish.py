import argparse
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gstack_codex_auto.cli import publish
from gstack_codex_auto.runtime import PipelineError, atomic_json


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.args = argparse.Namespace(run_dir=str(self.root), github_repo="owner/repo",
                                       base="main", title="Candidate")
        self.state = {"status": "complete", "config": {"repo": str(self.root)},
                      "winners": [{"sha": "abc123", "branch": "gca/run/r1-c1", "round": 1, "score": 8}]}
        atomic_json(self.root / "run.json", self.state)

    def test_blocked_run_cannot_publish(self):
        self.state["status"] = "blocked"
        atomic_json(self.root / "run.json", self.state)
        with patch("gstack_codex_auto.cli.git") as git:
            with self.assertRaises(PipelineError):
                publish(self.args)
            git.assert_not_called()

    def test_wrong_remote_cannot_push(self):
        with patch("gstack_codex_auto.cli.git", return_value="https://github.com/other/repo.git") as git:
            with self.assertRaises(PipelineError):
                publish(self.args)
            self.assertEqual(git.call_count, 1)

    def test_changed_branch_cannot_push(self):
        with patch("gstack_codex_auto.cli.git", side_effect=["https://github.com/owner/repo.git", "different"]) as git:
            with self.assertRaises(PipelineError):
                publish(self.args)
            self.assertEqual(git.call_count, 2)

    def test_publish_exact_commit_as_draft(self):
        with patch("gstack_codex_auto.cli.git", side_effect=["https://github.com/owner/repo.git", "abc123", ""]) as git:
            with patch("gstack_codex_auto.cli.process", side_effect=[
                {"returncode": 0, "output": "[]"},
                {"returncode": 0, "output": "https://github.com/owner/repo/pull/1\n"},
            ]) as process:
                result = publish(self.args)
                self.assertEqual(result["sha"], "abc123")
                git.assert_any_call(str(self.root), "push", "origin", "abc123:refs/heads/gca/run/r1-c1")
                self.assertIn("--draft", process.call_args.args[0])

    def test_repeat_publish_reuses_existing_pr(self):
        with patch("gstack_codex_auto.cli.git", side_effect=["git@github.com:owner/repo.git", "abc123", ""]):
            with patch("gstack_codex_auto.cli.process", return_value={
                "returncode": 0, "output": '[{"url":"https://github.com/owner/repo/pull/1"}]',
            }) as process:
                result = publish(self.args)
                self.assertTrue(result["pr"].endswith("/1"))
                self.assertEqual(process.call_count, 1)
