#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/nitro:/ui/pages" "$tmp/nitro:/ui/title"
python3 - "$tmp" <<'PY'
from pathlib import Path
import struct
import sys

base = Path(sys.argv[1]) / "nitro:" / "ui" / "pages"
for screen, page, name, pixel in ((0, 0, "home", 0x1234),
                                 (0, 10, "records", 0x001f),
                                 (1, 0, "home", 0x2345),
                                 (1, 10, "records", 0x03e0)):
    path = base / f"t{screen}_{page:02d}_{name}.rgb555"
    path.write_bytes(struct.pack("<H", pixel) * (256 * 192))
# Original UI supplies explicit bit15 opacity, not a guessed viewport.
# First/last pixels are HUD; center is the 3D model cutout.
source_overlay = [0x9123] * (256 * 192)
source_overlay[1] = 0x0000
source_overlay[256*96+128] = 0x0042
(base / "t1_01_dex_overlay.rgb555").write_bytes(
    struct.pack("<" + "H"*len(source_overlay), *source_overlay))
# Title is a separate original source boot asset on BOTH 3DS screens.
title = Path(sys.argv[1]) / "nitro:" / "ui" / "title"
(title / "t0_title.rgb555").write_bytes(
    struct.pack("<H",0x1234) * (256*192))
(title / "t1_title.rgb555").write_bytes(
    struct.pack("<H",0x2345) * (256*192))
# An all-opaque overlay must never hide the Pokémon model.
(base / "t1_10_records_overlay.rgb555").write_bytes(
    struct.pack("<H", 0x9234) * (256 * 192))
# A short invalid overlay must also be rejected.
(base / "t1_02_search_overlay.rgb555").write_bytes(b"\\x01\\x80")
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Itests/host_ui_stub -Isource \
   source/original_ui_page.c tests/test_c104_original_ui_pages.c \
   -o "$tmp/ui_test"
(cd "$tmp" && ./ui_test)
