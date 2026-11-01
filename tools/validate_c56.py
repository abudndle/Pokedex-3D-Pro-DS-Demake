#!/usr/bin/env python3
"""C56 private Z5->C5 validation; unusual 0x26 descriptors are warnings."""
import argparse
import csv
import hashlib
from pathlib import Path

from native_z5_decoder import decode_stream
from c5_dual_table_parser import parse


def assess(data: bytes):
    info = parse(data)
    tolerated = []
    for issue in info["issues"]:
        if not issue.startswith("first descriptor ") or "reserved fields nonzero" not in issue:
            continue
        index = int(issue.split()[2])
        descriptor = info["first_table"][index]
        if (int(descriptor["reserved0"], 16) == 0 and
                int(descriptor["reserved1"], 16) == 0x26):
            tolerated.append(issue)
    serious = [issue for issue in info["issues"] if issue not in tolerated]
    status = ("strict_valid" if not info["issues"] else
              "valid_with_0x26_flag_warning" if not serious else "invalid")
    return status, len(tolerated), serious, info


def validate_source(source: Path, destination: Path):
    if destination.exists():
        data = destination.read_bytes()
    else:
        raw = source.read_bytes()
        if len(raw) < 33:
            raise ValueError("truncated Z5 header")
        data = decode_stream(raw[32:], max_output=16 * 1024 * 1024)
    status, flags, errors, info = assess(data)
    if errors:
        raise ValueError("; ".join(errors[:4]))
    if not destination.exists():
        temporary = destination.with_suffix(".c5.partial")
        temporary.write_bytes(data)
        temporary.replace(destination)
    return [source.stem, status, len(data), flags,
            len(info["first_table"]), hashlib.sha256(data).hexdigest(), ""]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--decoded", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    args.decoded.mkdir(parents=True, exist_ok=True)
    rows = []
    for source in sorted(args.source.glob("p*.z5")):
        destination = args.decoded / (source.stem + ".c5")
        try:
            rows.append(validate_source(source, destination))
        except (OSError, ValueError) as error:
            rows.append([source.stem, "error", 0, 0, 0, "", str(error)])
    with args.report.open("w", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(["model", "status", "decoded_bytes", "0x26_descriptor_flags",
                         "primary_descriptor_count", "sha256", "error"])
        writer.writerows(rows)
    print(f"Validated {len(rows)} private source records; "
          f"errors: {sum(row[1] == 'error' for row in rows)}")
    if not rows or any(row[1] == "error" for row in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
