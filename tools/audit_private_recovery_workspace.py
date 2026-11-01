#!/usr/bin/env python3
"""Audit private C18–C98 archive inputs without extracting or publishing them."""
import argparse
import json
import pathlib
import zipfile

REQUIRED = {
 "recovery": (
  "Pokedex3D_C18_Forms_Models_Provisional_Color_Source.zip",
  "Pokedex3D_C56_Decoded_C5_Part_1_of_3.zip",
  "Pokedex3D_C56_Decoded_C5_Part_2_of_3.zip",
  "Pokedex3D_C56_Decoded_C5_Part_3_of_3.zip",
  "Pokedex3D_C56_Decoder_Tools_and_Validation.zip",
  "Pokedex3D_C62_528_UV_Model_Exports.zip",
  "Pokedex3D_C63_Partial_UV_Recovery_162_Models.zip",
  "Pokedex3D_C7_Validated_Geometry_OBJ_Collection.zip",
 ),
 "packages": (
  "C84_PRIVATE_ORIGINAL_GUI_MOVES_TEXTURE_DEX_NITROFS.zip",
  "C86_PRIVATE_DS_GEOMETRY_AND_UV_CANDIDATES.zip",
  "C86_PRIVATE_COMBINED_NITROFS_WITH_PREVIEWS.zip",
  "C98_PRIVATE_LEGACY_VS_CHUNKED_NITROFS.zip",
  "C98_PRIVATE_TOOLS_AND_AUDITS.zip",
 ),
}

def audit(root):
    results=[]
    for folder, names in REQUIRED.items():
        for name in names:
            path=root/folder/name
            row={"group":folder,"archive":name,"status":"missing"}
            if path.is_file():
                try:
                    with zipfile.ZipFile(path) as archive:
                        members=archive.namelist()
                        if len(members)!=len(set(members)):
                            raise ValueError("duplicate ZIP member names")
                        if any(m.startswith("/") or "\\" in m or ".." in pathlib.PurePosixPath(m).parts for m in members):
                            raise ValueError("unsafe ZIP member path")
                        corrupted=archive.testzip()
                        if corrupted: raise ValueError("corrupt ZIP member")
                        row.update(status="valid",entries=len(members),bytes=path.stat().st_size)
                except (OSError,ValueError,zipfile.BadZipFile) as exc:
                    row.update(status="invalid",reason=str(exc))
            results.append(row)
    return {"complete":all(r["status"]=="valid" for r in results),
            "archives":results,
            "missing":[r["archive"] for r in results if r["status"]=="missing"],
            "invalid":[r["archive"] for r in results if r["status"]=="invalid"]}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=pathlib.Path,default=pathlib.Path("private"))
    parser.add_argument("--strict",action="store_true",help="exit nonzero if any source archive is missing or invalid")
    args=parser.parse_args()
    result=audit(args.root)
    print(json.dumps(result,indent=2))
    if args.strict and not result["complete"]:raise SystemExit(1)
if __name__=="__main__":main()
