#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/species_learnset.c tests/c334_learnsets.c -o "$tmp/learnsets"
"$tmp/learnsets" "$tmp/fixture.p3sl"
