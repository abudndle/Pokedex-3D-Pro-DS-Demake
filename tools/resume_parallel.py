#!/usr/bin/env python3
"""Resume local private Z5->C5 recovery using atomic, validated checkpoints.

Previously extracted files must be revalidated; filesize alone is insufficient.
Never publish these decoded original Pokémon model files in GitHub.
"""
import argparse
import csv
import hashlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from native_z5_decoder import decode_stream
from validate_c56 import assess


def task(pair):
    source, destination = map(Path, pair)
    try:
        raw = source.read_bytes()
        if len(raw) < 33:
            raise ValueError("truncated Z5")
        decoded = decode_stream(raw[32:], max_output=16 * 1024 * 1024)
        status, _, serious, _ = assess(decoded)
        if serious:
            raise ValueError("C5 structure invalid: " + "; ".join(serious[:4]))
        tmp = destination.with_suffix(".c5.partial")
        tmp.write_bytes(decoded)
        tmp.replace(destination)
        return source.stem, status, len(decoded), hashlib.sha256(decoded).hexdigest(), ""
    except (OSError, ValueError) as error:
        return source.stem, "error", 0, "", str(error)[:180]


def existing_result(source, destination):
    if not destination.is_file():
        return None
    try:
        data = destination.read_bytes()
        status, _, serious, _ = assess(data)
        if serious:
            return None
        return {"model": source.stem, "status": "existing_" + status,
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "error": ""}
    except (OSError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    files = sorted(args.source.glob("p*.z5"))
    manifest = args.output / "C54_manifest.csv"
    rows = {}
    pending = []
    for source in files:
        destination = args.output / (source.stem + ".c5")
        previous = existing_result(source, destination)
        if previous is not None:
            rows[source.stem] = previous
        else:
            pending.append((str(source), str(destination)))
    fields = ["model", "status", "bytes", "sha256", "error"]
    def checkpoint():
        tmp = manifest.with_suffix(".csv.partial")
        with tmp.open("w", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for source in files:
                writer.writerow(rows.get(source.stem, {
                    "model": source.stem, "status": "pending",
                    "bytes": 0, "sha256": "", "error": ""}))
        tmp.replace(manifest)
    checkpoint()
    queue = pending[:max(0, args.limit)]
    if queue:
        with ProcessPoolExecutor(max_workers=max(1, min(8, args.workers))) as executor:
            for future in as_completed([executor.submit(task, pair) for pair in queue]):
                model, status, length, digest, error = future.result()
                rows[model] = {"model": model, "status": status,
                               "bytes": length, "sha256": digest, "error": error}
                checkpoint()
    print("original:", len(files), "processed:", len(queue),
          "errors:", sum(row["status"] == "error" for row in rows.values()),
          "manifest:", manifest)


if __name__ == "__main__":
    main()
