#!/usr/bin/env python3
"""C140: recover original C5 shader *declarations*, never guess material binding.

Runs locally on privately held decoded C56 archives and original validation ZIP.
Emits one private JSON inventory with source hashes and real shader capability
strings, not P3SC/P3SW/P3MR/P3MT; shader-to-mesh and sampler mapping is unknown.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
import re
import struct
import zipfile
from pathlib import Path

ROSTER = frozenset(range(734)) - {721, 722, 723, 724}
PART_RANGES = ((0, 249), (250, 499), (500, 733))
C5_FILE = re.compile(r"decoded_c5/p(\d{3})\.c5\Z")
FLAG = re.compile(r"CF_[A-Z][A-Z0-9_]*\Z")
MAX_C5 = 16 * 1024 * 1024
MAX_STRINGS = 64
MAX_RECORD_BYTES = 256
MAX_TABLE_BYTES = 16384
MAX_REFERENCE_BYTES = 1024 * 1024


def parse_declarations(data):
    """Read only the C5-header-addressed leading shader string records.

    This does not presume the neighboring material record layout, shader
    index mapping, or Nintendo 3DS GPU slot semantics.
    """
    if len(data) < 0x78 or data[:2] != b"\xc5\x78":
        raise ValueError("not a recovered C5 container")
    offset = struct.unpack_from("<I", data, 0x64)[0]
    if offset < 0x78 or offset >= len(data):
        raise ValueError("invalid source C5 shader string-table offset")
    end = min(len(data), offset + MAX_TABLE_BYTES)
    records = []
    cursor = offset
    for _ in range(MAX_STRINGS):
        nul = data.find(b"\0", cursor, min(end, cursor + MAX_RECORD_BYTES + 1))
        if nul < 0:
            raise ValueError("nonterminated/oversize C5 shader string")
        raw = data[cursor:nul]
        if b";;;CF_" not in raw:
            break
        try:
            decoded = raw.decode("ascii")
        except UnicodeDecodeError as error:
            raise ValueError("non-ASCII C5 shader declaration") from error
        if decoded.count(";;;") != 1:
            raise ValueError("malformed C5 shader delimiter")
        shader, flags = decoded.split(";;;")
        if not shader or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", shader):
            raise ValueError("invalid C5 shader program name")
        tokens = flags.split(",")
        if not tokens or any(not FLAG.fullmatch(x) for x in tokens):
            raise ValueError("invalid C5 shader capabilities")
        if len(tokens) != len(set(tokens)):
            raise ValueError("duplicate original C5 shader flag")
        records.append({"source_offset": cursor, "program": shader,
                        "flags": tokens, "source_sha256": hashlib.sha256(raw).hexdigest()})
        cursor = nul + 1
    if not records:
        raise ValueError("source C5 model has no original shader declarations")
    if cursor >= end:
        raise ValueError("shader declaration scan exceeded safety limit")
    return records


def reference_rows(bundle):
    with zipfile.ZipFile(bundle) as z:
        names = z.namelist()
        if names.count("C56_validation.csv") != 1 or len(names) != len(set(names)):
            raise ValueError("missing/ambiguous C56 source-validation file")
        with z.open("C56_validation.csv") as stream:
            payload = stream.read(MAX_REFERENCE_BYTES + 1)
        if len(payload) > MAX_REFERENCE_BYTES:
            raise ValueError("oversized original C56 validation catalog")
    rows = {}
    for row in csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))):
        label = row.get("model", "")
        if not re.fullmatch(r"p\d{3}", label) or label in rows:
            raise ValueError("duplicate/invalid source C56 model row")
        if not re.fullmatch(r"[a-f0-9]{64}", row.get("sha256", "")):
            raise ValueError("invalid C56 original source digest")
        rows[label] = row
    if {int(label[1:]) for label in rows} != ROSTER:
        raise ValueError("original C56 catalog is missing model rows")
    return rows


def audit(parts, decoder_bundle):
    if len(parts) != 3:
        raise ValueError("expected exactly three ordered C56 archive parts")
    references = reference_rows(decoder_bundle)
    models = {}
    flag_counts = collections.Counter()
    declaration_types = collections.Counter()
    program_counts = collections.Counter()
    for part_index, path in enumerate(parts):
        first, last = PART_RANGES[part_index]
        with zipfile.ZipFile(path) as z:
            entries = z.infolist()
            if len(entries) != len({entry.filename for entry in entries}):
                raise ValueError("duplicate C56 source archive member")
            for member in entries:
                m = C5_FILE.fullmatch(member.filename)
                if not m:
                    raise ValueError("unknown/unsafe private C56 source member")
                model = int(m.group(1))
                label = f"p{model:03d}"
                if model not in ROSTER or not first <= model <= last or label in models:
                    raise ValueError("duplicate/out-of-part recovered C5 model")
                if not 0 < member.file_size <= MAX_C5:
                    raise ValueError("recovered C5 data exceeds source file budget")
                decoded = z.read(member)
                ref = references[label]
                digest = hashlib.sha256(decoded).hexdigest()
                if digest != ref["sha256"] or len(decoded) != int(ref["decoded_bytes"]):
                    raise ValueError(f"private C56 source hash/size mismatch: {label}")
                declarations = parse_declarations(decoded)
                for record in declarations:
                    flag_counts.update(record["flags"])
                    program_counts[record["program"]] += 1
                    declaration_types[",".join(sorted(record["flags"]))] += 1
                models[label] = {"source_c5_sha256": digest,
                                 "shader_declarations": declarations,
                                 "source_material_to_shader_map_verified": False,
                                 "source_sampler_roles_verified": False,
                                 "native_texture_binding_ready": False}
    if set(models) != set(references):
        raise ValueError("private C56 archives do not cover all original models")
    return {
        "models_verified": len(models),
        "shader_declarations_recovered":
            sum(len(x["shader_declarations"]) for x in models.values()),
        "flag_occurrences": dict(sorted(flag_counts.items())),
        "program_occurrences": dict(sorted(program_counts.items())),
        "distinct_flag_sets": len(declaration_types),
        "flag_set_occurrences": dict(sorted(declaration_types.items())),
        "verified_source_material_to_shader_bindings": 0,
        "verified_original_sampler_roles": 0,
        "certified_original_textured_models": 0,
        "scope": "Verified original C5 shader declaration strings only; NOT source material assignments, P3SC or texture/sampler mapping.",
        "models": {k: models[k] for k in sorted(models)},
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--parts", nargs=3, required=True, type=Path)
    p.add_argument("--decoder-bundle", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path,
                   help="private JSON report; NEVER commit original game-derived declarations")
    args = p.parse_args()
    result = audit(args.parts, args.decoder_bundle)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "models" and k != "flag_set_occurrences"}, indent=2))


if __name__ == "__main__":
    main()