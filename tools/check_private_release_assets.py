#!/usr/bin/env python3
"""Audit privately staged original-derived DS game assets.

Only --release is a gate. It deliberately rejects partial source assets and
does not claim visual parity from the mere existence of files.
"""
import argparse
import json
import pathlib
import struct
import zlib
import subprocess
import sys
import zipfile

# All native P3DPage destinations require their original recovered lower-screen art.
# Keep in exact enum order: P3D_PAGE_RECORDS is index 10.
GUI_PAGES=("home","dex","search","moves","types","favorites","challenge","settings","album","ar","records")
MODEL_IDS=tuple(i for i in range(734) if i not in (721,722,723,724))
assert len(MODEL_IDS)==730

class Assets:
    def __init__(self,path):
        self.path=path
        self.archive=zipfile.ZipFile(path) if path.is_file() else None
        if self.archive is None and not path.is_dir():
            raise ValueError("asset root must be a directory or ZIP")
        self.names=set(self.archive.namelist()) if self.archive else None
    def exists(self,name):
        return name in self.names if self.archive else (self.path/name).is_file()
    def read(self,name):
        return self.archive.read(name) if self.archive else (self.path/name).read_bytes()
    def length(self,name):
        return self.archive.getinfo(name).file_size if self.archive else (self.path/name).stat().st_size
    def close(self):
        if self.archive:self.archive.close()

