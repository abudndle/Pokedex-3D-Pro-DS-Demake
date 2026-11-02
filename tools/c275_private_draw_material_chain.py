#!/usr/bin/env python3
"""C275: source-C5 draw -> material -> shader/C75 texture *reference* evidence.

This never identifies GPU sampler roles, maps C75 references to P3PX pixels,
or produces a diffuse-texture binding. Private C5/C75 data and the report
must stay off public GitHub/CI; tests use synthetic fixtures exclusively.
"""
import argparse
import collections
import csv
import hashlib
import json
import os
import re
import stat
import tempfile
import zipfile
from pathlib import Path

from c88_original_material_references import parse as parse_materials
from c90_original_draw_material_audit import draws as parse_draws, primary_map

MEMBER = re.compile(r"decoded_c5/(p\d{3})\.c5\Z")
MODEL = re.compile(r"p\d{3}\Z")
ROSTER = {f"p{i:03d}" for i in range(734) if i not in (721, 722, 723, 724)}
MAX_MODEL = 64 * 1024 * 1024
MAX_TOTAL = 1024 * 1024 * 1024
MAX_ENTRIES = 2048
MAX_C75_CSV = 16 * 1024 * 1024
SCHEMA = "C275_PRIVATE_C5_DRAW_MATERIAL_REFERENCE_V1"


def join(model_id, source_c5, c75_rows):
    """Independently parse both original C5 tables, then join by material ID."""
    if model_id not in ROSTER or not MODEL.fullmatch(model_id):
        raise ValueError("invalid original model roster ID")
    if not isinstance(source_c5, bytes) or len(source_c5) > MAX_MODEL:
        raise ValueError("original C5 source size invalid")
    materials, metadata = parse_materials(source_c5, c75_rows)
    if metadata["ntex"] != len(c75_rows):
        raise ValueError("C75 source texture roster required for every reference")
    draw_rows, mesh_count = parse_draws(source_c5, model_id)
    if not materials or len(materials) != metadata["nmaterial"]:
        raise ValueError("original material table incomplete")
    if {r["mesh_index"] for r in draw_rows} != set(range(mesh_count)):
        raise ValueError("original mesh without draw record")
    mapping, unresolved = primary_map(draw_rows, mesh_count)
    result = []
    for draw in draw_rows:
        mat = materials[draw["material_index"]]
        # C88 tuple: index, name, shader index, shader declaration,
        # texture0, texture1, texture name0, texture name1, status, binding.
        if mat[0] != draw["material_index"] or mat[8] != "VERIFIED_C5_C75":
            raise ValueError("unverified original C5/C75 material reference")
        result.append({
            "draw_index": draw["draw_index"],
            "mesh_index": draw["mesh_index"],
            "pass_code": draw["pass_code"],
            "triangle_count": draw["triangle_count"],
            "material_index": mat[0],
            "source_material_name": mat[1],
            "shader_index": mat[2],
            "shader_declaration": mat[3],
            "source_texture_reference_indices": [mat[4], mat[5]],
            "source_texture_reference_names": [mat[6], mat[7]],
            "provenance": "VERIFIED_C5_DRAW_AND_MATERIAL_C75_REFERENCES",
            "gpu_sampler_roles_verified": False,
            "p3px_image_binding_verified": False,
        })
    return {
        "schema": SCHEMA,
        "model_id": model_id,
        "source_c5_sha256": hashlib.sha256(source_c5).hexdigest(),
        "mesh_count": mesh_count,
        "material_count": metadata["nmaterial"],
        "source_texture_count": metadata["ntex"],
        "draws": result,
        "unique_primary_mesh_materials": len(mapping),
        "unresolved_primary_mesh_indices": unresolved,
        "verified_gpu_sampler_roles": 0,
        "verified_p3px_image_bindings": 0,
        "release_ready": False,
    }


