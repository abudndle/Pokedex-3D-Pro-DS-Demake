#!/usr/bin/env python3
"""Private C5 structural inventory. No vertex or topology semantics are inferred.

Run only against authorized local archives; the SHA-bearing report is private.
"""
import argparse
import hashlib
import json
import os
import re
import struct
import tempfile
import zipfile
from pathlib import Path

EXPECTED = set(range(734)) - {721, 722, 723, 724}
MODEL_PATH = re.compile(r"decoded_c5/p([0-9]{3})\.c5\Z")
MAX_C5_BYTES = 64 * 1024 * 1024  # Bound decompression of each untrusted ZIP member.
MAX_TOTAL_C5_BYTES = 1024 * 1024 * 1024  # Bound the complete 730-model audit.
MAX_ZIP_ENTRIES = 2048  # Reject archive metadata floods before inspecting entries.
MAX_ARCHIVES = 16


def inspect(data):
    if len(data) < 0x78 or data[:2] != b"\xc5\x78":
        raise ValueError("bad C5 header")
    u16 = lambda p: struct.unpack_from("<H", data, p)[0]
    u32 = lambda p: struct.unpack_from("<I", data, p)[0]
    a, b, c = [u32(p) for p in (0x3c, 0x40, 0x44)]
    n1, n2 = u16(0x14), u16(0x16)
    if not (0x78 <= a <= b <= c <= len(data)) or b - a != n1 * 20 or c - b != n2 * 12:
        raise ValueError("invalid descriptor table bounds")
    strides = {}
    errors = []
    flags_0x26 = 0
    for i in range(n1):
        off, res, packed, layout, res2 = struct.unpack_from("<5I", data, a + i * 20)
        count, stride = packed & 65535, (packed >> 16) & 255
        strides[str(stride)] = strides.get(str(stride), 0) + 1
        # Original C56 source files legitimately use the exact 0x26 marker
        # in this reserved word. The owner-supplied C56 validator treats it
        # as a warning, not corruption; every other value still fails closed.
        if res == 0 and res2 == 0x26:
            flags_0x26 += 1
        if res or res2 not in (0, 0x26) or off + count * stride > len(data):
            errors.append("primary descriptor " + str(i))
    for i in range(n2):
        off, res, packed = struct.unpack_from("<3I", data, b + i * 12)
        if res or off + (packed & 65535) * (packed >> 16) > len(data):
            errors.append("secondary descriptor " + str(i))
    return dict(sha256=hashlib.sha256(data).hexdigest(), primary=n1, secondary=n2,
                primary_strides=strides, primary_descriptor_0x26_flags=flags_0x26,
                structural_errors=errors,
                vertex_semantics_verified=False, topology_verified=False)


def audit(archives):
    archives = list(archives)
    if len(archives) > MAX_ARCHIVES:
        raise ValueError("too many C5 archives")
    records = {}
    total_bytes = 0
    for path in archives:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ZIP_ENTRIES:
                raise ValueError("C5 ZIP entry budget exceeded")
            for info in infos:
                name = info.filename
                if not (name.startswith("decoded_c5/") and name.endswith(".c5")):
                    continue
                match = MODEL_PATH.fullmatch(name)
                if match is None:
                    raise ValueError("noncanonical C5 member name")
                model = int(match.group(1))
                if model not in EXPECTED or model in records:
                    raise ValueError("duplicate or out-of-roster model " + str(model))
                # Reserve the model before reading, so malformed members never vanish.
                records[model] = {"error": "unreadable C5 member"}
                if info.is_dir() or info.file_size > MAX_C5_BYTES:
                    records[model] = {"error": "invalid or oversized C5 member"}
                    continue
                if total_bytes + info.file_size > MAX_TOTAL_C5_BYTES:
                    raise ValueError("aggregate C5 uncompressed byte budget exceeded")
                total_bytes += info.file_size
                try:
                    with archive.open(info) as member:
                        data = member.read(MAX_C5_BYTES + 1)
                    if len(data) != info.file_size or len(data) > MAX_C5_BYTES:
                        raise ValueError("C5 member size mismatch")
                    records[model] = inspect(data)
                except (ValueError, EOFError, RuntimeError, OSError, zipfile.BadZipFile) as exc:
                    records[model] = {"error": type(exc).__name__}
    missing = sorted(EXPECTED - records.keys())
    failed = sorted(model for model, row in records.items()
                    if row.get("error") or row.get("structural_errors"))
    warning_models = sorted(model for model, row in records.items()
                            if row.get("primary_descriptor_0x26_flags", 0))
    return dict(expected=len(EXPECTED), present=len(records), missing=missing,
                structural_failures=failed, all_structural_checks_passed=not missing and not failed,
                descriptor_0x26_warning_models=warning_models,
                vertex_semantics_verified=False, topology_verified=False,
                models={f"p{k:03d}": records[k] for k in sorted(records)})


def write_private_report(path, result):
    """Atomically write a private 0600 report without following destination links.

    Replacing an existing hard link rather than truncating its inode prevents
    accidental mutation of a tracked public file through a private path.
    """
    repo_root = Path(__file__).resolve().parents[1]
    requested = path.expanduser().absolute()
    parent = requested.parent.resolve()
    target = parent / requested.name
    if parent == repo_root or repo_root in parent.parents:
        raise ValueError("private SHA report must be outside the public repository")
    if target.is_symlink():
        raise ValueError("refusing symlink private report destination")
    parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        fd, name = tempfile.mkstemp(prefix=".c180-report-", suffix=".tmp", dir=parent)
        temporary = Path(name)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(result, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archives", nargs="+", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.archives)
    write_private_report(args.report, result)
    print("C180", result["present"], "/", result["expected"],
          "structural failures", len(result["structural_failures"]))
    if not result["all_structural_checks_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