def audit(src):
    invalid=[]
    missing=[]
    def check(name,predicate,reason):
        if not src.exists(name):
            missing.append(name)
        elif not predicate(src,name):
            invalid.append(name+": "+reason)
    # A faithful dual-screen port needs independently recovered top AND
    # bottom artwork for every original UI page; never copy one screen onto
    # the other or mark a developer text fallback as a release-complete UI.
    for screen in (0,1):
        for i,name in enumerate(GUI_PAGES):
            check(f"ui/pages/t{screen}_{i:02d}_{name}.rgb555",
                  lambda a,p:a.length(p)==256*192*2,
                  "not a full DS 256x192 16-bit page")
    # The 3D Dex uses a separate source-derived alpha mask for the HUD:
    # require both real opaque UI pixels and the transparent model viewport.
    # File presence alone is not proof of the recovered 3DS composition.
    def dex_overlay(a,p):
        if a.length(p)!=256*192*2:return False
        data=a.read(p)
        return (any(data[i]&0x80 for i in range(1,len(data),2))
                and any(not(data[i]&0x80) for i in range(1,len(data),2)))
    check("ui/pages/t1_01_dex_overlay.rgb555",dex_overlay,
          "original 3D Dex HUD must have opaque UI and transparent model cutout")
    def dex(a,p):
        if a.length(p)!=8+649*256:return False
        return a.read(p)[:8]==struct.pack("<4sHH",b"P3DX",1,649)
    check("data/dex_en.p3dx",dex,"P3DX 649-entry file invalid")
    def moves(a,p):
        if a.length(p)<8+4*560:return False
        b=a.read(p)
        if b[:8]!=struct.pack("<4sHH",b"P3DM",1,559):return False
        indexes=struct.unpack_from("<560I",b,8)
        return indexes[0]==8+4*560 and indexes[-1]==len(b) and all(
            7<=indexes[i+1]-indexes[i]<=2048 for i in range(559))
    check("moves.p3dm",moves,"P3DM 559-entry seek table invalid")
    def source_material_map(a,p,model_id):
        """Check C90 P3MR original C5 provenance before native use."""
        b=a.read(p)
        if len(b)<16:return False
        magic,version,mid,triangles,nranges,crc=struct.unpack_from("<4s4HI",b,0)
        if magic!=b"P3MR" or version!=1 or mid!=model_id or not 1<=triangles<=600 or not 1<=nranges<=64:
            return False
        payload=b[16:]
        if len(payload)!=nranges*12 or zlib.crc32(payload)!=crc:
            return False
        cursor=0
        for i in range(nranges):
            first,count,mat,t0,t1,mode=struct.unpack_from("<6H",payload,i*12)
            if first!=cursor or count==0 or count>triangles-cursor or mat>255 or mode!=0x0c02:
                return False
            cursor+=count
        return cursor==triangles
    def source_shader_caps(a,p,model_id):
        """Verify source C5 shader declaration provenance, never sampler roles."""
        b=a.read(p)
        if len(b)<16:return False
        magic,version,mid,nrecords,reserved,crc=struct.unpack_from("<4s4HI",b,0)
        if (magic!=b"P3SC" or version!=2 or mid!=model_id or reserved!=0 or
                not 1<=nrecords<=256 or len(b)!=16+nrecords*10 or
                zlib.crc32(b[16:])!=crc):
            return False
        for i in range(nrecords):
            mat,shader,t0,t1,flags=struct.unpack_from("<5H",b,16+10*i)
            if mat!=i or flags&~7:return False
        return True
    categories={
        "mesh_previews":"preview/p%03d.ds3m",
        "verified_uv":"preview/p%03d.p3uv",
        "verified_material_bindings":"materials/p%03d.p3mt",
        "original_texture_manifests":"materials/p%03d.p3tx",
        "original_texture_catalogs":"catalogs/p%03d.p3tm",
        "source_C5_material_provenance":"materials/p%03d.p3mr",
        "source_C5_shader_capabilities":"materials/p%03d.p3sc"
    }
    counts={}
    for category,pattern in categories.items():
        count=0
        for ident in MODEL_IDS:
            path=pattern%ident
            if src.exists(path):
                count+=1
                if category=="source_C5_shader_capabilities":
                    if not source_shader_caps(src,path,ident):
                        invalid.append(path+": invalid C5 shader capability declarations or CRC")
                elif category=="source_C5_material_provenance":
                    if not source_material_map(src,path,ident):
                        invalid.append(path+": invalid C5 material provenance, counts or CRC")
                elif src.length(path)==0:
                    invalid.append(path+": empty")
        counts[category]=count
    texture_count=0
    for ident in MODEL_IDS:
        prefix=f"textures/p{ident:03d}/"
        if src.archive is not None:
            texture_count+=sum(n.startswith(prefix) and n.endswith(".p3px") for n in src.names)
        else:
            texture_count+=len(list((src.path/prefix).glob("t*.p3px")))
    counts["original_derived_texture_payloads"]=texture_count
    for category in categories:
        if counts[category]<len(MODEL_IDS):
            missing.append(f"{category}: {len(MODEL_IDS)-counts[category]} model resources not staged")
    if texture_count<4039:
        missing.append(f"original textures: {4039-texture_count} below verified C78 count")
    return {"expected_resource_models":len(MODEL_IDS),
            "counts":counts,"missing":missing,"invalid":invalid,
            "asset_complete":not missing and not invalid,
            "visual_accuracy_verified":False,
            "original_shader_sampler_roles_verified":False,
            "full_gameplay_verified":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=pathlib.Path,required=True)
    p.add_argument("--report",type=pathlib.Path)
    p.add_argument("--release",action="store_true")
    args=p.parse_args()
    try:
        src=Assets(args.root)
        try: report=audit(src)
        finally:src.close()
    except (ValueError,OSError,zipfile.BadZipFile,KeyError) as exc:
        p.exit(2,"Private asset staging invalid: %s\n"%exc)
    print("Private DS assets: "+json.dumps({"counts":report["counts"],
        "missing_count":len(report["missing"]),"invalid_count":len(report["invalid"])},sort_keys=True))
    if args.report:args.report.write_text(json.dumps(report,indent=2)+"\n")
    if args.release:
        # Presence does not prove authentic visuals: code-level gameplay parity
        # must independently have emulator and hardware validation evidence.
        check=pathlib.Path(__file__).resolve().parent/"check_feature_parity.py"
        complete=subprocess.run([sys.executable,str(check),"--release"],capture_output=True,text=True)
        if report["missing"] or report["invalid"] or complete.returncode!=0:
            p.exit(1,"Release BLOCKED: missing/invalid original assets or unverified gameplay features.\n")
    return 0

if __name__=="__main__":sys.exit(main())
