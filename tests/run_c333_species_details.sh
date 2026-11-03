#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
 source/species_details.c tests/c333_species_details.c -o "$tmp/c333"
"$tmp/c333" "$tmp/species.p3sd"
