#!/usr/bin/env python3
"""C134: verify private C56 C5 archives and join C86 geometry readiness.

Produces only a local analysis report. Does not export game files to GitHub.
Structural C5 integrity NEVER implies correct UV/material/renderer fidelity.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

from validate_c56 import assess

EXPECTED_IDS = {i for i in range(734) if i not in (721, 722, 723, 724)}
WARNING_IDS = {76, 77, 145, 377, 391, 663, 729}
PART_RANGES = ((0, 249), (250, 499), (500, 733))
MAX_C5_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 900 * 1024 * 1024
NAME = re.compile(r"decoded_c5/p([0-9]{3})\.c5\Z")


def read_manifest(bundle):
    with zipfile.ZipFile(bundle) as z:
        if len(z.namelist()) != len(set(z.namelist())):
            raise ValueError("duplicate decoder bundle members")
        with z.open("C56_validation.csv") as handle:
            raw = handle.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError("decoder validation CSV too large")
    rows = {}
    for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))):
        label = row.get("model", "")
        if not re.fullmatch(r"p[0-9]{3}", label) or label in rows:
            raise ValueError("invalid or duplicate validation model ID")
        if row.get("status") not in ("strict_valid", "valid_with_0x26_flag_warning"):
            raise ValueError("invalid C56 source validation status")
        digest = row.get("sha256", "")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("invalid C56 source hash")
        rows[label] = row
    if {int(k[1:]) for k in rows} != EXPECTED_IDS:
        raise ValueError("C56 validation inventory does not contain 730 unique recovered IDs")
    return rows


def inspect_archives(paths, reference):
    if len(paths) != 3:
        raise ValueError("exactly three ordered C56 archive parts required")
    ids = set()
    classifications = {}
    total_bytes = 0
    for index, path in enumerate(paths):
        low, high = PART_RANGES[index]
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if len(names) != len(set(names)):
                raise ValueError("duplicate C56 archive entries")
            for info in z.infolist():
                match = NAME.fullmatch(info.filename)
                if not match:
                    raise ValueError("unknown/unsafe C56 archive member")
                model = int(match.group(1))
                if not low <= model <= high or model in ids or model not in EXPECTED_IDS:
                    raise ValueError("duplicate, displaced or unexpected C56 model")
                if not 0 < info.file_size <= MAX_C5_BYTES:
                    raise ValueError("C56 model payload size outside safety limits")
                total_bytes += info.file_size
                if total_bytes > MAX_TOTAL_BYTES:
                    raise ValueError("C56 total decoded data exceeds safety limit")
                data = z.read(info)
                label = f"p{model:03d}"
                expected = reference[label]
                if (len(data) != int(expected["decoded_bytes"]) or
                    hashlib.sha256(data).hexdigest() != expected["sha256"]):
                    raise ValueError(f"C56 private SHA/size mismatch: {label}")
                status, flags, serious, parsed = assess(data)
                if (serious or status != expected["status"] or
                    flags != int(expected["0x26_descriptor_flags"]) or
                    len(parsed["first_table"]) != int(expected["primary_descriptor_count"])):
                    raise ValueError(f"C56 structure/descriptor mismatch: {label}")
                if (model in WARNING_IDS) != (status == "valid_with_0x26_flag_warning"):
                    raise ValueError(f"C56 unexpected descriptor warning: {label}")
                classifications[label] = status
                ids.add(model)
    if ids != EXPECTED_IDS:
        raise ValueError("C56 archive inventory has missing models")
    return classifications, total_bytes


def join_geometry(classifications, geometry_report):
    report = json.loads(Path(geometry_report).read_text(encoding="utf-8"))
    records = report.get("per_model")
    if not isinstance(records, list) or len(records) != 730:
        raise ValueError("C86 per-model report missing or incomplete")
    rows = {}
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("invalid C86 geometry record")
        label = row.get("model_id")
        if label not in classifications or label in rows:
            raise ValueError("C86 model ID missing or duplicated")
        preview = row.get("fallback_preview")
        candidate = row.get("paired_uv_candidate")
        if type(preview) is not bool or type(candidate) is not bool:
            raise ValueError("C86 recovery flags must be boolean")
        if candidate and not preview:
            raise ValueError("C86 candidate has no matching fallback geometry")
        rows[label] = {
            "model": label, "c56_status": classifications[label],
            "fallback_ds3m": preview, "paired_uv_candidate": candidate,
            "verified_material_binding": False, "production_renderer_ready": False,
        }
    if set(rows) != set(classifications):
        raise ValueError("C86 inventory cannot be joined to C56")
    previews = sum(x["fallback_ds3m"] for x in rows.values())
    uv = sum(x["paired_uv_candidate"] for x in rows.values())
    if previews != 726 or uv != 538 or (
        report.get("source_model_records") != 730 or
        report.get("source_derived_fallback_ds3m") != previews or
        report.get("complete_uv_paired_candidates") != uv or
        report.get("missing_c18_meshes") != 4):
        raise ValueError("C86 model coverage counters inconsistent")
    missing = sorted(k for k, v in rows.items() if not v["fallback_ds3m"])
    return rows, missing


def verify(parts, decoder_bundle, c86_report):
    expected = read_manifest(decoder_bundle)
    classifications, total = inspect_archives(parts, expected)
    joined, missing = join_geometry(classifications, c86_report)
    return {
        "c56_c5_verified": len(classifications),
        "c56_strict": sum(v == "strict_valid" for v in classifications.values()),
        "c56_descriptor_warnings": sorted(k for k, v in classifications.items()
                                           if v != "strict_valid"),
        "c56_decoded_bytes": total,
        "c86_fallback_ds3m": sum(x["fallback_ds3m"] for x in joined.values()),
        "c86_paired_uv_candidates": sum(x["paired_uv_candidate"] for x in joined.values()),
        "c86_missing_fallback_geometry": missing,
        "verified_material_bindings": 0,
        "production_renderer_ready": 0,
        "private_integrity_check_passed": True,
        "per_model": [joined[k] for k in sorted(joined)],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parts", nargs=3, type=Path, required=True,
                        metavar=("C56_PART1", "C56_PART2", "C56_PART3"))
    parser.add_argument("--decoder-bundle", type=Path, required=True)
    parser.add_argument("--c86-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="JSON report in a PRIVATE, gitignored path")
    args = parser.parse_args()
    result = verify(args.parts, args.decoder_bundle, args.c86_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "per_model"}, indent=2))


if __name__ == "__main__":
    main()
