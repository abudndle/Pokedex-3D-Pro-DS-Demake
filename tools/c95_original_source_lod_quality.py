#!/usr/bin/env python3
"""C95 source-triangle LOD selection and private NitroFS diagnostic quality audit.

Only original source triangles may be selected. Area gain is a GEOMETRY metric;
it does not validate original 3DS GPU sampler, alpha, shading, or appearance.
Private generated P3MT color-name candidates must NEVER enter release NitroFS.
"""
import argparse
import json
import math
from pathlib import Path

from c92_diagnostic_textured_preview_audit import examine

MAX_DS_PREVIEW_FACES=600

def doubled_area(vertices, face):
    a,b,c=(vertices[i] for i in face)
    dx,dy,dz=(b[i]-a[i] for i in range(3))
    ex,ey,ez=(c[i]-a[i] for i in range(3))
    return math.sqrt((dy*ez-dz*ey)**2+(dz*ex-dx*ez)**2+(dx*ey-dy*ex)**2)

def select_source_faces(vertices, faces, take):
    """Return ordered ORIGINAL indices, never synthesized geometry.

    Partition source face order around the exact midpoint anchors of the
    former native 600-face sampler. Each interval contains that baseline
    face. Select its maximum-area ORIGINAL face; therefore summed selected
    source area cannot fall below midpoint sampling in any interval.
    """
    count=len(faces)
    if not 1<=take<=count or take>MAX_DS_PREVIEW_FACES:
        raise ValueError("invalid native source face budget")
    areas=[doubled_area(vertices,face) for face in faces]
    if not all(math.isfinite(a) and a>=0 for a in areas):
        raise ValueError("source has invalid triangle areas")
    anchors=[((2*i+1)*count)//(2*take) for i in range(take)]
    if len(set(anchors))!=take:raise ValueError("duplicated source sample anchors")
    selected=[]
    for i,anchor in enumerate(anchors):
        start=0 if i==0 else (anchors[i-1]+anchor)//2+1
        stop=count if i==take-1 else (anchor+anchors[i+1])//2+1
        if not start<=anchor<stop:raise ValueError("source face interval invalid")
        chosen=max(range(start,stop),key=lambda j:(areas[j],-j))
        if areas[chosen]<=1e-12:
            raise ValueError("source stratum has no nondegenerate original face")
        selected.append(chosen)
    if selected!=sorted(set(selected)):
        raise ValueError("selected original faces duplicate or reorder")
    improved=sum(areas[i] for i in selected)
    prior=sum(areas[i] for i in anchors)
    if improved+1e-10<prior:raise ValueError("surface area retention regressed")
    return selected,improved,prior,sum(areas)

def audit(private_stage,private_report,require_full=False):
    """Cross-check C95 source-surface metrics with existing C92 format auditor."""
    stage=examine(private_stage)
    data=json.loads(Path(private_report).read_text(encoding="utf-8"))
    rows=data.get("models",[])
    summary=data.get("summary",{})
    if not rows or len(rows)!=len({r["model_id"] for r in rows}):
        raise ValueError("source-model quality report empty/duplicated")
    if stage["diagnostic_models"]!=len(rows) or summary.get("models")!=len(rows):
        raise ValueError("original model stage and report roster differ")
    if stage["sampled_triangles"]!=sum(r["native_triangles"] for r in rows):
        raise ValueError("original model sampled triangles differ")
    if stage["material_ranges"]!=sum(r["material_ranges"] for r in rows):
        raise ValueError("native material range count differs")
    if summary.get("source_triangles")!=sum(r["original_triangles"] for r in rows):
        raise ValueError("source full geometry triangle count differs")
    for r in rows:
        if (not 1<=r["original_mesh_groups"]<=r["native_triangles"]<=MAX_DS_PREVIEW_FACES
            or r["area_retention_midpoint"]>r["area_retention_new"]+1e-10
            or r["mesh_material_reference"]!="C90_VERIFIED"
            or r["gpu_color_sampler_role"]!="C92_PROVISIONAL"
            or r["native_model_visual_fidelity_certified"] is not False):
            raise ValueError("invalid surface retention or false source-material claim")
    if summary.get("original_gpu_sampler_roles_proven") is not False or summary.get("native_visual_accuracy_verified") is not False:
        raise ValueError("original 3DS shader/visual accuracy cannot be inferred from area")
    if require_full and (stage["diagnostic_models"]!=500
           or stage["sampled_triangles"]!=300000
           or stage["original_derived_color_images"]!=1152
           or stage["material_ranges"]!=2147
           or summary["source_triangles"]!=2396500):
        raise ValueError("original C95 500-model source batch incomplete")
    return {"original_source_models":len(rows),
            "original_source_triangles":summary["source_triangles"],
            "ds_preview_triangles":stage["sampled_triangles"],
            "material_ranges":stage["material_ranges"],
            "original_derived_color_candidates":stage["original_derived_color_images"],
            "mean_source_area_baseline":sum(r["area_retention_midpoint"] for r in rows)/len(rows),
            "mean_source_area_selected":sum(r["area_retention_new"] for r in rows)/len(rows),
            "original_models_with_surface_regression":0,
            "original_gpu_sampler_roles_verified":False,
            "native_visual_parity_verified":False,
            "normal_release_approved":False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True)
    parser.add_argument("--require-full-c95",action="store_true")
    a=parser.parse_args()
    try:print(json.dumps(audit(a.stage,a.report,a.require_full_c95),indent=2))
    except (OSError,KeyError,ValueError,IndexError,TypeError) as e:
        parser.exit(1,"C95 original-source preview rejected: %s\n"%e)
if __name__=="__main__":main()
