#!/usr/bin/env python3
"""C142: audit original C5 pointer-indexed track records, WITHOUT guessing roles.

Read private C56 archives and original validated SHA-256 records. C5 header
field 0x1a holds the track table count, 0x48/0x4c table bounds, 0x64 string
section start, 0x68 numeric-data section. Each table entry is four little-
endian u32 words (data pointer + THREE opaque control words). Table pointers
must be strictly increasing in the section. Source records are NOT proof of
any specific face, material, shader or sampler assignment.
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

from c140_c5_shader_inventory import ROSTER, PART_RANGES, reference_rows, parse_declarations
from c141_c5_mesh_provenance import preview_header

MODEL_NAME = re.compile(r"decoded_c5/p([0-9]{3})\.c5\Z")
PREVIEW_NAME = re.compile(r"preview/p([0-9]{3})\.ds3m\Z")
MAX_C5_BYTES = 16 * 1024 * 1024
MAX_TRACKS = 512


def parse_source_tracks(data: bytes, *, include_records=True):
    """Recover exact physical record spans with SHA proof, not semantic roles."""
    if len(data) < 0x78 or data[:2] != b"\xc5\x78":
        raise ValueError("not a C5 0x78 model container")
    count = struct.unpack_from("<H", data, 0x1a)[0]
    table_start, table_end, strings_start, numeric_start = (
        struct.unpack_from("<I", data, x)[0]
        for x in (0x48, 0x4c, 0x64, 0x68)
    )
    if not 0 < count <= MAX_TRACKS:
        raise ValueError("invalid original C5 track count")
    if not (0x78 <= table_start < table_end <= numeric_start < strings_start < len(data)):
        raise ValueError("invalid C5 track/string/numeric section boundaries")
    if table_end - table_start != count * 16:
        raise ValueError("C5 original track descriptor count/size mismatch")
    pointers = []
    controls = []
    for i in range(count):
        location, a, b, c = struct.unpack_from("<4I", data, table_start + i * 16)
        if (location < numeric_start or location >= strings_start or
                location % 4 or (pointers and location <= pointers[-1])):
            raise ValueError("invalid, duplicate or unordered C5 track data pointer")
        pointers.append(location)
        controls.append((a, b, c))
    if strings_start - pointers[-1] < 4:
        raise ValueError("final C5 track payload truncated")
    rows = []
    spans = collections.Counter()
    source_bytes = 0
    h = hashlib.sha256()
    for i, (location, control) in enumerate(zip(pointers, controls)):
        end = pointers[i+1] if i+1 < count else strings_start
        n = end - location
        if n <= 0 or n > 65536 or n % 4:
            raise ValueError("invalid C5 track payload span")
        raw = data[location:end]
        h.update(raw)
        source_bytes += n
        spans[n] += 1
        if include_records:
            rows.append({
                "record": i,
                "source_table_offset": table_start+i*16,
                "source_payload_start": location,
                "source_payload_end": end,
                "payload_bytes": n,
                "payload_sha256": hashlib.sha256(raw).hexdigest(),
                "control_words_opaque": [f"0x{x:08x}" for x in control],
                "source_face_material_link_verified": False,
                "source_shader_sampler_link_verified": False,
            })
    return {
        "source_track_records": count,
        "table_start": table_start,
        "table_end": table_end,
        "numeric_section_start": numeric_start,
        "shader_string_section_start": strings_start,
        "track_payload_bytes": source_bytes,
        "track_payload_aggregate_sha256": h.hexdigest(),
        "record_span_histogram": {str(k): spans[k] for k in sorted(spans)},
        "source_track_records_are_material_bindings": False,
        "records": rows,
    }


def audit(parts, decoder_bundle, c140_report, c141_report, private_nitrofs, *, include_records=True):
    if len(parts) != 3:
        raise ValueError("expected three ordered private C56 source archives")
    original = reference_rows(decoder_bundle)
    shader = json.loads(Path(c140_report).read_text(encoding="utf-8"))
    mesh = json.loads(Path(c141_report).read_text(encoding="utf-8"))
    if shader.get("models_verified") != 730 or mesh.get("original_c56_models_verified") != 730:
        raise ValueError("private shader/mesh provenance inventories incomplete")
    result = {}
    histogram = collections.Counter()
    total_track_bytes = total_tracks = total_shader_records = total_meshes = 0
    with zipfile.ZipFile(private_nitrofs) as native:
        names = native.namelist()
        if len(names) != len(set(names)):
            raise ValueError("ambiguous private preview ZIP path")
        if {int((m:=PREVIEW_NAME.fullmatch(name)).group(1)) for name in names if (m:=PREVIEW_NAME.fullmatch(name))} != ROSTER:
            raise ValueError("native private NitroFS missing original previews")
        for idx, archive_path in enumerate(parts):
            first, last = PART_RANGES[idx]
            with zipfile.ZipFile(archive_path) as z:
                files = z.infolist()
                if len(files) != len({x.filename for x in files}):
                    raise ValueError("duplicate source C5 file paths")
                for member in files:
                    match = MODEL_NAME.fullmatch(member.filename)
                    if not match:
                        raise ValueError("unexpected source archive member")
                    model = int(match.group(1))
                    label = f"p{model:03d}"
                    if model not in ROSTER or not first <= model <= last or label in result:
                        raise ValueError("invalid, duplicated or displaced C5 source model")
                    if member.file_size < 0x78 or member.file_size > MAX_C5_BYTES:
                        raise ValueError("source C5 size outside original recovery budget")
                    data = z.read(member)
                    digest = hashlib.sha256(data).hexdigest()
                    ref = original[label]
                    if digest != ref["sha256"] or len(data) != int(ref["decoded_bytes"]):
                        raise ValueError(f"original C56 hash/size mismatch: {label}")
                    if shader["models"][label]["source_c5_sha256"] != digest or mesh["models"][label]["source_sha256"] != digest:
                        raise ValueError(f"C140/C141 source identity mismatch: {label}")
                    decl = parse_declarations(data)
                    n_mesh = mesh["models"][label]["source_mesh_groups"]
                    if len(decl) != len(shader["models"][label]["shader_declarations"]) or n_mesh < 1:
                        raise ValueError(f"C140/C141 source counts incompatible: {label}")
                    tri, total = preview_header(native.read(f"preview/{label}.ds3m"))
                    if total != mesh["models"][label]["source_triangle_count"] or tri != mesh["models"][label]["preview_triangles"]:
                        raise ValueError(f"private source preview does not match verified C141 metadata: {label}")
                    tracks = parse_source_tracks(data, include_records=include_records)
                    for width, count in tracks["record_span_histogram"].items():
                        histogram[int(width)] += count
                    total_track_bytes += tracks["track_payload_bytes"]
                    total_tracks += tracks["source_track_records"]
                    total_shader_records += len(decl)
                    total_meshes += n_mesh
                    result[label] = {"source_sha256": digest,
                                     "original_shader_declarations": len(decl),
                                     "source_mesh_groups": n_mesh,
                                     "native_preview_triangles": tri,
                                     **tracks}
    if set(result) != set(original):
        raise ValueError("C56 source roster incomplete")
    return {
        "c56_models_verified": len(result),
        "source_track_record_details_included": include_records,
        "c140_shader_declarations_cross_verified": total_shader_records,
        "c141_source_mesh_groups_cross_verified": total_meshes,
        "c142_pointer_indexed_source_records": total_tracks,
        "c142_source_track_payload_bytes": total_track_bytes,
        "c142_span_distribution": {str(n): histogram[n] for n in sorted(histogram)},
        "source_track_meanings_resolved": False,
        "original_face_to_material_indices_verified": 0,
        "source_material_to_shader_bindings_verified": 0,
        "original_sampler_roles_verified": 0,
        "certified_original_textured_models": 0,
        "private_preview_source_count_verified": len(result),
        "scope": "Exact opaque 16-byte C5 track records and ordered payload bytes with SHA-256; NOT C5 material/face/texture mappings",
        "models": {k:result[k] for k in sorted(result)},
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--parts", nargs=3, type=Path, required=True)
    p.add_argument("--decoder-bundle", type=Path, required=True)
    p.add_argument("--c140-report", type=Path, required=True)
    p.add_argument("--c141-report", type=Path, required=True)
    p.add_argument("--nitrofs", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--summary-only", action="store_true",
                   help="skip 79k individual payload hashes/rows; retain original archive, aggregate and per-model verification")
    args = p.parse_args()
    output = audit(args.parts, args.decoder_bundle, args.c140_report, args.c141_report, args.nitrofs,
                   include_records=not args.summary_only)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    if args.report.exists():
        p.error("refusing to overwrite existing private report")
    args.report.write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in output.items() if k not in ("models", "c142_span_distribution")},indent=2))


if __name__ == "__main__":
    main()