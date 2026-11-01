#!/usr/bin/env python3
"""Private P3SW v1 sidecars: preserve original C5 material-operation dwords.

Each 13-dword material row comes from C88-validated original C5/C75 source.
P3SW is provenance for future decoder work, NOT a decoded sampler-role map.
Never publish Nintendo material words or generated private ZIP to GitHub.
"""
import argparse
import csv
import json
import re
import struct
import zipfile
import zlib
from collections import defaultdict
from pathlib import Path

from c111_original_sampler_evidence import material_evidence, ROSTER

MEMBER = re.compile(r"decoded_c5/(p\d{3})\.c5$")
HEADER = "<4s4HI"
ROW = "<13I"

def encode_source_words(model_id, original_c5, original_c75):
    evidence, _ = material_evidence(model_id, original_c5, original_c75)
    records = evidence["evidence"]
    if not 1 <= len(records) <= 256:
        raise ValueError("invalid original C5 material word count")
    data = bytearray()
    for i, row in enumerate(records):
        if row["material_index"] != i:
            raise ValueError("C5 material index mismatch")
        values = [int(value, 16) for value in row["source_material_words_hex"]]
        if len(values) != 13:
            raise ValueError("original C5 material must have exactly 13 dwords")
        if values[0] & 65535 != row["shader_index"]:
            raise ValueError("shader references contradict source material words")
        if [values[1] & 65535, values[1] >> 16] != row["source_texture_references"]:
            raise ValueError("original texture refs contradict source material words")
        data += struct.pack(ROW, *values)
    header = struct.pack(HEADER, b"P3SW", 1, int(model_id[1:]),
                         len(records), 0, zlib.crc32(data))
    return header + data

def build(private_root, original_c75_csv, output_zip, require_full=False):
    references = defaultdict(list)
    with Path(original_c75_csv).open(newline="", encoding="utf-8") as fp:
        for row in csv.DictReader(fp):
            mid = row.get("model_id", "")
            if re.fullmatch(r"p\d{3}", mid) is None:
                raise ValueError("invalid source C75 model ID")
            references[mid].append(row)
    for rows in references.values():
        rows.sort(key=lambda item: int(item["index"]))
    seen, outputs = set(), {}
    rows_count = 0
    for part in (1, 2, 3):
        with zipfile.ZipFile(Path(private_root) /
                f"Pokedex3D_C56_Decoded_C5_Part_{part}_of_3.zip") as archive:
            if archive.testzip() is not None:
                raise ValueError("corrupted private original C5 ZIP")
            for name in archive.namelist():
                match = MEMBER.fullmatch(name)
                if match is None:
                    continue
                mid = match.group(1)
                if mid not in ROSTER or mid in seen:
                    raise ValueError("duplicate or unknown source C5 model")
                seen.add(mid)
                payload = encode_source_words(mid, archive.read(name), references[mid])
                outputs[f"materials/{mid}.p3sw"] = payload
                rows_count += struct.unpack_from("<H", payload, 8)[0]
    if not outputs or (set(references) - seen):
        raise ValueError("missing original C5 model or C75 references")
    if require_full and seen != ROSTER:
        raise ValueError("expected all 730 original C5 model archives")
    output_zip = Path(output_zip)
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for name, payload in sorted(outputs.items()):
            output.writestr(name, payload)
    return {"models": len(seen), "original_C5_material_words": rows_count * 13,
            "verified_original_GPU_sampler_roles": 0,
            "P3SW_is_source_evidence_not_decoded_sampler_equations": True}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--texture-reference-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    try:
        result = build(args.private_root, args.texture_reference_csv,
                       args.output, args.require_full)
    except (OSError, ValueError, IndexError, KeyError, UnicodeError,
            struct.error, zipfile.BadZipFile) as exc:
        parser.exit(1, "C113 original C5 material words rejected: " + str(exc) + "\n")
    print(json.dumps(result, indent=2))
if __name__ == "__main__":
    main()
