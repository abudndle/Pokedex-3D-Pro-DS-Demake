#!/usr/bin/env python3
"""C141: verify source C5 mesh-group index bounds against staged DS3M previews.

Private-input research. A mesh group is NOT automatically a material range:
original C5 material/shader indices and sampler roles remain unresolved.
An optional explicit private-only rewrite repairs DS3M source-face COUNT metadata,
never its triangle bytes, UVs, textures or shader roles.
"""
import argparse
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path

from c140_c5_shader_inventory import PART_RANGES, ROSTER, reference_rows
from c5_dual_table_parser import parse
from validate_c56 import assess

MODEL_NAME = re.compile(r"decoded_c5/p([0-9]{3})\.c5\Z")
PREVIEW_NAME = re.compile(r"preview/p([0-9]{3})\.ds3m\Z")
MAX_C5_BYTES = 16 * 1024 * 1024


def preview_header(data):
    if len(data) < 16:
        raise ValueError("truncated DS3M preview")
    magic, version, count, reserved, source_faces = struct.unpack_from("<4sHHII", data)
    if (magic != b"DS3M" or version not in (1, 2) or
            not 1 <= count <= 600 or reserved != 0 or source_faces < count or
            source_faces > 0x7fffffff or
            len(data) != 16 + count * (21 if version == 2 else 18)):
        raise ValueError("preview does not meet native DS3M contract")
    return count, source_faces


def read_source_meshes(parts, bundle):
    if len(parts) != 3:
        raise ValueError("exactly three ordered C56 source archives required")
    references = reference_rows(bundle)
    result = {}
    for idx, path in enumerate(parts):
        first, last = PART_RANGES[idx]
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if len(set(names)) != len(names):
                raise ValueError("duplicate C56 original source names")
            for info in z.infolist():
                match = MODEL_NAME.fullmatch(info.filename)
                if not match:
                    raise ValueError("unexpected original C56 archive member")
                model = int(match.group(1))
                label = f"p{model:03d}"
                if model not in ROSTER or not first <= model <= last or label in result:
                    raise ValueError("displaced or duplicate original C56 model")
                if not 0 < info.file_size <= MAX_C5_BYTES:
                    raise ValueError("C5 source byte budget exceeded")
                data = z.read(info)
                expected = references[label]
                digest = hashlib.sha256(data).hexdigest()
                if (len(data) != int(expected["decoded_bytes"]) or
                        digest != expected["sha256"]):
                    raise ValueError(f"C5 hash/size mismatch for {label}")
                status, flags, serious, parsed = assess(data)
                if (serious or status != expected["status"] or
                        flags != int(expected["0x26_descriptor_flags"]) or
                        len(parsed["first_table"]) != int(expected["primary_descriptor_count"])):
                    raise ValueError(f"C5 structural status changed for {label}")
                first_table, second_table = parsed["first_table"], parsed["second_table"]
                if not first_table or len(first_table) != len(second_table):
                    raise ValueError("C5 vertex/index descriptor pairing missing")
                cursor = 0
                groups = []
                for mesh_id, (vertex, index) in enumerate(zip(first_table, second_table)):
                    count = index["low16"]
                    if (not count or count % 3 or not vertex["record_count"] or
                            not index["in_file"] or not vertex["in_file"]):
                        raise ValueError(f"C5 malformed mesh/index descriptor {label}")
                    triangles = count // 3
                    groups.append({"source_mesh_group": mesh_id,
                                   "source_first_triangle": cursor,
                                   "source_triangles": triangles,
                                   "source_vertex_records": vertex["record_count"],
                                   "source_vertex_stride_low8": vertex["low_byte_of_upper16"],
                                   "source_mesh_material_binding_verified": False})
                    cursor += triangles
                result[label] = {"source_sha256": digest,
                                 "c56_status": status,
                                 "source_mesh_groups": len(groups),
                                 "source_triangle_count": cursor,
                                 "source_vertex_record_count": sum(v["record_count"] for v in first_table),
                                 "mesh_group_spans": groups}
    if set(result) != {f"p{i:03d}" for i in ROSTER}:
        raise ValueError("incomplete 730-model C5 source index inventory")
    return result


