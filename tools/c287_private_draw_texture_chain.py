#!/usr/bin/env python3
"""C287: join original C5 draw/material texture references to SHA-backed candidates.

No sampler roles, original GPU format or native P3PX binding is inferred.
Only private JSON inputs; no Nintendo data may enter public CI.
"""
import argparse
import collections
import json
import re
from pathlib import Path

from c286_private_format_consensus import _read_private_json, ROSTER, SHA

SCHEMA = "C287_PRIVATE_DRAW_TO_SOURCE_TEXTURE_CHAIN_V1"
C275 = "C275_PRIVATE_C5_DRAW_MATERIAL_REFERENCE_V1"
C279 = "C279_PRIVATE_C5_HEADER_TEXTURE_BASE_V1"
C286 = "C286_PRIVATE_C5_FORMAT_WORD_CONSENSUS_V1"


def _index(value, limit, label):
    if type(value) is not int or not 0 <= value < limit:
        raise ValueError("invalid " + label)
    return value


def _models(report, schema):
    if (not isinstance(report, dict) or not isinstance(report.get("summary"), dict) or
            report["summary"].get("schema") != schema or
            not isinstance(report.get("models"), list) or
            not 1 <= len(report["models"]) <= 730):
        raise ValueError("wrong or unbounded " + schema + " report")
    models = {}
    for row in report["models"]:
        if not isinstance(row, dict) or row.get("model_id") not in ROSTER:
            raise ValueError("invalid original source model")
        mid = row["model_id"]
        if mid in models:
            raise ValueError("duplicate original source model")
        models[mid] = row
    return models


