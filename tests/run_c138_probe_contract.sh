#!/bin/sh
# Public, asset-free contract test for the private native model probe.
set -eu
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -DC7_TEST_HOST \
  -Itools/host_stub -Isource \
  source/preview_stream.c source/preview_chunk_stream.c source/model_uv.c \
  tests/c138_native_preview_probe.c -o "$tmp/c138_probe"
for invalid in -1 731 abc 49junk ""; do
  if "$tmp/c138_probe" "$invalid" >"$tmp/out" 2>&1; then
    echo "C138 accepted invalid UV count: $invalid" >&2
    exit 1
  fi
  if ! grep -q 'expected UV count must be an integer' "$tmp/out"; then
    echo "C138 invalid UV count did not fail at argument validation" >&2
    cat "$tmp/out" >&2
    exit 1
  fi
done
# Valid boundary values must pass parsing and reach the private asset loader.
# This asset-free test expects missing fixtures, not a successful 730-model run.
for valid in 0 49 730; do
  if (cd "$tmp" && ./c138_probe "$valid") >"$tmp/out" 2>&1; then
    echo "C138 unexpectedly passed without private model assets" >&2
    exit 1
  fi
  if ! grep -q 'missing DS3M p000' "$tmp/out"; then
    echo "C138 valid UV count did not reach native model loading: $valid" >&2
    cat "$tmp/out" >&2
    exit 1
  fi
done
# Exercise the complete 730-model probe with source-free DS3M v1 fixtures.
# This catches native v1 header/color regressions without private assets.
mkdir -p "$tmp/nitrofs/preview"
python3 - "$tmp/nitrofs/preview" <<'PY'
import pathlib
import struct
import sys
root = pathlib.Path(sys.argv[1])
payload = struct.pack('<4sHHII', b'DS3M', 1, 1, 0, 1) + bytes(18)
for model in range(734):
    if model not in (721, 722, 723, 724):
        (root / f'p{model:03d}.ds3m').write_bytes(payload)
PY
if ! (cd "$tmp" && ./c138_probe 0) >"$tmp/out" 2>&1; then
  echo "C138 rejected complete synthetic DS3M v1 roster" >&2
  cat "$tmp/out" >&2
  exit 1
fi
if ! grep -q 'PASS 730/730 models; UV 0' "$tmp/out"; then
  echo "C138 synthetic DS3M v1 roster did not reach complete probe" >&2
  cat "$tmp/out" >&2
  exit 1
fi
# Rebuild the same asset-free roster as DS3M v2 with per-face RGB.
# Validate the native probe's version-specific color contract end-to-end.
python3 - "$tmp/nitrofs/preview" <<'PY'
import pathlib
import struct
import sys
root = pathlib.Path(sys.argv[1])
payload = (struct.pack('<4sHHII', b'DS3M', 2, 1, 0, 1)
           + bytes(18) + bytes((12, 34, 56)))
for model in range(734):
    if model not in (721, 722, 723, 724):
        (root / f'p{model:03d}.ds3m').write_bytes(payload)
PY
if ! (cd "$tmp" && ./c138_probe 0) >"$tmp/out" 2>&1; then
  echo "C138 rejected complete synthetic DS3M v2 roster" >&2
  cat "$tmp/out" >&2
  exit 1
fi
if ! grep -q 'PASS 730/730 models; UV 0' "$tmp/out"; then
  echo "C138 synthetic DS3M v2 roster did not reach complete probe" >&2
  cat "$tmp/out" >&2
  exit 1
fi
# Exercise the full native textured-GL path with synthetic unit UVs for
# every model. No original Pokémon coordinates or texture pixels are used.
python3 - "$tmp/nitrofs/preview" <<'PY'
import pathlib
import struct
import sys
root = pathlib.Path(sys.argv[1])
payload = struct.pack('<4sHH', b'P3UV', 1, 1) + struct.pack('<6h', 0, 0, 4096, 0, 0, 4096)
for model in range(734):
    if model not in (721, 722, 723, 724):
        (root / f'p{model:03d}.p3uv').write_bytes(payload)
PY
if ! (cd "$tmp" && ./c138_probe 730) >"$tmp/out" 2>&1; then
  echo "C138 rejected complete synthetic textured DS3M v2 roster" >&2
  cat "$tmp/out" >&2
  exit 1
fi
if ! grep -q 'PASS 730/730 models; UV 730' "$tmp/out"; then
  echo "C138 synthetic textured roster did not reach complete probe" >&2
  cat "$tmp/out" >&2
  exit 1
fi
# Coverage must be exact: a complete 730-pair roster cannot satisfy a
# falsely reported 729-pair preflight result.
if (cd "$tmp" && ./c138_probe 729) >"$tmp/out" 2>&1; then
  echo "C138 accepted a mismatched preflight UV count" >&2
  exit 1
fi
if ! grep -q 'unexpected coverage loaded=730 uv=730 expected_uv=729' "$tmp/out"; then
  echo "C138 did not report the UV coverage mismatch" >&2
  cat "$tmp/out" >&2
  exit 1
fi
# A companion with a correct header and payload but trailing garbage must
# also fail; the native loader and audit require exact P3UV file lengths.
python3 - "$tmp/nitrofs/preview/p000.p3uv" <<'PY'
import pathlib
import sys
path = pathlib.Path(sys.argv[1])
path.write_bytes(path.read_bytes() + b'\\x00')
PY
if (cd "$tmp" && ./c138_probe 730) >"$tmp/out" 2>&1; then
  echo "C138 accepted a UV companion with trailing bytes" >&2
  exit 1
fi
if ! grep -q 'unexpected coverage loaded=730 uv=729 expected_uv=730' "$tmp/out"; then
  echo "C138 trailing UV bytes did not fail the coverage contract" >&2
  cat "$tmp/out" >&2
  exit 1
fi
python3 - "$tmp/nitrofs/preview/p000.p3uv" <<'PY'
import pathlib
import sys
path = pathlib.Path(sys.argv[1])
path.write_bytes(path.read_bytes()[:-1])
PY
# A corrupt UV companion must fail the complete private probe instead
# of silently reducing the UV-equipped count.
printf 'P3UV' > "$tmp/nitrofs/preview/p000.p3uv"
if (cd "$tmp" && ./c138_probe 730) >"$tmp/out" 2>&1; then
  echo "C138 silently accepted a truncated private UV companion" >&2
  exit 1
fi
if ! grep -q 'unexpected coverage loaded=730 uv=729 expected_uv=730' "$tmp/out"; then
  echo "C138 corrupt UV companion did not fail the coverage contract" >&2
  cat "$tmp/out" >&2
  exit 1
fi
echo 'C138 native probe: full v1/v2 textured rosters and corrupt UV coverage gate PASS'
