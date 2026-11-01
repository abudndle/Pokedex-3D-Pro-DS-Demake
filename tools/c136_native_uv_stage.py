#!/usr/bin/env python3
"""C136: repair DS3M native header and optionally stage safe paired C62 UVs.

Work exclusively on private original-derived ZIPs. The default output fixes
the 16-byte native DS3M header without inventing data. Optional unit-UV QA
swaps BOTH matching geometry and UV files. Texture/material bindings are not
generated or inferred; this is not a verified original-textured ROM.
"""
import argparse
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path

ROSTER = {i for i in range(734) if i not in (721, 722, 723, 724)}
PREVIEW = re.compile(r"preview/p([0-9]{3})\.ds3m\Z")
CANDIDATE = re.compile(r"uv_candidates/p([0-9]{3})\.(ds3m|p3uv)\Z")
MAX_PREVIEW_BYTES = 16 + 600 * 21
MAX_UV_BYTES = 8 + 600 * 12


def validate_model(raw):
    if len(raw) < 16 or len(raw) > MAX_PREVIEW_BYTES:
        raise ValueError("DS3M header/size invalid")
    magic, version, triangles, source_vertices, faces = struct.unpack_from("<4sHHII", raw)
    if magic != b"DS3M" or version not in (1, 2) or not 1 <= triangles <= 600:
        raise ValueError("invalid DS3M model format")
    if len(raw) != 16 + triangles * (21 if version == 2 else 18) or faces < triangles:
        raise ValueError("DS3M face count or length invalid")
    # Native DS preview_stream.c interprets header bytes 8..11 as RESERVED 0.
    # Historical C18/C86/C135 packs stored original vertex counts there.
    # Preserve original vertex counts only in a PRIVATE per-model audit.
    return triangles, source_vertices, faces


def native_model(raw):
    triangles, historical_vertices, source_faces = validate_model(raw)
    native = raw[:8] + bytes(4) + raw[12:]
    assert struct.unpack_from("<I", native, 8)[0] == 0
    return native, {"preview_triangles": triangles,
                    "historical_source_vertices": historical_vertices,
                    "source_triangles": source_faces,
                    "native_sha256": hashlib.sha256(native).hexdigest()}


def validate_uv(raw, triangles):
    if len(raw) != 8 + triangles * 12 or len(raw) > MAX_UV_BYTES:
        raise ValueError("P3UV geometry/size mismatch")
    magic, version, count = struct.unpack_from("<4sHH", raw)
    if magic != b"P3UV" or version != 1 or count != triangles:
        raise ValueError("P3UV source format/triangle mismatch")
    values = struct.unpack_from("<" + "h" * (6 * count), raw, 8)
    return all(0 <= x <= 4096 for x in values)


def _read_candidate_inventory(archive):
    names = archive.namelist()
    if len(names) != len(set(names)):
        raise ValueError("duplicate candidate ZIP path")
    ds3m, uv = {}, {}
    for name in names:
        match = CANDIDATE.fullmatch(name)
        if not match:
            continue
        number = int(match.group(1))
        if number not in ROSTER:
            raise ValueError("candidate references unsupported model ID")
        (ds3m if match.group(2) == "ds3m" else uv)[number] = name
    if set(ds3m) != set(uv):
        raise ValueError("candidate pair missing geometry or UV")
    return ds3m, uv


def build(base_zip, candidates_zip, output_zip, *, mode="baseline",
          source_report=None, require_full=True):
    if mode not in ("baseline", "unit-uv-qa"):
        raise ValueError("invalid staging mode")
    if Path(base_zip).resolve() == Path(output_zip).resolve():
        raise ValueError("never overwrite original source archive")
    rows = {}
    with zipfile.ZipFile(base_zip) as base, zipfile.ZipFile(candidates_zip) as cand:
        names = base.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate source ZIP entries")
        source_models = {}
        for name in names:
            match = PREVIEW.fullmatch(name)
            if match:
                model = int(match.group(1))
                if model not in ROSTER:
                    raise ValueError("unexpected base DS3M model")
                source_models[model] = name
        if require_full and set(source_models) != ROSTER:
            raise ValueError("expected 730 recovered DS3M previews")
        ds3m, uv = _read_candidate_inventory(cand)
        sources = {}
        if source_report is not None:
            report = json.loads(Path(source_report).read_text(encoding="utf-8"))
            sources = {int(row["model_id"][1:]): row.get("source", "")
                       for row in report["per_model"]}
        substitutions = {}
        for model, dsname in sorted(ds3m.items()):
            source_ds = cand.read(dsname)
            triangles, _, _ = validate_model(source_ds)
            companion = cand.read(uv[model])
            unit = validate_uv(companion, triangles)
            # Historical C7 inferred UVs are never allowed into strict C62 QA.
            if unit and sources and sources.get(model) != "C62 complete source-derived candidate":
                continue
            if unit and not sources and mode == "unit-uv-qa":
                raise ValueError("source provenance report required for opt-in UV QA")
            if unit:
                substitutions[model] = (source_ds, companion)
        with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=5) as out:
            for name in names:
                match = PREVIEW.fullmatch(name)
                if not match:
                    out.writestr(name, base.read(name))
                    continue
                model = int(match.group(1))
                data = base.read(name)
                if mode == "unit-uv-qa" and model in substitutions:
                    data = substitutions[model][0]
                native, info = native_model(data)
                rows[f"p{model:03d}"] = info
                info["paired_unit_uv_qa"] = mode == "unit-uv-qa" and model in substitutions
                out.writestr(name, native)
                if info["paired_unit_uv_qa"]:
                    out.writestr(f"preview/p{model:03d}.p3uv", substitutions[model][1])
            # Preserve absence of P3MT/P3MR/P3SC files; never imply source sampler binding.
            out.writestr("C136_PRIVATE_STAGING_README.txt",
                "C136 original-source preview transport; all DS3M bytes 8..11 reserved zero.\n"
                "Unit-UV QA swaps exact DS3M/P3UV source pairs; sampler roles unresolved.\n"
                "No original-textured DS gameplay or 3DS parity is claimed.\n")
    result = {
        "mode": mode, "native_compatible_preview_models": len(rows),
        "available_candidate_pairs": len(ds3m),
        "source_unit_uv_candidates": len(substitutions),
        "activated_paired_unit_uv_qa": sum(r["paired_unit_uv_qa"] for r in rows.values()),
        "original_texture_material_bindings_verified": 0,
        "original_3ds_visual_parity_proven": False,
        "models": rows,
    }
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--candidates", type=Path, required=True)
    p.add_argument("--source-report", type=Path, required=True)
    p.add_argument("--mode", choices=("baseline", "unit-uv-qa"), default="baseline")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    result = build(args.base, args.candidates, args.output, mode=args.mode,
                   source_report=args.source_report)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "models"}, indent=2))


if __name__ == "__main__":
    main()