def join(c275, c279, c286, require_full=False):
    draws = _models(c275, C275)
    textures = _models(c279, C279)
    if set(draws) != set(textures) or (require_full and set(draws) != ROSTER):
        raise ValueError("draw/texture model roster or full 730-model coverage mismatch")
    if (not isinstance(c286, dict) or not isinstance(c286.get("summary"), dict) or
            c286["summary"].get("schema") != C286 or
            not isinstance(c286.get("textures"), list) or
            len(c286["textures"]) > 4096):
        raise ValueError("wrong C286 candidate schema or size")
    candidates = {}
    for row in c286["textures"]:
        if not isinstance(row, dict):
            raise ValueError("malformed C286 candidate")
        mid, idx = row.get("model_id"), row.get("texture_index")
        if mid not in draws or type(idx) is not int or not 0 <= idx < 256:
            raise ValueError("C286 candidate for unknown model or index")
        key = (mid, idx)
        if key in candidates:
            raise ValueError("duplicate C286 candidate")
        if (row.get("gpu_format_verified") is not False or
                row.get("sampler_role_verified") is not False or
                row.get("native_p3px_binding_verified") is not False):
            raise ValueError("C286 candidate falsely asserts verified GPU/sampler binding")
        candidate = row.get("format_word_consensus_candidate")
        if candidate is not None and (type(candidate) is not str or not re.fullmatch(r"[A-Z0-9_]{1,64}", candidate)):
            raise ValueError("malformed C286 consensus hypothesis")
        candidates[key] = row
    result = []
    counts = collections.Counter()
    for mid in sorted(draws):
        d, t = draws[mid], textures[mid]
        source_sha = d.get("source_c5_sha256")
        if (type(source_sha) is not str or not SHA.fullmatch(source_sha) or
                t.get("source_c5_sha256") != source_sha):
            raise ValueError("C275/C279 full original C5 source SHA mismatch")
        mesh_count, mat_count, tex_count = (d.get(k) for k in
                                           ("mesh_count", "material_count", "source_texture_count"))
        if (type(mesh_count) is not int or not 1 <= mesh_count <= 4096 or
                type(mat_count) is not int or not 1 <= mat_count <= 256 or
                type(tex_count) is not int or not 1 <= tex_count <= 256 or
                not isinstance(t.get("records"), list) or len(t["records"]) != tex_count or
                not isinstance(d.get("draws"), list) or not 1 <= len(d["draws"]) <= 4096):
            raise ValueError("invalid original draw/material/texture table bounds")
        descriptors = t["records"]
        for i, tex in enumerate(descriptors):
            if (not isinstance(tex, dict) or tex.get("index") != i or
                    type(tex.get("source_sha256")) is not str or
                    not SHA.fullmatch(tex["source_sha256"]) or
                    type(tex.get("c73_sha_anchor")) is not bool or
                    type(tex.get("p3tm_metadata_corrob")) is not bool or
                    type(tex.get("opaque_format")) is not int):
                raise ValueError("invalid C279 source texture descriptor")
        seen_draws = set()
        joined = []
        for row in d["draws"]:
            if not isinstance(row, dict):
                raise ValueError("invalid original draw record")
            draw_id = row.get("draw_index")
            if type(draw_id) is not int or not 0 <= draw_id < 4096 or draw_id in seen_draws:
                raise ValueError("duplicate/invalid original draw index")
            seen_draws.add(draw_id)
            _index(row.get("mesh_index"), mesh_count, "source mesh index")
            _index(row.get("material_index"), mat_count, "source material index")
            refs, names = row.get("source_texture_reference_indices"), row.get("source_texture_reference_names")
            if (not isinstance(refs, list) or not isinstance(names, list) or
                    len(refs) != 2 or len(names) != 2):
                raise ValueError("invalid original texture reference slots")
            slots = []
            for slot, (index, name) in enumerate(zip(refs, names)):
                if index == 65535:
                    slots.append({"slot": slot, "source_texture_index": None,
                                  "status": "SOURCE_REFERENCE_ABSENT", "gpu_sampler_verified": False,
                                  "native_p3px_binding_verified": False})
                    continue
                _index(index, tex_count, "original source texture reference")
                if (type(name) is not str or not 1 <= len(name) <= 127 or
                        not name.isascii() or not name.isprintable()):
                    raise ValueError("invalid original texture reference name")
                tex = descriptors[index]
                c = candidates.get((mid, index))
                if c is not None and (c.get("source_sha256") != tex["source_sha256"] or
                        not tex["c73_sha_anchor"] or not tex["p3tm_metadata_corrob"] or
                        c.get("opaque_source_format") != tex["opaque_format"]):
                    raise ValueError("C286 candidate not tied to C279 source SHA/format")
                anchored = tex["c73_sha_anchor"] and tex["p3tm_metadata_corrob"]
                status = ("SOURCE_SHA_AND_C84_CANDIDATE" if anchored and c is not None else
                          "SOURCE_SHA_ANCHORED_NO_LOW_BPP_CANDIDATE" if anchored else
                          "SOURCE_REFERENCE_UNANCHORED")
                counts[status] += 1
                slots.append({"slot": slot, "source_texture_index": index,
                              "source_texture_name": name, "source_texture_sha256": tex["source_sha256"],
                              "source_opaque_format": tex["opaque_format"], "status": status,
                              "candidate_disposition": c["disposition"] if c is not None else None,
                              "candidate_hypothesis": c["format_word_consensus_candidate"] if c is not None else None,
                              "gpu_sampler_verified": False, "native_p3px_binding_verified": False})
            joined.append({"draw_index": draw_id, "mesh_index": row["mesh_index"],
                           "material_index": row["material_index"], "texture_reference_slots": slots,
                           "source_draw_material_reference_verified": True,
                           "gpu_sampler_verified": False, "native_p3px_binding_verified": False})
        counts["draws"] += len(joined)
        counts["models"] += 1
        result.append({"model_id": mid, "source_c5_sha256": source_sha, "draws": joined})
    return {"summary": {"schema": SCHEMA, **dict(sorted(counts.items())),
                        "source_draw_to_material_references_verified": True,
                        "gpu_sampler_roles_verified": 0,
                        "native_p3px_image_bindings_verified": 0,
                        "asset_integrated_emulator_verified": False, "release_ready": False},
            "models": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--c275-private-json", type=Path, required=True)
    parser.add_argument("--c279-private-json", type=Path, required=True)
    parser.add_argument("--c286-private-json", type=Path, required=True)
    parser.add_argument("--output-private-json", type=Path, required=True)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    from c275_private_draw_material_chain import write_private_report
    try:
        inputs = (args.c275_private_json, args.c279_private_json, args.c286_private_json)
        if args.output_private_json.resolve() in tuple(p.resolve() for p in inputs):
            raise ValueError("private output must differ from all input reports")
        report = join(*(_read_private_json(p) for p in inputs), require_full=args.require_full)
        write_private_report(args.output_private_json, report)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(1, "C287 original draw texture chain rejected: " + str(exc) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
