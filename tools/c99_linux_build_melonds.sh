#!/usr/bin/env bash
# Private original-derived asset workflow; never share ROMs or source pixels.
set -Eeuo pipefail
if [[ "$#" -lt 2 ]];then
  echo "Usage: $0 SOURCE_REPOSITORY PRIVATE_C98_NITROFS_ZIP [RESULTS_DIR]" >&2
  exit 2
fi
ROOT="$(realpath "$1")"
ZIP="$(realpath "$2")"
OUT="$(realpath -m "$PWD/c99_linux_results")"
if [[ "$#" -ge 3 ]];then OUT="$(realpath -m "$3")";fi
mkdir -p "$OUT"
if [[ ! -f "$ROOT/Makefile.native" || ! -f "$ZIP" ]];then
  echo "Source checkout or private C98 archive missing" >&2;exit 2
fi
if [[ ! -x /opt/wonderful/toolchain/gcc-arm-none-eabi/bin/arm-none-eabi-gcc ||
      ! -f /opt/blocksds/core/sys/crts/ds_arm9.specs ]];then
  echo "BLOCKED: BlocksDS ARM compiler is not installed" | tee "$OUT/build_status.txt"
  echo "See https://blocksds.skylyrac.net/docs/setup/linux/"
  exit 3
fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 - "$ZIP" "$TMP/nitrofs" <<'PY'
import pathlib,sys,zipfile
root=pathlib.Path(sys.argv[2]);root.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(sys.argv[1]) as z:
    if z.testzip() is not None:raise SystemExit("Private ZIP CRC failed")
    for name in z.namelist():
        parts=pathlib.PurePosixPath(name).parts
        if not parts or name.startswith("/") or any(x in ("..",".") for x in parts):
            raise SystemExit("Unsafe private ZIP path")
        target=root.joinpath(*parts);target.parent.mkdir(parents=True,exist_ok=True)
        if not name.endswith("/"):target.write_bytes(z.read(name))
PY
( cd "$ROOT" && make -f Makefile.native "NITROFSDIR=$TMP/nitrofs" rom ) \
  2>&1 | tee "$OUT/native_build.log"
ROM="$ROOT/Pokedex3D_DS_BlocksDS.nds"
test -s "$ROM" || { echo "Native ROM was not produced" >&2;exit 4; }
cp "$ROM" "$OUT/C99_PRIVATE_DEVELOPMENT_ONLY.nds"
MELON="$(command -v melonDS || command -v melonds || true)"
if [[ -z "$MELON" ]];then
  echo "BLOCKED: no melonDS binary; emulator screenshots NOT captured" \
    | tee "$OUT/emulator_status.txt"
  exit 0
fi
echo "Launching melonDS GUI for actual manual screenshots" | tee "$OUT/emulator_status.txt"
"$MELON" "$OUT/C99_PRIVATE_DEVELOPMENT_ONLY.nds"
