"""Bounded subprocesses, atomic state, exclusive runner lock and Codex adapter."""
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
import tempfile
import fcntl
from contextlib import contextmanager

from .phases import RESPONSE_SCHEMA


class PipelineError(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w") as f:
        os.chmod(temp, 0o600)
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


def read_json(path):
    return json.loads(Path(path).read_text())


@contextmanager
def lock(path, wait=False):
    with Path(path).open("a") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB))
        except BlockingIOError as exc:
            raise PipelineError("Another runner owns this run") from exc
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def process(argv, cwd, timeout, stdin=None, log=None, cancel_event=None):
    """Never shell-expand config commands. Kill the process group on timeout."""
    start = time.monotonic()
    sink = open(log, "w+b") if log else tempfile.TemporaryFile()
    if log:
        os.chmod(log, 0o600)
    try:
        with subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE,
                              stdout=sink, stderr=subprocess.STDOUT,
                              text=True, start_new_session=True) as proc:
            try:
                if cancel_event is None:
                    proc.communicate(stdin, timeout=timeout)
                else:
                    first = True
                    while True:
                        if cancel_event.is_set():
                            raise PipelineError("Run interrupted; stopping active subprocess")
                        remaining = timeout - (time.monotonic() - start)
                        if remaining <= 0:
                            raise subprocess.TimeoutExpired(argv, timeout)
                        try:
                            proc.communicate(stdin if first else None, timeout=min(.1, remaining))
                            break
                        except subprocess.TimeoutExpired:
                            first = False
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                raise PipelineError(f"Command interrupted or timed out after {timeout}s: {argv[0]}")
            finally:
                # The leader can exit before its descendants. Always clean the
                # group, including after success, so late writes cannot escape checks.
                signal_group(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    pass
                signal_group(proc.pid, signal.SIGKILL)
                proc.wait()
            out = b""
            if not log:
                sink.seek(0)
                out = sink.read(2_000_001)
            if len(out) > 2_000_000:
                raise PipelineError("Command output exceeded 2 MB; use log capture")
            return {"returncode": proc.returncode, "output": out.decode(errors="replace"),
                    "seconds": round(time.monotonic() - start, 3)}
    finally:
        sink.close()


def signal_group(pid, sig):
    try:
        os.killpg(pid, sig)
    except ProcessLookupError:
        pass


def read_tail(path, size=6000):
    with Path(path).open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        stream.seek(max(0, stream.tell() - size))
        return stream.read(size).decode(errors="replace")


def git(repo, *args, strip=True):
    r = process(["git", "-c", "core.hooksPath=/dev/null", "-C", str(repo), *args], repo, 120)
    if r["returncode"]:
        raise PipelineError(f"git {args[0]} failed: {r['output'][-1500:]}")
    return r["output"].strip() if strip else r["output"]


def fingerprint(repo):
    # Includes unstaged, staged and untracked (non-ignored) content.
    names = git(repo, "ls-files", "-co", "--exclude-standard", "-z", strip=False).split("\0")
    h = hashlib.sha256(git(repo, "rev-parse", "HEAD").encode())
    h.update(git(repo, "rev-parse", "--abbrev-ref", "HEAD").encode())
    h.update(git(repo, "ls-files", "--stage", "-v", "-z", strip=False).encode())
    for name in sorted(set(filter(None, names))):
        p = Path(repo) / name
        h.update(name.encode())
        h.update(str(p.lstat().st_mode).encode() if p.exists() or p.is_symlink() else b"deleted")
        if p.is_symlink():
            h.update(os.readlink(p).encode())
        elif p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


def check_index(repo, clean=False):
    """Reject Git flags that hide differences between tested files and commits."""
    entries = git(repo, "ls-files", "--stage", "-v", "-z", strip=False).split("\0")
    for entry in filter(None, entries):
        if entry[0].islower() or entry[0] == "S":
            raise PipelineError("Hidden index flags (assume-unchanged/skip-worktree) are unsupported")
        if entry[2:8] == "160000":
            raise PipelineError("Submodules are unsupported; use a standalone target repository")
    if git(repo, "ls-files", "--unmerged"):
        raise PipelineError("Unmerged index entries")
    if clean and git(repo, "status", "--porcelain"):
        raise PipelineError("Candidate is not a clean committed tree")


def validate_response(value):
    if not isinstance(value, dict) or set(value) != {"status", "summary", "findings", "scores"}:
        raise PipelineError("Invalid Codex response fields")
    if value["status"] not in ("pass", "blocked") or not isinstance(value["summary"], str):
        raise PipelineError("Invalid Codex response status/summary")
    if not isinstance(value["findings"], list):
        raise PipelineError("Invalid findings")
    for finding in value["findings"]:
        if (not isinstance(finding, dict) or set(finding) != {"severity", "detail"}
                or finding["severity"] not in ("blocker", "warning", "info")
                or not isinstance(finding["detail"], str)):
            raise PipelineError("Invalid finding")
    expected = RESPONSE_SCHEMA["properties"]["scores"]["required"]
    if not isinstance(value["scores"], dict) or set(value["scores"]) != set(expected):
        raise PipelineError("Invalid score dimensions")
    for score in value["scores"].values():
        if type(score) not in (float, int) or not 0 <= score <= 10 or not math.isfinite(score):
            raise PipelineError("Invalid score value")
    return value


def passed(response):
    return response["status"] == "pass" and not any(f["severity"] == "blocker" for f in response["findings"])


class CodexRunner:
    def __init__(self, config, cancel_event=None):
        self.config = config
        self.cancel_event = cancel_event

    def run(self, phase, prompt, worktree, artifact):
        schema = artifact.with_suffix(".schema.json")
        output = artifact.with_suffix(".response.json")
        atomic_json(schema, RESPONSE_SCHEMA)
        # A retry must not accidentally accept a previous successful response.
        output.unlink(missing_ok=True)
        argv = [self.config.get("codex", "codex"), "exec", "-C", str(worktree),
                "--sandbox", "workspace-write" if phase.write else "read-only",
                "-c", 'approval_policy="never"', "--ephemeral", "--json",
                "--output-schema", str(schema), "--output-last-message", str(output)]
        if self.config.get("model"):
            argv += ["--model", self.config["model"]]
        argv.append("-")
        result = process(argv, worktree, self.config["timeout"], stdin=prompt,
                         log=artifact.with_suffix(".events.jsonl"), cancel_event=self.cancel_event)
        if result["returncode"]:
            raise PipelineError(f"Codex exited {result['returncode']}; inspect {artifact.with_suffix('.events.jsonl')}")
        if not output.is_file():
            raise PipelineError("Codex returned no structured response")
        return validate_response(read_json(output))
