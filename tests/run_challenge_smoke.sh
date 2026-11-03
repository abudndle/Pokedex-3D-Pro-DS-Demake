#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource source/challenge.c tests/test_challenge_smoke.c -o "$tmp/test"
"$tmp/test"
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
 source/challenge.c tests/test_c232_challenge_review.c -o "$tmp/review"
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
 source/challenge.c tests/test_c330_challenge_replay.c -o "$tmp/replay"
"$tmp/replay"
"$tmp/review"
