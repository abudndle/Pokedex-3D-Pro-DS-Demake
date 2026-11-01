#!/usr/bin/env python3
"""C161: export source-provenance draw-pass metadata for private ROM staging.

This is NOT a DS rendering or texture-binding format. Do not include source
C5 files, texture bytes, private SHA rosters, or unverified sampler claims.
"""
import argparse
import json
import re
from pathlib import Path
from c160_draw_pass_contract import parse_draws, classify_meshes

MODEL_NAME = re.compile(r"p(?:[0-6][0-9]{2}|7(?:[0-2][0-9]|3[0-3]))")
PASS_NAME = {0x0c02: "primary", 0x0c01: "secondary"}

def build_manifest(model_id, raw):
    if not MODEL_NAME.fullmatch(model_id) or model_id in {"p721","p722","p723","p724"}:
        raise ValueError("invalid model roster ID")
    meshes, rows = parse_draws(raw)
    classified = classify_meshes(meshes, rows)
    return {
        "schema": "p3d-source-draw-pass-v1",
        "model_id": model_id,
        "mesh_count": meshes,
        "draws": [
            {"order": order, "mesh": mesh, "material": material,
             "pass": PASS_NAME[mode], "triangles": faces}
            for order, mesh, material, mode, faces in rows
        ],
        "secondary_only_meshes": [
            m["mesh"] for m in classified if not m["primary_verified"]
        ],
        "sampler_roles_verified": False,
        "native_renderer_integrated": False,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("model_id")
    p.add_argument("source_c5", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    result = build_manifest(args.model_id, args.source_c5.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")

if __name__ == "__main__":
    main()
