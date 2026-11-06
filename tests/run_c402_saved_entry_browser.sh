#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/saved_entry_browser.c tests/c402_saved_entry_browser.c -o "$tmp/test"
"$tmp/test"
