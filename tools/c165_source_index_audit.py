"""C165: audit original C5 index descriptors without inventing primitive order.

A face count or index descriptor is not a recovered index buffer. Reports
source mesh descriptor counts only; never certifies DS geometry bindings.
"""
import argparse
import json
import struct
import zipfile
from pathlib import Path
from c160_draw_pass_contract import parse_draws

def inspect_source(raw):
    meshes, draws = parse_draws(raw)
    index_start = struct.unpack_from("<I", raw, 0x40)[0]
    descriptors=[]
    for mesh in range(meshes):
        off=index_start+12*mesh
        first, second, packed=struct.unpack_from("<3I",raw,off)
        descriptors.append({"mesh":mesh,"descriptor_word0":first,
                            "descriptor_word1":second,"declared_indices":packed & 65535})
    return {"mesh_count":meshes,"draw_count":len(draws),
            "source_draw_triangles":sum(x[4] for x in draws),
            "index_descriptors":descriptors,
            "original_index_buffer_recovered":False,
            "original_primitive_order_verified":False,
            "geometry_binding_export_allowed":False}

def audit_archives(root):
    models={}
    for part in (1,2,3):
        path=root/f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip"
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if not name.startswith("decoded_c5/") or not name.endswith(".c5"):continue
                mid=Path(name).stem
                if mid in models:raise ValueError("duplicate model ID")
                models[mid]=inspect_source(z.read(name))
    expected={f"p{i:03d}" for i in range(734) if i not in (721,722,723,724)}
    if set(models)!=expected:raise ValueError("incomplete original C5 roster")
    return {"schema":"p3d-source-index-descriptor-audit-v1",
            "models":len(models),
            "meshes":sum(x["mesh_count"] for x in models.values()),
            "draws":sum(x["draw_count"] for x in models.values()),
            "source_draw_triangles":sum(x["source_draw_triangles"] for x in models.values()),
            "original_index_buffers_recovered":0,
            "verified_geometry_bindings":0,
            "native_renderer_integrated":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("private_archive_directory",type=Path)
    p.add_argument("private_output",type=Path)
    a=p.parse_args()
    result=audit_archives(a.private_archive_directory)
    a.private_output.parent.mkdir(parents=True,exist_ok=True)
    a.private_output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
