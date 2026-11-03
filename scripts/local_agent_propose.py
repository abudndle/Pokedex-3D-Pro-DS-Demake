#!/usr/bin/env python3
"""No-cost local Ollama proposal, restricted to an original C file and its C regression."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

TASKS = {"menu":{"source":"source/menu_navigation.c","test":"tests/test_menu_navigation.c","goal":"Fix a demonstrable menu touch or navigation boundary defect, and add an assertion.","command":["sh","tests/run_menu_navigation.sh"]},"dsi":{"source":"source/dsi_features.c","test":"tests/test_dsi_feature_gating.c","goal":"Improve DS/DSi feature gating on a documented edge case, add regression; never claim DSi camera runtime without emulator evidence.","command":["sh","tests/run_dsi_feature_gating.sh"]},"layout":{"source":"source/menu_layout.c","test":"tests/test_menu_layout_smoke.c","goal":"Fix menu layout bounds edge case with regression; preserve original UI positions.","command":["sh","tests/run_menu_layout_smoke.sh"]}}
ENDPOINT = "http://127.0.0.1:11434/api/generate"

def validate_and_apply(root: Path, focus: str, plan: object) -> list[str]:
    if focus not in TASKS or not isinstance(plan, dict):
        raise ValueError("Unknown focus or malformed response")
    summary, edits = plan.get("summary"), plan.get("changes")
    if not isinstance(summary, str) or not 8 <= len(summary.strip()) <= 120:
        raise ValueError("Specific summary required")
    if not isinstance(edits, list) or not 2 <= len(edits) <= 4:
        raise ValueError("Expected 2-4 exact snippet edits")
    task = TASKS[focus]
    allowed = {task["source"], task["test"]}
    originals: dict[str, str] = {}
    proposed: dict[str, str] = {}
    asserted = False
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {"path", "old", "new"}:
            raise ValueError("Only path, old, new allowed")
        path, old, new = edit["path"], edit["old"], edit["new"]
        if type(path) is not str or path not in allowed:
            raise ValueError("Non-allowlisted source path")
        if (type(old) is not str or type(new) is not str or old == new or
            not 1 <= len(old) <= 1800 or not 1 <= len(new) <= 2400):
            raise ValueError("Empty, oversized or ineffective edit")
        target = root / path
        if not target.is_file() or target.is_symlink():
            raise ValueError("Missing or symlinked original source")
        if path not in originals:
            originals[path] = target.read_text(encoding="utf-8")
        before = proposed.get(path, originals[path])
        if before.count(old) != 1:
            raise ValueError("Snippet does not occur exactly once")
        proposed[path] = before.replace(old, new, 1)
        if path == task["test"] and re.search(r"\bassert\s*\(", new):
            asserted = True
    if set(proposed) != allowed or not asserted:
        raise ValueError("Must modify source and regression, adding assertion")
    for path, content in proposed.items():
        if (len(content) > len(originals[path]) + 2800 or
            len(content) < len(originals[path]) - 1800):
            raise ValueError("Whole-file rewrite forbidden")
    for path, content in proposed.items():
        (root / path).write_text(content, encoding="utf-8")
    return sorted(proposed)

def generate_plan(root: Path, focus: str, model: str, endpoint: str) -> dict:
    if endpoint != ENDPOINT:
        raise ValueError("Only local Ollama loopback endpoint allowed")
    task = TASKS[focus]
    source, test = task["source"], task["test"]
    prompt = (
        "Act as a cautious Nintendo DS C developer. Find ONE real correctness "
        "defect and fix it, adding a regression assert. If there is no genuine "
        "defect, return empty changes. Reply with ONE JSON object, no markdown. "
        "Schema: {\"summary\":\"specific bug\", \"changes\":["
        "{\"path\":\"source path\",\"old\":\"exact verbatim snippet\","
        "\"new\":\"replacement\"},{\"path\":\"test path\","
        "\"old\":\"exact verbatim snippet\",\"new\":\"replacement with assertion\"}]}. "
        "Do not create files, change APIs, run commands, modify workflows, "
        "touch proprietary assets or invent original-game features. "
        "Task: " + task["goal"] + "\nSOURCE [" + source + "]:\n"
        + (root / source).read_text(encoding="utf-8")
        + "\nTEST [" + test + "]:\n"
        + (root / test).read_text(encoding="utf-8")
    )
    request = urllib.request.Request(
        endpoint,
        data=json.dumps({"model": model, "prompt": prompt, "format": "json",
                         "stream": False, "options": {"temperature": 0.1,
                         "num_predict": 1800, "num_ctx": 8192}}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        body = json.load(response)
    if not isinstance(body, dict) or not isinstance(body.get("response"), str):
        raise ValueError("Malformed local model response")
    return json.loads(body["response"])

def run(root: Path, output_dir: Path, focus: str, model: str) -> bool:
    if focus not in TASKS:
        raise ValueError("Unknown focus")
    output_dir.mkdir(parents=True, exist_ok=True)
    task = TASKS[focus]
    original = {name: (root / task[name]).read_bytes() for name in ("source", "test")}
    last_error = None
    # Independent attempts: failed snippets must not contaminate retry inputs.
    for attempt in range(2):
        try:
            plan = generate_plan(root, focus, model, ENDPOINT)
            paths = validate_and_apply(root, focus, plan)
            # Trusted fixed commands only; model output is never executed as commands.
            subprocess.run(task["command"], cwd=root, check=True, timeout=420)
            subprocess.run(["git", "diff", "--check"], cwd=root, check=True, timeout=20)
            patch = subprocess.run(
                ["git", "diff", "--", *paths], cwd=root, check=True,
                text=True, capture_output=True, timeout=20).stdout
            if not patch or len(patch) >= 14000:
                raise ValueError("No bounded source/test diff to publish")
            (output_dir / "proposal.patch").write_text(patch, encoding="utf-8")
            (output_dir / "proposal.json").write_text(json.dumps({
                "summary": plan["summary"], "focus": focus, "paths": paths,
                "validated": True, "model": model}, indent=2) + "\n",
                encoding="utf-8")
            return True
        except (ValueError, OSError, TimeoutError, json.JSONDecodeError,
                subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            last_error = exc
            for name, data in original.items():
                (root / task[name]).write_bytes(data)
            print(f"Rejected candidate {attempt + 1}/2: {exc}", file=sys.stderr)
    raise ValueError("No passing proposal after two bounded attempts: " + str(last_error))

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--focus", choices=TASKS, default=next(iter(TASKS)))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, default=Path("agent-output"))
    parser.add_argument("--model", default=os.environ.get("LOCAL_AGENT_MODEL", "qwen2.5-coder:1.5b"))
    args = parser.parse_args()
    try:
        run(args.root, args.output_dir, args.focus, args.model)
    except (ValueError, OSError, TimeoutError, json.JSONDecodeError,
            subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print("No safe tested proposal: " + str(exc), file=sys.stderr)
        return 1
    print("Validated bounded source/test patch available for draft PR")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
