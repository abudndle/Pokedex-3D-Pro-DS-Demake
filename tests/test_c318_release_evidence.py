#!/usr/bin/env python3
"""C318: release claims need independently reviewable evidence references."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "feature_parity", Path(__file__).resolve().parents[1] / "tools/check_feature_parity.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def evidence():
    return [{"kind": kind, "reference": "private-evidence-report-" + kind,
             "sha256": ("%02x" % i) * 32}
            for i, kind in enumerate(("original_source", "emulator", "hardware"), 1)]

assert module.has_release_evidence({"release_evidence": evidence()})
assert not module.has_release_evidence({})
assert not module.has_release_evidence({"release_evidence": evidence()[:2]})
for kind in ("original_source", "emulator", "hardware"):
    invalid = evidence()
    invalid[0]["kind"] = kind
    if kind != "original_source":
        assert not module.has_release_evidence({"release_evidence": invalid})
invalid = evidence()
invalid[1]["sha256"] = "not-a-digest"
assert not module.has_release_evidence({"release_evidence": invalid})
invalid = evidence()
invalid[2]["reference"] = "placeholder"
assert not module.has_release_evidence({"release_evidence": invalid})
invalid = evidence()
invalid.append(dict(invalid[0]))
assert not module.has_release_evidence({"release_evidence": invalid})
print("C318 release evidence acceptance/rejection checks passed")
