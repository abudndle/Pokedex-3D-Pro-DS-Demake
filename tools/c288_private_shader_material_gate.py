#!/usr/bin/env python3
"""C288: cross-check C111 raw original material words against C275/C287 draws.

This is a private-only source-provenance gate, NOT GPU sampler decoding or a
verified native P3PX binding. Never upload Nintendo assets or private reports.
"""
import argparse
import collections
import json
import re
import stat
import zipfile
from pathlib import Path

from c114_original_sampler_differential import validate_model
from c286_private_format_consensus import _read_private_json, ROSTER, SHA

C275 = "C275_PRIVATE_C5_DRAW_MATERIAL_REFERENCE_V1"
C287 = "C287_PRIVATE_DRAW_TO_SOURCE_TEXTURE_CHAIN_V1"
SCHEMA = "C288_PRIVATE_RAW_MATERIAL_DRAW_CROSSCHECK_V1"
MEMBER = re.compile(r"evidence/(p\d{3})\.json\Z")
MAX_ZIP_BYTES = 32 * 1024 * 1024
MAX_MEMBER_BYTES = 256 * 1024


def _models(report, schema):
    if (not isinstance(report, dict) or not isinstance(report.get("summary"), dict)
            or report["summary"].get("schema") != schema
            or not isinstance(report.get("models"), list)
            or not 1 <= len(report["models"]) <= 730):
        raise ValueError("wrong source report schema or roster bounds")
    result = {}
    for row in report["models"]:
        if not isinstance(row, dict) or row.get("model_id") not in ROSTER:
            raise ValueError("invalid model ID")
        mid = row["model_id"]
        if mid in result:
            raise ValueError("duplicate model ID")
        if not isinstance(row.get("source_c5_sha256"), str) or not SHA.fullmatch(row["source_c5_sha256"]):
            raise ValueError("invalid source C5 SHA")
        result[mid] = row
    return result


def reconcile(c275, c287, evidence, require_full=False):
    """Reject inconsistent raw-source/material/texture joins without guessing roles."""
    original = _models(c275, C275)
    joined = _models(c287, C287)
    if (set(original) != set(joined) or set(original) != set(evidence)
            or (require_full and set(original) != ROSTER)):
        raise ValueError("C111/C275/C287 model roster mismatch or incomplete 730")
    counts = collections.Counter()
    for mid in sorted(original):
        src, bridge, raw = original[mid], joined[mid], evidence[mid]
        rows = validate_model(mid, raw)
        sha = src["source_c5_sha256"]
        if raw["source_C5_sha256"] != sha or bridge["source_c5_sha256"] != sha:
            raise ValueError("independent source C5 SHA mismatch")
        if (src.get("material_count") != len(rows) or
                type(src.get("material_count")) is not int or
                not isinstance(src.get("draws"), list) or
                not isinstance(bridge.get("draws"), list) or
                not 1 <= len(src["draws"]) <= 4096 or
                len(src["draws"]) != len(bridge["draws"])):
            raise ValueError("material or draw roster mismatch")
        checked = set()
        for draw, joined_draw in zip(src["draws"], bridge["draws"]):
            if not isinstance(draw, dict) or not isinstance(joined_draw, dict):
                raise ValueError("malformed draw")
            idx = draw.get("material_index")
            did = draw.get("draw_index")
            if (type(idx) is not int or not 0 <= idx < len(rows) or
                    type(did) is not int or not 0 <= did < 4096 or did in checked):
                raise ValueError("invalid or duplicate draw/material index")
            checked.add(did)
            raw_row = rows[idx]
            if (draw.get("shader_index") != raw_row["shader_index"] or
                    draw.get("shader_declaration") != raw_row["shader_declaration"] or
                    draw.get("source_material_name") != raw_row["source_material_name"] or
                    draw.get("source_texture_reference_indices") != raw_row["source_texture_references"]):
                raise ValueError("raw C111 material words contradict C275 draw")
            if (joined_draw.get("draw_index") != did or
                    joined_draw.get("material_index") != idx or
                    joined_draw.get("mesh_index") != draw.get("mesh_index") or
                    joined_draw.get("source_draw_material_reference_verified") is not True or
                    joined_draw.get("gpu_sampler_verified") is not False or
                    joined_draw.get("native_p3px_binding_verified") is not False):
                raise ValueError("C287 draw identity or unverified sampler status mismatch")
            slots = joined_draw.get("texture_reference_slots")
            if not isinstance(slots, list) or len(slots) != 2:
                raise ValueError("invalid C287 texture slots")
            for n, (slot, ref) in enumerate(zip(slots, raw_row["source_texture_references"])):
                if (not isinstance(slot, dict) or slot.get("slot") != n or
                        slot.get("gpu_sampler_verified") is not False or
                        slot.get("native_p3px_binding_verified") is not False or
                        slot.get("source_texture_index") != (None if ref == 65535 else ref)):
                    raise ValueError("raw C111 texture slot mismatch or forged GPU proof")
                if ref == 65535:
                    if slot.get("status") != "SOURCE_REFERENCE_ABSENT":
                        raise ValueError("missing source texture not marked absent")
                else:
                    counts["source_texture_reference_slots_checked"] += 1
            counts["draws_checked"] += 1
        counts["materials_checked"] += len(rows)
        counts["models_checked"] += 1
    return {"summary": {"schema": SCHEMA, **dict(sorted(counts.items())),
                        "raw_material_source_consistency_verified": True,
                        "original_gpu_sampler_roles_verified": 0,
                        "native_p3px_bindings_verified": 0,
                        "private_asset_emulator_verified": False,
                        "release_ready": False}}


