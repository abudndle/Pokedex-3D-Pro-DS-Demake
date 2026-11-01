#!/usr/bin/env python3
"""C143: source-verified C5 repeating three-channel record group inventory.

The exact record control words follow a repeated Q/S/T-like channel pattern.
Neither labels nor the linked source subject semantics are verified; in
particular these are NOT material-face or texture/sampler assignments.
Original game assets and detailed control payloads remain private.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path
from c140_c5_shader_inventory import ROSTER, PART_RANGES, reference_rows
from c142_c5_track_index import parse_source_tracks

NAME = re.compile(r"decoded_c5/p([0-9]{3})\.c5\Z")
CHANNEL_CODES = (0x00040071, 0x00030053, 0x00030054)
MAX_C5_BYTES = 16 * 1024 * 1024


def group_candidates(data: bytes, *, detailed=False):
    """Group only exact consecutive control-code triplets with matching keys.

    A different code, owner key, or low-16 control key is preserved as opaque,
    not silently coerced to an animation group.
    """
    verified = parse_source_tracks(data, include_records=False)
    start = verified["table_start"]
    count = verified["source_track_records"]
    entries = [struct.unpack_from("<4I", data, start + 16 * i) for i in range(count)]
    groups = []
    unknown = collections.Counter()
    unknown_records = []
    i = 0
    while i < count:
        triple = entries[i:i + 3]
        matches = (len(triple) == 3 and
                   tuple(t[3] for t in triple) == CHANNEL_CODES and
                   triple[0][1] == triple[1][1] == triple[2][1] and
                   (triple[0][2] & 0xffff) == (triple[1][2] & 0xffff) == (triple[2][2] & 0xffff))
        if matches:
            if detailed:
                groups.append({
                    "first_record": i,
                    "owner_word_opaque": f"0x{triple[0][1]:08x}",
                    "shared_low16_control_opaque": f"0x{triple[0][2] & 0xffff:04x}",
                    "channel_codes": [f"0x{c:08x}" for c in CHANNEL_CODES],
                    "source_payload_offsets": [v[0] for v in triple],
                    "source_material_assignment_verified": False,
                    "animation_channel_semantics_verified": False,
                })
            i += 3
        else:
            code = f"0x{entries[i][3]:08x}"
            unknown[code] += 1
            if detailed:
                unknown_records.append({"record": i, "control_code": code,
                                        "owner_word_opaque": f"0x{entries[i][1]:08x}"})
            i += 1
    n = (count - sum(unknown.values())) // 3
    assert n * 3 + sum(unknown.values()) == count
    return {
        "source_track_records": count,
        "three_channel_candidates": n,
        "matched_source_records": n * 3,
        "unclassified_source_records": sum(unknown.values()),
        "unclassified_code_counts": dict(sorted(unknown.items())),
        "source_track_payload_aggregate_sha256": verified["track_payload_aggregate_sha256"],
        "source_track_payload_bytes": verified["track_payload_bytes"],
        "channel_group_semantics_verified": False,
        "material_face_links_verified": False,
        **({"candidate_groups": groups, "unclassified_records": unknown_records} if detailed else {}),
    }


def audit(parts, decoder_bundle, c142_summary, *, detailed=False):
    if len(parts) != 3:
        raise ValueError("exactly three ordered C56 model archives required")
    original = reference_rows(decoder_bundle)
    prior = json.loads(Path(c142_summary).read_text(encoding="utf-8"))
    expected_records = prior.get("c142_pointer_indexed_source_records")
    if prior.get("c56_models_verified") != 730 or not isinstance(expected_records,int) or not 730 <= expected_records <= 730 * 512:
        raise ValueError("C142 verified baseline missing or incomplete")
    if set(prior.get("models", {})) != set(original):
        raise ValueError("C142 model ID inventory incomplete")
    models = {}
    counts = collections.Counter()
    opcodes = collections.Counter()
    for idx, part in enumerate(parts):
        low, high = PART_RANGES[idx]
        with zipfile.ZipFile(part) as z:
            members = z.infolist()
            if len(members) != len({x.filename for x in members}):
                raise ValueError("duplicate original source archive member")
            for member in members:
                m = NAME.fullmatch(member.filename)
                if not m:
                    raise ValueError("unsafe or unexpected C5 archive member")
                model = int(m.group(1))
                label = f"p{model:03d}"
                if model not in ROSTER or not low <= model <= high or label in models:
                    raise ValueError(f"duplicate, displaced or unsupported source model {label}")
                if not 0x78 <= member.file_size <= MAX_C5_BYTES:
                    raise ValueError(f"original C5 payload size out of bounds: {label}")
                raw = z.read(member)
                digest = hashlib.sha256(raw).hexdigest()
                ref = original[label]
                before = prior["models"][label]
                if (digest != ref["sha256"] or len(raw) != int(ref["decoded_bytes"]) or
                    digest != before["source_sha256"]):
                    raise ValueError(f"C56/C142 hash or length mismatch: {label}")
                candidate = group_candidates(raw, detailed=detailed)
                if (candidate["source_track_records"] != before["source_track_records"] or
                    candidate["source_track_payload_bytes"] != before["track_payload_bytes"] or
                    candidate["source_track_payload_aggregate_sha256"] != before["track_payload_aggregate_sha256"]):
                    raise ValueError(f"C142 track checksum/bounds mismatch: {label}")
                for key in ("source_track_records", "three_channel_candidates", "matched_source_records",
                            "unclassified_source_records"):
                    counts[key] += candidate[key]
                opcodes.update(candidate["unclassified_code_counts"])
                models[label] = {"source_sha256": digest, **candidate}
    if set(models) != set(original) or counts["source_track_records"] != expected_records:
        raise ValueError("C143 original source model or track inventory incomplete")
    return {
        "c56_models_verified": len(models),
        "source_track_records_verified": counts["source_track_records"],
        "ordered_three_channel_candidates": counts["three_channel_candidates"],
        "matched_source_records": counts["matched_source_records"],
        "unclassified_source_records": counts["unclassified_source_records"],
        "unclassified_code_counts": dict(sorted(opcodes.items())),
        "group_control_codes": [f"0x{c:08x}" for c in CHANNEL_CODES],
        "verified_animation_semantics": False,
        "verified_face_material_links": 0,
        "verified_original_texture_sampler_roles": 0,
        "certified_original_textured_models": 0,
        "scope": "Consecutive C5 three-code record groups with matching opaque keys; not confirmed bones, animations, shader links or material assignments",
        "models": {name: models[name] for name in sorted(models)},
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--parts", type=Path, nargs=3, required=True)
    p.add_argument("--decoder-bundle", type=Path, required=True)
    p.add_argument("--c142-summary", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--detailed", action="store_true", help="include each candidate group and unclassified source record privately")
    args = p.parse_args()
    if args.report.exists():
        p.error("refusing to overwrite a private report")
    output = audit(args.parts, args.decoder_bundle, args.c142_summary, detailed=args.detailed)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items() if k != "models"}, indent=2))


if __name__ == "__main__":
    main()