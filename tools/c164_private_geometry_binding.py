"""C164: private-only verified geometry binding export.

Consumes independent source-order evidence. Never infers geometry order from
draw order, face counts, or a DS preview. Output remains non-renderable metadata.
"""
import argparse
import json
from pathlib import Path
from c163_geometry_draw_gate import validate_geometry_binding

def build_verified_binding(manifest, evidence, triangle_count):
    if not isinstance(evidence, dict) or evidence.get("schema") != "p3d-geometry-evidence-v1":
        raise ValueError("missing independent geometry evidence schema")
    if evidence.get("model_id") != manifest.get("model_id"):
        raise ValueError("model identity mismatch")
    if evidence.get("source_order_method") not in ("original-index-buffer", "original-primitive-trace"):
        raise ValueError("unsupported source order verification method")
    if evidence.get("verified") is not True:
        raise ValueError("source ordering not verified")
    bindings = evidence.get("bindings")
    result = validate_geometry_binding(manifest, bindings, triangle_count)
    if result["triangles_bound"] != triangle_count:
        raise ValueError("unassigned geometry triangles")
    return {"schema":"p3d-verified-geometry-binding-v1",
            "model_id":manifest["model_id"],"triangle_count":triangle_count,
            "bindings":bindings,"source_order_method":evidence["source_order_method"],
            "sampler_roles_verified":False,"native_renderer_integrated":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest",type=Path)
    p.add_argument("independent_evidence",type=Path)
    p.add_argument("triangle_count",type=int)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    m=json.loads(a.manifest.read_text())
    e=json.loads(a.independent_evidence.read_text())
    result=build_verified_binding(m,e,a.triangle_count)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
if __name__=="__main__":main()
