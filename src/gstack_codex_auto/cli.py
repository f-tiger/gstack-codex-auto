import argparse
import json
from pathlib import Path
import shutil
import sys

from . import __version__
from .engine import load_config, new_run, report, run, skill_snapshot
from .phases import PHASES
from .runtime import PipelineError, git, process, read_json


def main(argv=None):
    parser = argparse.ArgumentParser(description="Codex-native, resumable development pipeline")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "plan"):
        p = sub.add_parser(name)
        p.add_argument("--config", default="gca.json")
    p = sub.add_parser("run")
    p.add_argument("--config", default="gca.json")
    p.add_argument("--run-dir", required=True, help="Private state directory OUTSIDE target repository")
    for name in ("resume", "status", "report"):
        p = sub.add_parser(name)
        p.add_argument("run_dir")
    p = sub.add_parser("publish", help="Explicitly push a completed winner and open a draft PR")
    p.add_argument("run_dir")
    p.add_argument("--github-repo", required=True, help="Exact owner/name, must match origin")
    p.add_argument("--base", default="main")
    p.add_argument("--title", default="Pipeline candidate")
    args = parser.parse_args(argv)
    try:
        if args.command in ("doctor", "plan"):
            c = load_config(args.config)
            skills = skill_snapshot(c)
            result = {"phases": [{"id": p.id, "skill": p.skill, "sandbox": "workspace-write" if p.write else "read-only"} for p in PHASES],
                      "execution_order": "01–09, 12-document, then 10-review/11-qa/gates/repair loop, 13-score",
                      "skill_mode": c["skill_mode"], "skills_found": len(skills),
                      "candidates": c["candidates"], "rounds": c["rounds"],
                      "max_calls": c["max_calls"], "gates": c["gates"]}
            if args.command == "doctor":
                result["codex_found"] = bool(shutil.which(c["codex"]))
                result["authentication"] = "not checked: login status alone does not prove a live call works"
                if not result["codex_found"]:
                    raise PipelineError("codex executable missing")
        elif args.command == "run":
            root = new_run(args.config, args.run_dir)
            print(f"Run created: {root}", file=sys.stderr, flush=True)
            run(root)
            result = report(root)
        elif args.command == "resume":
            run(args.run_dir)
            result = report(args.run_dir)
        elif args.command == "publish":
            result = publish(args)
        else:
            result = report(args.run_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result.get("status") == "blocked" else 0
    except (PipelineError, OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def publish(args):
    state = read_json(Path(args.run_dir) / "run.json")
    if state["status"] != "complete":
        raise PipelineError("Only completed runs can be published")
    winner = state["winners"][-1]
    repo = state["config"]["repo"]
    remote = git(repo, "remote", "get-url", "origin")
    allowed = [f"https://github.com/{args.github_repo}", f"git@github.com:{args.github_repo}"]
    if remote.removesuffix(".git") not in allowed:
        raise PipelineError("Requested GitHub repository does not match origin")
    if git(repo, "rev-parse", winner["branch"]) != winner["sha"]:
        raise PipelineError("Winner branch changed since verification")
    git(repo, "push", "origin", f"{winner['sha']}:refs/heads/{winner['branch']}")
    existing = process(["gh", "pr", "list", "--repo", args.github_repo,
                        "--head", winner["branch"], "--base", args.base, "--json", "url"], repo, 60)
    if existing["returncode"]:
        raise PipelineError("Push succeeded; PR lookup failed. Inspect remote before retrying.")
    prs = json.loads(existing["output"])
    if prs:
        return {"pr": prs[0]["url"], "sha": winner["sha"]}
    body = (f"Codex pipeline candidate. Round {winner['round']}; model score {winner['score']}/10. "
            "Local configured gates passed. Scores are not independent validation. "
            "Review this diff and run CI before merging.")
    response = process(["gh", "pr", "create", "--draft", "--repo", args.github_repo,
                        "--head", winner["branch"], "--base", args.base,
                        "--title", args.title, "--body", body], repo, 120)
    if response["returncode"]:
        raise PipelineError("Push succeeded; PR creation failed. Inspect remote before retrying.")
    return {"pr": response["output"].strip(), "sha": winner["sha"]}


if __name__ == "__main__":
    sys.exit(main())