def read_c75(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > MAX_C75_CSV:
        raise ValueError("C75 CSV absent or over budget")
    result = collections.defaultdict(list)
    with path.open(newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        required = {"model_id", "index", "original_texture_name", "original_name_absolute_offset"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("C75 CSV missing required columns")
        for row in reader:
            mid = row["model_id"]
            if mid not in ROSTER:
                raise ValueError("unexpected C75 model ID")
            try:
                index = int(row["index"])
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid C75 texture index") from exc
            if not 0 <= index < 256:
                raise ValueError("C75 texture index out of range")
            result[mid].append(row)
            if len(result[mid]) > 256:
                raise ValueError("C75 texture count over budget")
    for mid, rows in result.items():
        rows.sort(key=lambda x: int(x["index"]))
        if [int(r["index"]) for r in rows] != list(range(len(rows))):
            raise ValueError(f"{mid}: duplicate or missing C75 texture index")
    return result


def audit(private_root, c75_csv, require_full=False):
    """Read bounded private C56 ZIP parts, return private evidence and summary."""
    textures = read_c75(c75_csv)
    root = Path(private_root)
    models = {}
    consumed = 0
    for part in (1, 2, 3):
        path = root / f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip"
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > MAX_ENTRIES:
                raise ValueError("C5 archive entry budget exceeded")
            for info in members:
                if info.is_dir():
                    continue
                mode = info.external_attr >> 16
                if stat.S_IFMT(mode) == stat.S_IFLNK:
                    raise ValueError("symlinked C5 archive member")
                match = MEMBER.fullmatch(info.filename)
                if not match:
                    if info.filename.lower().endswith(".c5"):
                        raise ValueError("unexpected C5 source member")
                    continue
                mid = match.group(1)
                if mid not in ROSTER or mid in models:
                    raise ValueError("duplicate or unexpected original C5 model")
                if not 0 < info.file_size <= MAX_MODEL or consumed + info.file_size > MAX_TOTAL:
                    raise ValueError("private C5 archive byte budget exceeded")
                consumed += info.file_size
                raw = archive.read(info)
                if len(raw) != info.file_size:
                    raise ValueError("truncated original C5 archive member")
                models[mid] = join(mid, raw, textures.get(mid, []))
    if not models or set(textures) - set(models):
        raise ValueError("C75 references without original C5 source")
    if require_full and set(models) != ROSTER:
        raise ValueError("expected all 730 original C5 models")
    ordered = [models[k] for k in sorted(models)]
    summary = {
        "schema": SCHEMA,
        "original_models_checked": len(ordered),
        "source_draw_material_links": sum(len(m["draws"]) for m in ordered),
        "source_draw_texture_reference_slots": sum(
            sum(x != 65535 for x in row["source_texture_reference_indices"])
            for m in ordered for row in m["draws"]),
        "models_with_unresolved_primary_meshes": sum(
            bool(m["unresolved_primary_mesh_indices"]) for m in ordered),
        "verified_gpu_sampler_roles": 0,
        "verified_p3px_image_bindings": 0,
        "private_original_source_required": True,
        "release_ready": False,
    }
    return {"summary": summary, "models": ordered}


def write_private_report(output, report):
    """Atomically replace private JSON with mode 0600; refuse link targets."""
    path = Path(output)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise ValueError("private report directory must exist and not be a symlink")
    if path.is_symlink() or (path.exists() and (
            not path.is_file() or path.stat().st_nlink != 1)):
        raise ValueError("unsafe private report destination")
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".c275-", suffix=".tmp", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--texture-reference-csv", type=Path, required=True)
    parser.add_argument("--output-private-json", type=Path, required=True)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    try:
        report = audit(args.private_root, args.texture_reference_csv, args.require_full)
        write_private_report(args.output_private_json, report)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            zipfile.BadZipFile) as exc:
        parser.exit(1, "C275 private material chain rejected: " + str(exc) + "\n")
    # Only aggregate counts go to stdout; never print source names or hashes.
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
