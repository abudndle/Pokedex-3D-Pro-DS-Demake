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
    struct.pack("<H",0x4b21) * (256*192))
(title / "t1_title.rgb555").write_bytes(
    struct.pack("<H",0x54ab) * (256*192))
# A PRIVATE original title animation may provide additional independent
# frames plus frame durations. All content here is synthetic host test data.
title = Path(sys.argv[1]) / "nitro:" / "ui" / "title"
(title / "t0_01_title.rgb555").write_bytes(
    struct.pack("<H",0x1111) * (256*192))
(title / "t1_01_title.rgb555").write_bytes(
    struct.pack("<H",0x2222) * (256*192))
import zlib
sequence=struct.pack("<4H",0,2,1,3)
(title / "timeline.p3tl").write_bytes(
    struct.pack("<4s4HI",b"P3TL",1,2,0,0,zlib.crc32(sequence))+sequence)
# An all-opaque overlay must never hide the Pokémon model.
(base / "t1_10_records_overlay.rgb555").write_bytes(
    struct.pack("<H", 0x9234) * (256 * 192))
# A short invalid overlay must also be rejected.
(base / "t1_02_search_overlay.rgb555").write_bytes(b"\\x01\\x80")
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Itests/host_ui_stub -Isource \
   source/original_ui_page.c source/title_timeline.c tests/test_c104_original_ui_pages.c \
   -o "$tmp/ui_test"
(cd "$tmp" && ./ui_test)
