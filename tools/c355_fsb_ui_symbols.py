#!/usr/bin/env python3
"""C355: recover original FSB script string records with exact offsets and SHA.

Script literals are evidence, NOT runtime navigation/coordinate measurements.
Keep generated original-derived JSON only in the private repository.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import zipfile

MAX_FSB = 256 * 1024
FSB_PREFIX = ("romfs/scripts/", "romfs/scripts_en/")
ANCHOR_RE = re.compile(r"touch|button|btn|icon|rect|hitbox|position", re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse_fsb(data, expected_stem):
    if not 128 <= len(data) <= MAX_FSB:
        raise ValueError("FSB outside original safety limits")
    start, compiled_end, linkage_end, strings_start, file_end, signature, r0, r1 = struct.unpack_from("<8I", data)
    if (start != 32 or signature != 0x4f588000 or r0 or r1 or
            not start < compiled_end < linkage_end == strings_start < file_end == len(data)):
        raise ValueError("FSB header/section boundaries invalid")
    if data[-1] != 0:
        raise ValueError("FSB string pool is not terminated")
    entries = []
    cursor = strings_start
    while cursor < file_end:
        end = data.find(b"\0", cursor)
        if end < 0 or end >= file_end:
            raise ValueError("unterminated FSB string")
        if end - cursor > 1024:
            raise ValueError("unreasonably long FSB string")
        try:
            value = data[cursor:end].decode("utf8")
        except UnicodeDecodeError as exc:
            raise ValueError("invalid original FSB UTF-8") from exc
        if value:
            entries.append({"source_offset": cursor, "utf8": value,
                            "source_sha256": sha(data[cursor:end])})
        cursor = end + 1
    if not 5 <= len(entries) <= 1000 or entries[0]["utf8"].casefold() != expected_stem.casefold():
        raise ValueError("FSB source identity or string count mismatch")
    return {
        "source_bytes": len(data), "source_sha256": sha(data),
        "compiled_section": {"start": start, "end": compiled_end,
                             "sha256": sha(data[start:compiled_end])},
        "opaque_linkage_section": {"start": compiled_end, "end": linkage_end,
                                   "sha256": sha(data[compiled_end:linkage_end])},
        "original_string_section": {"start": strings_start, "end": file_end,
                                     "sha256": sha(data[strings_start:file_end])},
        "strings": entries,
    }


def audit(archive):
    archive = Path(archive)
    if archive.is_symlink() or not archive.is_file():
        raise ValueError("missing/private archive symlink")
    records = {}
    with zipfile.ZipFile(archive) as z:
        members = z.infolist()
        names = [x.filename for x in members]
        if len(names) != len(set(names)):
            raise ValueError("ambiguous duplicate original archive member")
        for item in members:
            p = item.filename
            if (not p or p.startswith("/") or "\\" in p or
                    any(x in ("", ".", "..") for x in p.rstrip("/").split("/")) or
                    stat.S_ISLNK(item.external_attr >> 16)):
                raise ValueError("unsafe original ZIP member")
        scripts = [name for name in names if name.startswith(FSB_PREFIX) and name.endswith(".fsb")]
        if len(scripts) != 50:
            raise ValueError("expected exactly 50 original Japanese/English FSB scripts")
        by_language = {lang: {} for lang in FSB_PREFIX}
        for name in sorted(scripts):
            base = Path(name).stem
            data_size = z.getinfo(name).file_size
            if not 128 <= data_size <= MAX_FSB:
                raise ValueError("original script source size outside bounds")
            raw = z.read(name)
            if len(raw) != data_size:
                raise ValueError("truncated original script source")
            parsed = parse_fsb(raw, base)
            by_language[next(lang for lang in FSB_PREFIX if name.startswith(lang))][base] = name
            records[name] = parsed
        if any(len(v) != 25 for v in by_language.values()) or (
                set(by_language[FSB_PREFIX[0]]) != set(by_language[FSB_PREFIX[1]])):
            raise ValueError("English/Japanese script names do not pair exactly")
    stems = set(by_language[FSB_PREFIX[0]])
    edges = []
    anchors = []
    total_strings = 0
    for name, record in sorted(records.items()):
        total_strings += len(record["strings"])
        language = "en" if name.startswith(FSB_PREFIX[1]) else "jp"
        for entry in record["strings"]:
            token = entry["utf8"]
            if token in stems and token != Path(name).stem:
                edges.append({"source": name, "literal": token,
                              "original_offset": entry["source_offset"],
                              "target_candidate": by_language[FSB_PREFIX[1] if language == "en" else FSB_PREFIX[0]][token],
                              "runtime_control_flow_verified": False})
            if ANCHOR_RE.search(token) and len(token) <= 100:
                anchors.append({"source": name, "original_offset": entry["source_offset"],
                                "literal": token, "touch_coordinates_verified": False})
    return {
        "schema": "c355-original-fsb-ui-symbol-source-catalog-v1",
        "original_archive_sha256": sha(archive.read_bytes()),
        "original_scripts_verified": len(records),
        "original_scripts_per_language": {"en":25,"jp":25},
        "original_source_string_records": total_strings,
        "literal_script_reference_candidates": len(edges),
        "ui_name_or_touch_label_candidates": len(anchors),
        "source_script_refs_are_runtime_control_flow": False,
        "source_text_labels_are_touch_rectangles": False,
        "original_layout_coordinates_decoded": False,
        "authentic_256x192_release_frames_ready": False,
        "original_touchmap_ready": False,
        "release_ready": False,
        "scripts": records, "literal_script_references": edges,
        "ui_name_candidates": anchors,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    a=p.parse_args()
    if a.report.exists() or not a.report.parent.is_dir():
        raise SystemExit("Refusing overwrite or missing private output parent")
    result=audit(a.archive)
    a.report.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf8")
    print(json.dumps({key: result[key] for key in (
        "original_scripts_verified", "original_source_string_records",
        "literal_script_reference_candidates", "ui_name_or_touch_label_candidates",
        "original_layout_coordinates_decoded", "release_ready")}, indent=2))


if __name__ == "__main__":
    main()