def audit(parts, bundle, preview_zip):
    sources = read_source_meshes(parts, bundle)
    mismatches = []
    with zipfile.ZipFile(preview_zip) as z:
        names = z.namelist()
        if len(set(names)) != len(names):
            raise ValueError("duplicate private NitroFS entries")
        entries = {name: int(match.group(1)) for name in names
                   if (match := PREVIEW_NAME.fullmatch(name))}
        if set(entries.values()) != ROSTER:
            raise ValueError("private NitroFS does not contain 730 native DS3M previews")
        for name, model in sorted(entries.items()):
            label = f"p{model:03d}"
            n, declared = preview_header(z.read(name))
            source = sources[label]
            count = source["source_triangle_count"]
            if count < n or count > 0x7fffffff:
                raise ValueError(f"source C5 face count impossible for {label}")
            source["preview_triangles"] = n
            source["preview_declared_source_triangles"] = declared
            source["source_face_count_matches_preview"] = count == declared
            if count != declared:
                mismatches.append({"model": label,
                                   "native_preview_triangles": n,
                                   "preview_declared_source_triangles": declared,
                                   "original_C5_index_descriptor_triangles": count,
                                   "reason": "source index-descriptor count differs from DS3M metadata"})
    return {
        "original_c56_models_verified": len(sources),
        "native_preview_models_checked": len(sources),
        "source_mesh_groups_total": sum(x["source_mesh_groups"] for x in sources.values()),
        "source_face_count_matches": len(sources) - len(mismatches),
        "source_face_count_mismatches": mismatches,
        "original_face_to_material_indices_verified": 0,
        "original_material_to_shader_bindings_verified": 0,
        "original_sampler_roles_verified": 0,
        "certified_original_textured_models": 0,
        "native_texmap_sidecars_produced": 0,
        "source_mesh_groups_are_not_material_groups": True,
        "models": sources,
    }


def repair_preview_source_counts(preview_zip, new_zip, report, allowed):
    """Modify only 4-byte source count header for expected strict C5 mismatches."""
    source_path, target = Path(preview_zip), Path(new_zip)
    if source_path.resolve() == target.resolve() or target.exists():
        raise ValueError("refusing to overwrite private original package")
    changes = {row["model"]: row for row in report["source_face_count_mismatches"]}
    if not changes or set(changes) != set(allowed):
        raise ValueError("unexpected source count mismatches; refuse private repair")
    for label in changes:
        if report["models"][label]["c56_status"] != "strict_valid":
            raise ValueError("cannot repair an unresolved C5 descriptor warning")
    with zipfile.ZipFile(source_path) as source, zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=5) as out:
        for info in source.infolist():
            name = info.filename
            data = source.read(info)
            match = PREVIEW_NAME.fullmatch(name)
            if match:
                label = f"p{int(match.group(1)):03d}"
                if label in changes:
                    count, old = preview_header(data)
                    if old != changes[label]["preview_declared_source_triangles"]:
                        raise ValueError("private preview changed after audit")
                    data = data[:12] + struct.pack("<I", changes[label]["original_C5_index_descriptor_triangles"]) + data[16:]
                    assert preview_header(data)[0] == count
            out.writestr(name, data)
    with zipfile.ZipFile(target) as z:
        if z.testzip() is not None:
            raise ValueError("private repaired ZIP CRC verification failed")
    return {"private_corrected_archive": target.name,
            "repaired_source_triangle_metadata": sorted(changes),
            "geometry_vertices_modified": False,
            "original_material_binding_verified": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--parts", type=Path, nargs=3, required=True)
    p.add_argument("--decoder-bundle", type=Path, required=True)
    p.add_argument("--nitrofs", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--repair-output", type=Path)
    p.add_argument("--expected-mismatch", action="append", default=[])
    args = p.parse_args()
    report = audit(args.parts, args.decoder_bundle, args.nitrofs)
    if args.repair_output:
        report["private_repair"] = repair_preview_source_counts(
            args.nitrofs, args.repair_output, report, args.expected_mismatch)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "models"}, indent=2))


if __name__ == "__main__":
    main()