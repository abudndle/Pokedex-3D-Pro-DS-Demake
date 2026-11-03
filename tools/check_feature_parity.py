#!/usr/bin/env python3
"""Audit original-game feature parity; only --release enforces completion."""
import argparse
import json
import pathlib
import sys
import re
VALID={"missing","partial","implemented_baseline","verified_complete"}
REQUIRED_FEATURE_IDS=['animations','challenges','cries_music_speech','dsi_camera_ar','dual_screen_menus','favorites','move_dex','nds_melonds_hardware_validation','original_localizations','original_pokemon_models','original_text_search_filters','original_texture_materials','photo_album','pokedex_entries_forms','pokemon_stats_evolutions_learnsets','progress_saves','records','settings_custom_art','touch_and_buttons','type_chart']
SHA256 = re.compile(r"^[0-9a-f]{64}$")

def has_release_evidence(row):
    """Release evidence must be concrete, not a boolean or placeholder label.

    Public CI URLs may prove source tests, but private original-game assets and
    hardware captures must stay outside this repository. Only evidence metadata
    and independently reviewable references belong in this manifest.
    """
    evidence = row.get("release_evidence")
    if not isinstance(evidence, list) or len(evidence) < 3:
        return False
    kinds = set()
    for item in evidence:
        if not isinstance(item, dict):
            return False
        kind, reference, digest = (item.get("kind"), item.get("reference"),
                                   item.get("sha256"))
        if kind not in ("original_source", "emulator", "hardware") or kind in kinds:
            return False
        if not isinstance(reference, str) or len(reference.strip()) < 12:
            return False
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            return False
        kinds.add(kind)
    return kinds == {"original_source", "emulator", "hardware"}

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
        if not isinstance(source,str) or not source.startswith(("source/","tools/","Makefile")) or not (root/source).is_file():
            raise ValueError("missing source evidence for "+identifier)
        gap=row.get("gap")
        if not isinstance(gap,str) or not gap:
            raise ValueError("missing gap statement for "+identifier)
        if row["status"]=="verified_complete" and (
            row.get("verified_end_to_end") is not True or
            not row.get("emulator_test") or not row.get("hardware_or_documented_exception") or
            not has_release_evidence(row)):
            raise ValueError("unsubstantiated completion claim for "+identifier)
    if ids != set(REQUIRED_FEATURE_IDS):
        raise ValueError("mandatory features missing or unexpected: %s"%sorted(ids.symmetric_difference(REQUIRED_FEATURE_IDS)))
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
