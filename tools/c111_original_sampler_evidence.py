#!/usr/bin/env python3
"""Private forensic inventory of original 3DS C5 material shader/sampler words.

This collects *raw source evidence* rather than interpreting unresolved GPU
sampler equations. The C88 verified material/shader/C75 references are compared
with all 13 original material dwords. No diffuse/normal/specular/effect role is
asserted from shader declarations or texture filenames. Keep output private.
"""
import argparse
import csv
import hashlib
import json
import re
import struct
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from c88_original_material_references import parse

C5_MEMBER = re.compile(r"decoded_c5/(p\d{3})\.c5$")
ROSTER = {f"p{i:03d}" for i in range(734) if i not in (721, 722, 723, 724)}
FLAGS = re.compile(r"CF_[A-Z0-9_]+")
SCHEMA = "C111_ORIGINAL_C5_MATERIAL_WORDS_V1"

def material_evidence(model_id, raw, texture_rows):
    """Return checked original dword records without inferring GPU sampler roles."""
    if not C5_MEMBER.fullmatch(f"decoded_c5/{model_id}.c5"):
        raise ValueError("invalid C5 model ID")
    refs, meta = parse(raw, texture_rows)
    if meta["ntex"] and not texture_rows:
        raise ValueError("original C75 reference inventory required")
    start = struct.unpack_from("<I", raw, 0x34)[0]
    end = start + 52 * meta["nmaterial"]
    if end > len(raw):
        raise ValueError("original C5 material table truncated")
    rows = []
    categories = Counter()
    for i, ref in enumerate(refs):
        words = struct.unpack_from("<13I", raw, start + i * 52)
        ref_index, material_name, shader_index, shader_name, t0, t1 = ref[:6]
        if (ref_index != i or words[0] & 0xffff != shader_index or
                words[1] & 0xffff != t0 or words[1] >> 16 != t1):
            raise ValueError("original material raw words/reference mismatch")
        if ";;;" not in shader_name:
            raise ValueError("original shader declaration missing")
        flags = shader_name.split(";;;", 1)[1].split(",")
        if not flags or any(not FLAGS.fullmatch(f) for f in flags) or len(flags) != len(set(flags)):
            raise ValueError("invalid original C5 capability declaration")
        color = "CF_COLORMAP" in flags
        bump = "CF_BUMPMAP" in flags
        values = {n for n in (t0, t1) if n != 65535}
        if not color:
            status = "NO_COLORMAP_DECLARATION"
        elif bump:
            status = "COLORMAP_WITH_BUMPMAP_UNRESOLVED"
        elif len(values) != 1:
            status = "MULTIPLE_OR_MISSING_REFERENCES_UNRESOLVED"
        else:
            status = "SINGLE_REFERENCE_COLOR_CANDIDATE_NOT_GPU_VERIFIED"
        categories[status] += 1
        raw_bytes = raw[start + i * 52:start + (i + 1) * 52]
        rows.append({
            "material_index": i,
            "shader_index": shader_index,
            "shader_declaration": shader_name,
            "source_material_name": material_name,
            "source_texture_references": [t0, t1],
            "source_material_words_hex": [f"0x{word:08x}" for word in words],
            "source_material_record_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "source_sampler_role_status": status,
            "original_color_sampler_slot_verified": False,
            "original_normal_sampler_slot_verified": False,
        })
    return ({
        "schema": SCHEMA,
        "model_id": model_id,
        "source_C5_sha256": hashlib.sha256(raw).hexdigest(),
        "material_count": len(rows),
        "evidence": rows,
        "original_GPU_sampler_roles_verified": 0
    }, categories)

def collect(source_dir, texture_csv, output, require_full=False):
    references = defaultdict(list)
    with Path(texture_csv).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mid = row.get("model_id", "")
            if re.fullmatch(r"p\d{3}", mid) is None:
                raise ValueError("invalid C75 texture model ID")
            references[mid].append(row)
    for records in references.values():
        records.sort(key=lambda x: int(x["index"]))
    discovered = set()
    evidence = {}
    classifications = Counter()
    for part in (1, 2, 3):
        with zipfile.ZipFile(Path(source_dir) /
                f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip") as archive:
            if archive.testzip() is not None:
                raise ValueError("corrupted original C5 ZIP")
            for name in archive.namelist():
                match = C5_MEMBER.fullmatch(name)
                if match is None:
                    continue
                mid = match.group(1)
                if mid not in ROSTER or mid in discovered:
                    raise ValueError("duplicate or unknown original model ID")
                discovered.add(mid)
                checked, classified = material_evidence(mid, archive.read(name), references[mid])
                evidence[f"evidence/{mid}.json"] = checked
                classifications.update(classified)
    if not discovered:
        raise ValueError("no decoded original C5 materials found")
    if set(references) - discovered:
        raise ValueError("C75 references without matching original C5 model")
    if require_full and discovered != ROSTER:
        raise ValueError("expected all 730 original model C5 archives")
    summary = {
        "schema": SCHEMA,
        "original_models_inspected": len(discovered),
        "original_materials_inspected": sum(classifications.values()),
        "material_source_categories": dict(sorted(classifications.items())),
        "verified_GPU_color_sampler_slots": 0,
        "verified_GPU_normal_sampler_slots": 0,
        "private_shader_instructions_still_required": True,
        "release_ready": False,
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in sorted(evidence.items()):
            archive.writestr(name, json.dumps(payload, indent=2) + "\n")
        archive.writestr("C111_sampler_evidence_report.json",
                         json.dumps(summary, indent=2) + "\n")
    return summary

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--texture-reference-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    try:
        report = collect(args.private_root, args.texture_reference_csv,
                         args.output, args.require_full)
    except (OSError, ValueError, IndexError, KeyError, UnicodeError,
            struct.error, zipfile.BadZipFile) as exc:
        parser.exit(1, "C111 original sampler evidence rejected: " + str(exc) + "\n")
    print(json.dumps(report, indent=2))
if __name__ == "__main__":
    main()
