#!/usr/bin/env python3
"""Audit original-game feature parity; only --release enforces completion."""
import argparse
import json
import pathlib
import sys
VALID={"missing","partial","implemented_baseline","verified_complete"}
def check(path, root):
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version")!=1 or not isinstance(data.get("features"),list):
        raise ValueError("unsupported parity schema")
    ids=set()
    for row in data["features"]:
        identifier=row.get("id")
        if not isinstance(identifier,str) or not identifier or identifier in ids:
            raise ValueError("invalid or duplicate feature ID")
        ids.add(identifier)
        if row.get("status") not in VALID or row.get("required_for_release") is not True:
            raise ValueError("invalid status/mandatory flag for "+identifier)
        source=row.get("source")
        if not isinstance(source,str) or not source.startswith(("source/","Makefile")) or not (root/source).is_file():
            raise ValueError("missing source evidence for "+identifier)
        gap=row.get("gap")
        if not isinstance(gap,str) or not gap:
            raise ValueError("missing gap statement for "+identifier)
        if row["status"]=="verified_complete" and (
            row.get("verified_end_to_end") is not True or
            not row.get("emulator_test") or not row.get("hardware_or_documented_exception")):
            raise ValueError("unsubstantiated completion claim for "+identifier)
    if not ids:
        raise ValueError("empty feature inventory")
    return data
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("manifest",type=pathlib.Path,nargs="?",default=pathlib.Path("docs/C80_FEATURE_PARITY.json"))
    parser.add_argument("--release",action="store_true",help="nonzero unless all required features verified")
    a=parser.parse_args()
    root=pathlib.Path(__file__).resolve().parents[1]
    try:
        data=check(a.manifest,root)
    except (OSError,ValueError,json.JSONDecodeError) as exc:
        parser.exit(2,"Parity inventory invalid: %s\n"%exc)
    total=len(data["features"])
    incomplete=[r for r in data["features"] if r["status"]!="verified_complete"]
    print("Pokédex DS/DSi feature audit: %d tracked, %d require further work"%(total,len(incomplete)))
    for r in incomplete:
        print("  %-38s %-20s %s"%(r["id"],r["status"],r["gap"]))
    if a.release and incomplete:
        parser.exit(1,"Final release gate FAILED: required original features remain incomplete.\n")
if __name__=="__main__":main()
