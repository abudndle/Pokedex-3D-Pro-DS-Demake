#!/usr/bin/env python3
"""C286: cross-check C279 source format words against C285 C84 candidates.

This narrows conversion-consistent candidates only. Original GPU format IDs,
texture-unit/sampler roles and source-to-native material bindings remain unproven.
Original model names, hashes, source files and reports stay private.
"""
import argparse
import collections
import json
import os
import re
import stat
from pathlib import Path

SOURCE_SCHEMA = "C279_PRIVATE_C5_HEADER_TEXTURE_BASE_V1"
CANDIDATE_SCHEMA = "C285_PRIVATE_ETC1_5BIT_EXPANSION_CANDIDATES_V1"
SCHEMA = "C286_PRIVATE_C5_FORMAT_WORD_CONSENSUS_V1"
MAX_REPORT = 32 * 1024 * 1024
MODEL = re.compile(r"p\d{3}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
CANDIDATE = re.compile(r"[A-Z0-9_]{1,64}\Z")
ROSTER = {f"p{i:03d}" for i in range(734) if i not in (721, 722, 723, 724)}
STATUSES = {0: "no_supported_candidate_not_verified",
            1: "unique_candidate_consistent_with_C84"}


def _model(mid):
    if type(mid) is not str or not MODEL.fullmatch(mid) or mid not in ROSTER:
        raise ValueError("invalid original model ID")
    return mid


def _candidate_for_bits(name, bits):
    if type(name) is not str or not CANDIDATE.fullmatch(name):
        return False
    if bits == 8:
        return name in ("L8", "A8", "LA44_L_LOW", "LA44_L_HIGH") or name.startswith("ETC1A4_")
    return name in ("L4_LOW_FIRST", "L4_HIGH_FIRST", "A4_LOW_FIRST", "A4_HIGH_FIRST") or name.startswith("ETC1_")


def reconcile(c279, c285, require_full=False):
    """Fail closed on cross-report identity/metadata errors; do not assert GPU proof."""
    if (not isinstance(c279, dict) or not isinstance(c285, dict) or
            not isinstance(c279.get("summary"), dict) or
            not isinstance(c285.get("summary"), dict) or
            c279["summary"].get("schema") != SOURCE_SCHEMA or
            c285["summary"].get("schema") != CANDIDATE_SCHEMA):
        raise ValueError("wrong source or candidate report schema")
    source_models, candidates = c279.get("models"), c285.get("textures")
    if (not isinstance(source_models, list) or not 1 <= len(source_models) <= 730 or
            not isinstance(candidates, list) or len(candidates) > 4096):
        raise ValueError("report model/texture count outside bounds")
    source = {}
    models = set()
    for model in source_models:
        if not isinstance(model, dict):
            raise ValueError("malformed C279 model")
        mid = _model(model.get("model_id"))
        if mid in models:
            raise ValueError("duplicate C279 model")
        models.add(mid)
        rows = model.get("records")
        if not isinstance(rows, list) or not 1 <= len(rows) <= 256:
            raise ValueError("invalid source descriptor roster")
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or type(row.get("index")) is not int or row["index"] != index:
                raise ValueError("duplicate/missing source descriptor index")
            fmt = row.get("opaque_format")
            digest = row.get("source_sha256")
            if (type(fmt) is not int or not 0 <= fmt <= 0xffffffff or
                    type(digest) is not str or not SHA.fullmatch(digest) or
                    type(row.get("c73_sha_anchor")) is not bool or
                    type(row.get("p3tm_metadata_corrob")) is not bool or
                    row.get("byte_density") not in ("4_BPP_STORAGE_ONLY", "8_BPP_STORAGE_ONLY",
                                                    "16_BPP_STORAGE_ONLY", "24_BPP_STORAGE_ONLY",
                                                    "32_BPP_STORAGE_ONLY", "UNKNOWN_OR_PADDED",
                                                    "NONINTEGRAL_OR_PADDED")):
                raise ValueError("malformed C279 source provenance")
            source[(mid, index)] = row
    if require_full and models != ROSTER:
        raise ValueError("expected full 730-model original source roster")
    if type(c285["summary"].get("models")) is not int or c285["summary"]["models"] != len(models):
        raise ValueError("C285/C279 model count mismatch")
    grouped = collections.defaultdict(list)
    seen = set()
    for record in candidates:
        if not isinstance(record, dict):
            raise ValueError("malformed C285 texture")
        mid = _model(record.get("model_id"))
        idx = record.get("texture_index")
        bits = record.get("storage_bits_per_pixel")
        if type(idx) is not int or type(bits) is not int or bits not in (4, 8):
            raise ValueError("invalid C285 texture index or density")
        key = (mid, idx)
        if key in seen or key not in source:
            raise ValueError("duplicate or missing C279 texture")
        seen.add(key)
        original = source[key]
        if (not original["c73_sha_anchor"] or not original["p3tm_metadata_corrob"] or
                original["byte_density"] != f"{bits}_BPP_STORAGE_ONLY"):
            raise ValueError("C285 source SHA/metadata/density not independently anchored")
        names = record.get("candidates")
        if (not isinstance(names, (tuple, list)) or len(names) > 16 or
                any(type(n) is not str for n in names) or len(set(names)) != len(names) or
                any(not _candidate_for_bits(n, bits) for n in names)):
            raise ValueError("invalid or duplicate C285 hypotheses")
        expected = STATUSES.get(len(names), "ambiguous_candidates_not_verified")
        if record.get("status") != expected:
            raise ValueError("C285 status contradicts candidate count")
        grouped[(original["opaque_format"], bits)].append({
            "model_id": mid, "texture_index": idx,
            "source_sha256": original["source_sha256"],
            "candidates": list(names), "initial_status": expected,
        })
    if not candidates:
        raise ValueError("no source-anchored low-bpp candidates")
    results = []
    summary = collections.Counter()
    for (fmt, bits), entries in sorted(grouped.items()):
        unique = {r["candidates"][0] for r in entries if len(r["candidates"]) == 1}
        conflict = len(unique) > 1 or (len(unique) == 1 and any(
            r["candidates"] and next(iter(unique)) not in r["candidates"] for r in entries))
        selected = next(iter(unique)) if len(unique) == 1 and not conflict else None
        if conflict:
            summary["conflicting_source_format_words"] += 1
        if selected:
            summary["source_format_words_with_unique_C84_anchor"] += 1
        for row in entries:
            count = len(row["candidates"])
            if count == 0:
                summary["unmatched_candidates"] += 1
                disposition = "UNMATCHED_NO_SOURCE_FORMAT_PROOF"
            elif count == 1:
                summary["initially_unique_C84_candidates"] += 1
                disposition = ("CONFLICTING_SOURCE_FORMAT_WORD" if conflict else
                               "UNIQUE_C84_CONVERSION_CANDIDATE")
            elif selected and selected in row["candidates"]:
                summary["ambiguous_narrowed_by_repeated_source_word"] += 1
                disposition = "NARROWED_C84_HYPOTHESIS_NOT_GPU_PROOF"
            else:
                summary["remaining_ambiguous_C84_candidates"] += 1
                disposition = ("CONFLICTING_SOURCE_FORMAT_WORD" if conflict else
                               "AMBIGUOUS_C84_CONVERSION_CANDIDATES")
            results.append({**row, "opaque_source_format": fmt, "storage_bits_per_pixel": bits,
                            "format_word_consensus_candidate": selected if not conflict and count else None,
                            "disposition": disposition,
                            "gpu_format_verified": False, "sampler_role_verified": False,
                            "native_p3px_binding_verified": False})
    summary["source_models_checked"] = len(models)
    summary["low_bpp_textures_checked"] = len(results)
    summary["source_format_word_groups"] = len(grouped)
    return {"summary": {"schema": SCHEMA, **dict(sorted(summary.items())),
                        "independent_gpu_format_verified": False,
                        "native_material_sampler_binding_verified": False,
                        "asset_integrated_emulator_verified": False, "release_ready": False},
            "textures": sorted(results, key=lambda r: (r["model_id"], r["texture_index"]))}


def _read_private_json(path):
    path = Path(path)
    if path.parent.is_symlink():
        raise ValueError("private input parent symlink rejected")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= MAX_REPORT:
            raise ValueError("private input must be bounded regular single-link file")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            payload = stream.read(MAX_REPORT + 1)
        if len(payload) != info.st_size:
            raise ValueError("private report length changed while reading")
        return json.loads(payload)
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--c279-private-json", type=Path, required=True)
    parser.add_argument("--c285-private-json", type=Path, required=True)
    parser.add_argument("--output-private-json", type=Path, required=True)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    from c275_private_draw_material_chain import write_private_report
    try:
        if args.output_private_json.resolve() in (args.c279_private_json.resolve(),
                                                  args.c285_private_json.resolve()):
            raise ValueError("private output must differ from both source reports")
        report = reconcile(_read_private_json(args.c279_private_json),
                           _read_private_json(args.c285_private_json), args.require_full)
        write_private_report(args.output_private_json, report)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(1, "C286 private source format consensus rejected: " + str(exc) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
