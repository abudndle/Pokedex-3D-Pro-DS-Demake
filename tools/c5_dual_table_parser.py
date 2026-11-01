#!/usr/bin/env python3
"""C56 structural parser of recovered C5 container's two descriptor tables.

This validates bounds and descriptor relationships only. It does not prove
vertex attributes, face topology, UVs, shader semantics or material mapping.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def _u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def parse(data: bytes):
    if len(data) < 0x78 or data[:2] != b"\xc5\x78":
        raise ValueError("not a C5 78 container")
    head = {
        "first_table_count_header_lo": struct.unpack_from("<H", data, 0x14)[0],
        "second_table_count_header_hi": struct.unpack_from("<H", data, 0x16)[0],
        "track_count_header_hi": struct.unpack_from("<H", data, 0x1a)[0],
        "first_table_offset": _u32(data, 0x3c),
        "second_table_offset": _u32(data, 0x40),
        "next_section_offset": _u32(data, 0x44),
        "track_table_offset": _u32(data, 0x48),
        "track_table_end": _u32(data, 0x4c),
        "string_table_offset": _u32(data, 0x64),
        "numeric_section_offset": _u32(data, 0x68),
    }
    for key in ("first_table_offset", "second_table_offset",
                "next_section_offset", "track_table_offset", "track_table_end"):
        if not 0 <= head[key] < len(data):
            raise ValueError(f"invalid {key}")
    issues = []
    def check(ok, message):
        if not ok:
            issues.append(message)
    a, b, c = (head[k] for k in ("first_table_offset", "second_table_offset", "next_section_offset"))
    n1 = head["first_table_count_header_lo"]
    n2 = head["second_table_count_header_hi"]
    check(b - a == n1 * 20, "first table boundary mismatch")
    check(c - b == n2 * 12, "second table boundary mismatch")
    check(head["track_table_end"] - head["track_table_offset"] ==
          head["track_count_header_hi"] * 16, "track table count/size mismatch")
    first, second = [], []
    for i in range(n1):
        pos = a + 20 * i
        if pos + 20 > len(data):
            raise ValueError("first table truncated")
        offset, reserved0, packed, layout, reserved1 = struct.unpack_from("<5I", data, pos)
        count = packed & 0xffff
        fmt = packed >> 16
        stride = fmt & 0xff
        length = count * stride
        row = {
            "descriptor_offset": hex(pos), "data_offset": hex(offset),
            "reserved0": hex(reserved0), "packed_count_stride": hex(packed),
            "record_count": count, "upper16": hex(fmt),
            "low_byte_of_upper16": stride, "layout_word": hex(layout),
            "reserved1": hex(reserved1), "inferred_payload_bytes": length,
            "inferred_end_offset": hex(offset + length),
            "in_file": offset + length <= len(data),
        }
        first.append(row)
        check(row["in_file"], f"first payload {i} out of bounds")
        check(reserved0 == 0 and reserved1 == 0, f"first descriptor {i} reserved fields nonzero")
    for i in range(n2):
        pos = b + 12 * i
        if pos + 12 > len(data):
            raise ValueError("second table truncated")
        offset, reserved, packed = struct.unpack_from("<3I", data, pos)
        count, factor = packed & 0xffff, packed >> 16
        length = count * factor
        row = {
            "descriptor_offset": hex(pos), "data_offset": hex(offset),
            "reserved": hex(reserved), "packed_word": hex(packed),
            "low16": count, "high16": factor,
            "candidate_payload_bytes": length,
            "candidate_end_offset": hex(offset + length),
            "in_file": offset + length <= len(data),
        }
        second.append(row)
        check(row["in_file"], f"second payload {i} out of bounds")
        check(reserved == 0, f"second descriptor {i} reserved field nonzero")
    for i in range(len(first) - 1):
        check(int(first[i]["inferred_end_offset"], 16) ==
              int(first[i + 1]["data_offset"], 16), f"first payload {i} not contiguous")
    if first and second:
        check(int(first[-1]["inferred_end_offset"], 16) ==
              int(second[0]["data_offset"], 16), "first/second payload boundary mismatch")
    for i in range(len(second) - 1):
        end = int(second[i]["candidate_end_offset"], 16)
        nxt = int(second[i + 1]["data_offset"], 16)
        check(nxt == (end + 3) // 4 * 4, f"second payload {i} alignment mismatch")
    checks = []
    for i in range(min(len(first), len(second))):
        row = second[i]
        length = row["candidate_payload_bytes"]
        offset = int(row["data_offset"], 16)
        if row["high16"] == 2 and length >= 2 and length % 2 == 0 and offset + length <= len(data):
            values = struct.unpack_from(f"<{length // 2}H", data, offset)
            limit = first[i]["record_count"]
            valid = sum(value < limit for value in values)
            checks.append({
                "paired_record": i, "second_buffer_u16_count": len(values),
                "first_buffer_record_count": limit,
                "u16_values_less_than_first_record_count": valid,
                "fraction_in_range": round(valid / len(values), 6),
                "direct_triangle_index_interpretation_valid": valid == len(values),
            })
    return {
        "file_size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "header": head, "first_table": first, "second_table": second,
        "direct_index_hypothesis_checks": checks,
        "structural_checks_passed": not issues, "issues": issues,
        "interpretation_limit": "Descriptor bounds only; vertex attributes and polygon topology NOT decoded.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("-o", "--out", type=Path)
    args = parser.parse_args()
    results = {path.stem: parse(path.read_bytes()) for path in args.inputs}
    output = json.dumps(results, indent=2) + "\n"
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output)
