#!/usr/bin/env python3
"""Test the allowlist and fail-closed policy without using a model or Nintendo assets."""
from pathlib import Path
import importlib.util
import tempfile
root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("local_agent_propose", root / "scripts/local_agent_propose.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
focus = next(iter(module.TASKS))
task = module.TASKS[focus]
with tempfile.TemporaryDirectory() as directory:
    base = Path(directory)
    for key in ("source", "test"):
        p = base / task[key]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("source token\n" if key == "source" else "assert(1);\n")
    orig_source = (base / task["source"]).read_text()
    orig_test = (base / task["test"]).read_text()
    good = {"summary": "Guard a synthetic boundary condition", "changes": [
        {"path": task["source"], "old": "source token", "new": "source token improved"},
        {"path": task["test"], "old": "assert(1);", "new": "assert(1);\nassert(2);"}]}
    invalid = [
        {"summary": good["summary"], "changes": [good["changes"][0]]},
        {"summary": good["summary"], "changes": [
            dict(good["changes"][0], path=".github/workflows/evil.yml"), good["changes"][1]]},
        {"summary": good["summary"], "changes": [
            good["changes"][0], dict(good["changes"][1], new="no assertion")]},
        {"summary": good["summary"], "changes": [
            good["changes"][0], dict(good["changes"][1], new="assert(1);\nassert(1);")]},
        {"summary": good["summary"], "changes": [
            dict(good["changes"][0], old="snippet missing"), good["changes"][1]]},
    ]
    invalid.append({"summary": good["summary"], "changes": [
        good["changes"][0], dict(good["changes"][1], new="assert(1); assert(2);")]})
    for bad in invalid:
        try:
            module.validate_and_apply(base, focus, bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Unsafe proposal was accepted")
        assert (base / task["source"]).read_text() == orig_source
        assert (base / task["test"]).read_text() == orig_test
    # Reject cosmetically modified C code even with a new test assertion.
    for cosmetic in ("source token // cosmetic note", "source   token"):
        bad = {"summary": good["summary"], "changes": [
            dict(good["changes"][0], new=cosmetic),
            good["changes"][1],
        ]}
        try:
            module.validate_and_apply(base, focus, bad)
        except ValueError:
            pass
        else:
            raise AssertionError("Cosmetic-only C edit accepted")
        assert (base / task["source"]).read_text() == orig_source
        assert (base / task["test"]).read_text() == orig_test
    changed = module.validate_and_apply(base, focus, good)
    assert set(changed) == {task["source"], task["test"]}
    assert (base / task["test"]).read_text().count("assert(") == 2
    try:
        module.generate_plan(base, focus, "test", "https://example.invalid")
    except ValueError:
        pass
    else:
        raise AssertionError("Remote model endpoint accepted")

# Automatic runs cover every allowlisted module without expanding write permissions.
if "module" in globals():
    choose = module.select_focus
else:
    from local_agent_propose import select_focus as choose
keys = tuple(module.TASKS)
for index, key in enumerate(keys):
    assert choose("auto", index) == key
    assert choose("auto", index + len(keys)) == key
    assert choose(key, 0) == key
for invalid in ("not-a-module",):
    try:
        choose(invalid, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("Unknown module accepted")
try:
    choose("auto", -1)
except ValueError:
    pass
else:
    raise AssertionError("Negative rotation slot accepted")

print("PASS: exact source/test allowlist, injected paths rejected, atomic failure")
