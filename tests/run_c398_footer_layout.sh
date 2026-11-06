#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror ${P3D_HOST_SANITIZERS:-} -Isource source/page_footer.c tests/c398_footer_layout.c -o "$tmp/footer"
"$tmp/footer"
