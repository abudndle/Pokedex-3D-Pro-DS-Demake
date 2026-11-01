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
    # A source-art HOME page is NOT compatible with the text-debug row
    # hitboxes. Require a complete privately measured seven-icon touch map.
    def original_home_hotspots(a,p):
        body=a.read(p)
        if len(body)!=86 or body[:4]!=b"P3HM":
            return False
        magic,version,count,reserved,crc=struct.unpack_from("<4sHHII",body)
        if (version!=1 or count!=7 or reserved or
            zlib.crc32(body[16:])!=crc):
            return False
        required={1,3,6,10,8,9,7}
        seen=set()
        rectangles=[]
        for i in range(7):
            page,x0,y0,x1,y1=struct.unpack_from("<5H",body,16+i*10)
            if (page not in required or page in seen or
                not 0<=x0<x1<=256 or not 0<=y0<y1<=192 or
                x1-x0<8 or y1-y0<8):
                return False
            if any(x0<ax1 and ax0<x1 and y0<ay1 and ay0<y1
                   for ax0,ay0,ax1,ay1 in rectangles):
                return False
            seen.add(page)
            rectangles.append((x0,y0,x1,y1))
        return seen==required
    check("ui/home_hotspots.p3hm",original_home_hotspots,
          "missing/inconsistent original 3DS seven-icon HOME touch geometry")
    # The actual original 3DS title is distinct from both HOME bitmaps.
    # A development fallback/menu screenshot never satisfies this requirement.
    for screen in (0,1):
        check(f"ui/title/t{screen}_title.rgb555",
              lambda a,p:a.length(p)==256*192*2,
              "missing/malformed original 3DS title frame")
    # C117: when the user's original title includes a recovered animation,
    # enforce its declared timing, every independent upper/lower source frame,
    # and CRC. The presence of a manifest is NOT proof its timings have been
    # visually matched against the running original 3DS game.
    timeline="ui/title/timeline.p3tl"
    if src.exists(timeline):
        data=src.read(timeline)
        valid=(len(data)>=24 and data[:4]==b"P3TL")
        if valid:
            _,version,count,loop,reserved,crc=struct.unpack_from("<4s4HI",data)
            valid=(version==1 and 2<=count<=16 and loop in (0,1) and
                   reserved==0 and len(data)==16+4*count and
                   zlib.crc32(data[16:])==crc)
        if not valid:
            invalid.append(timeline+": malformed original-source title timeline")
        else:
            for i in range(count):
                index,ticks=struct.unpack_from("<HH",data,16+i*4)
                if index!=i or not 1<=ticks<=3600:
                    invalid.append(timeline+": invalid frame order or source timing")
                    break
            else:
                for i in range(1,count):
                    for screen in (0,1):
                        check(f"ui/title/t{screen}_{i:02d}_title.rgb555",
                              lambda a,p:a.length(p)==256*192*2,
                              "invalid original 3DS title animation frame")
    # C118 source-observed short title sound cues are OPTIONAL, but a
    # declared cue must reference a valid private original PCM16 asset and
    # a real title frame. CRC-valid but impossible timing must block release.
    cues="ui/title/cues.p3tc"
    if src.exists(cues):
        data=src.read(cues)
        valid=(len(data)>=20 and data[:4]==b"P3TC")
        if valid:
            _,version,nframes,nevents,reserved,crc=struct.unpack_from(
                "<4s4HI",data)
            expected_frames=1
            if src.exists(timeline):
                t=src.read(timeline)
                if len(t)>=16 and t[:4]==b"P3TL":
                    expected_frames=struct.unpack_from("<H",t,6)[0]
                else:
                    expected_frames=0
            valid=(version==1 and 1<=nframes<=16 and
                   nframes==expected_frames and 1<=nevents<=nframes and
                   reserved==0 and len(data)==16+nevents*4 and
                   zlib.crc32(data[16:])==crc)
        if not valid:
            invalid.append(cues+": malformed original title audio event map")
        else:
            last=-1
            sound_ids=set()
            for i in range(nevents):
                frame,cue=struct.unpack_from("<HH",data,16+i*4)
                if not last<frame<nframes or not 1<=cue<=16:
                    invalid.append(cues+": invalid source cue order or ID")
                    break
                last=frame
                sound_ids.add(cue)
            else:
                for cue in sound_ids:
                    file=f"ui/title/audio/c{cue:02d}.p3sa"
                    def valid_pcm(a,p):
                        wav=a.read(p)
                        if len(wav)<18:return False
                        magic,version,rate,samples,crc=struct.unpack_from(
                            "<4sHHII",wav)
                        return (magic==b"P3SA" and version==1 and
                                8000<=rate<=32000 and 1<=samples<=16384 and
                                len(wav)==16+samples*2 and
                                zlib.crc32(wav[16:])==crc)
                    check(file,valid_pcm,"invalid original source PCM16 title cue")
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
    def original_source_words(a,p,model_id):
        """P3SW preserves 13 original C5 material dwords; no decoded roles."""
        b=a.read(p)
        if len(b)<16:return False
        magic,version,mid,count,reserved,crc=struct.unpack_from("<4s4HI",b,0)
        if (magic!=b"P3SW" or version!=1 or mid!=model_id or
                reserved!=0 or not 1<=count<=256 or
                len(b)!=16+count*52 or zlib.crc32(b[16:])!=crc):
            return False
        # Keep every raw 32-bit field untouched: no source GPU operation
        # meaning can safely be inferred here. Native cross-checks its known
        # original material/texture/shader reference fields against P3MR/P3SC.
        return True
    def source_c5_crossfile_consistent(a,model_id):
        """Cross-check three separately CRC-valid original C5 sidecars.

        This verifies original material/shader/texture REFERENCES, never
        interprets unknown original GPU sampler or effect operation words.
        """
        base=f"materials/p{model_id:03d}"
        w=a.read(base+".p3sw")
        c=a.read(base+".p3sc")
        r=a.read(base+".p3mr")
        # Individual validators below check header/CRC; the crossfile check
        # also fails safely if called independently with invalid inputs.
        if not (original_source_words(a,base+".p3sw",model_id) and
                source_shader_caps(a,base+".p3sc",model_id) and
                source_material_map(a,base+".p3mr",model_id)):
            return False
        nwords=struct.unpack_from("<H",w,8)[0]
        nshader=struct.unpack_from("<H",c,8)[0]
        nregions=struct.unpack_from("<H",r,10)[0]
        if nwords!=nshader:
            return False
        for i in range(nwords):
            shader=struct.unpack_from("<H",c,16+i*10+2)[0]
            texture0,texture1=struct.unpack_from("<2H",c,16+i*10+4)
            raw_shader=struct.unpack_from("<I",w,16+i*52)[0]
            raw_texture_refs=struct.unpack_from("<I",w,16+i*52+4)[0]
            if ((raw_shader&65535)!=shader or
                (raw_texture_refs&65535)!=texture0 or
                (raw_texture_refs>>16)!=texture1):
                return False
        for i in range(nregions):
            first,count,material,t0,t1,mode=struct.unpack_from(
                "<6H",r,16+12*i)
            if material>=nwords:
                return False
            texture0,texture1=struct.unpack_from("<2H",c,16+material*10+4)
            if (texture0,texture1)!=(t0,t1):
                return False
        return True
    categories={
        "mesh_previews":"preview/p%03d.ds3m",
        "verified_uv":"preview/p%03d.p3uv",
        "verified_material_bindings":"materials/p%03d.p3mt",
        "original_texture_manifests":"materials/p%03d.p3tx",
        "original_texture_catalogs":"catalogs/p%03d.p3tm",
        "source_C5_material_provenance":"materials/p%03d.p3mr",
        "source_C5_shader_capabilities":"materials/p%03d.p3sc",
        "source_C5_operation_words":"materials/p%03d.p3sw"
    }
    counts={}
    for category,pattern in categories.items():
        count=0
        for ident in MODEL_IDS:
            path=pattern%ident
            if src.exists(path):
                count+=1
                if category=="source_C5_operation_words":
                    if not original_source_words(src,path,ident):
                        invalid.append(path+": invalid original C5 material operation words or CRC")
                elif category=="source_C5_shader_capabilities":
                    if not source_shader_caps(src,path,ident):
                        invalid.append(path+": invalid C5 shader capability declarations or CRC")
                elif category=="source_C5_material_provenance":
                    if not source_material_map(src,path,ident):
                        invalid.append(path+": invalid C5 material provenance, counts or CRC")
                elif src.length(path)==0:
                    invalid.append(path+": empty")
        counts[category]=count
    # Three matching CRCs are NOT sufficient: inconsistent original model
    # material/sampler references must also block an asset-bearing release.
    # Missing sidecars are already reported by the individual categories.
    for ident in MODEL_IDS:
        paths=tuple(f"materials/p{ident:03d}{ext}"
                    for ext in (".p3sw",".p3sc",".p3mr"))
        if all(src.exists(path) for path in paths):
            if not source_c5_crossfile_consistent(src,ident):
                invalid.append(
                    f"materials/p{ident:03d}: original C5 P3SW/P3SC/P3MR references disagree")
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
            "original_title_screen_visually_verified":False,
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