def load_evidence(path):
    path = Path(path)
    if path.parent.is_symlink() or path.is_symlink():
        raise ValueError("private C111 symlink rejected")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_ZIP_BYTES:
        raise ValueError("private C111 ZIP must be bounded single-link regular file")
    result, total = {}, 0
    with zipfile.ZipFile(path) as archive:
        if len(archive.infolist()) > 731:
            raise ValueError("private C111 ZIP has too many members")
        for item in archive.infolist():
            if item.filename == "C111_sampler_evidence_report.json":
                continue
            match = MEMBER.fullmatch(item.filename)
            if not match or match.group(1) not in ROSTER:
                raise ValueError("unexpected private C111 ZIP member")
            mid = match.group(1)
            if mid in result or item.is_dir() or item.file_size > MAX_MEMBER_BYTES:
                raise ValueError("duplicate or oversized C111 evidence member")
            total += item.file_size
            if total > MAX_ZIP_BYTES:
                raise ValueError("private C111 uncompressed evidence budget exceeded")
            with archive.open(item) as fp:
                payload = fp.read(MAX_MEMBER_BYTES + 1)
            if len(payload) != item.file_size:
                raise ValueError("C111 evidence member length mismatch")
            result[mid] = json.loads(payload)
    if not result:
        raise ValueError("empty original C111 material evidence")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--c111-private-zip", type=Path, required=True)
    parser.add_argument("--c275-private-json", type=Path, required=True)
    parser.add_argument("--c287-private-json", type=Path, required=True)
    parser.add_argument("--output-private-json", type=Path, required=True)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    from c275_private_draw_material_chain import write_private_report
    try:
        paths = [args.c111_private_zip, args.c275_private_json, args.c287_private_json]
        if args.output_private_json.resolve() in [p.resolve() for p in paths]:
            raise ValueError("private output aliases an input")
        report = reconcile(_read_private_json(paths[1]), _read_private_json(paths[2]),
                           load_evidence(paths[0]), args.require_full)
        write_private_report(args.output_private_json, report)
    except (OSError, ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError,
            zipfile.BadZipFile) as exc:
        parser.exit(1, "C288 private material crosscheck rejected: " + str(exc) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
