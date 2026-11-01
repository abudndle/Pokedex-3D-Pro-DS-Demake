#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/nitro:/ui/pages"
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
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Itests/host_ui_stub -Isource \
   source/original_ui_page.c tests/test_c104_original_ui_pages.c \
   -o "$tmp/ui_test"
(cd "$tmp" && ./ui_test)
