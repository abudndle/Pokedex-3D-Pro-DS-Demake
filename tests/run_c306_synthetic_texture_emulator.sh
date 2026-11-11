#!/usr/bin/env bash
# C306: DeSmuME 0.9.13 synthetic, material-gated native texture visual QA.
set -euo pipefail
rom="${1:?expected synthetic texture ROM path}"
test -s "$rom"
case "$(dpkg-query -W -f='${Version}' desmume)" in
  0.9.13-*) ;;
  *) echo "Unsupported DeSmuME SDL key ABI" >&2; exit 1 ;;
esac
temp="$(mktemp -d)"
trap 'if [ -n "${pid:-}" ]; then kill "$pid" 2>/dev/null || true; fi; rm -rf "$temp"' EXIT
export XDG_CONFIG_HOME="$temp/config"
mkdir -m 700 "$XDG_CONFIG_HOME"
python3 tools/c236_desmume_keymap.py --xdg-config-home "$XDG_CONFIG_HOME"
cc -std=c11 -Wall -Wextra -Werror -fPIC -shared \
  tests/c238_sdl_event_trace.c -ldl -o "$temp/input-adapter.so"
env LD_PRELOAD="$temp/input-adapter.so" P3D_C240_ADAPT_0913=1 \
  /usr/games/desmume-cli --disable-sound "$rom" >"$temp/desmume.log" 2>&1 &
pid=$!
window=""
for attempt in $(seq 1 30); do
  window="$(xwininfo -root -tree | awk '/"Desmume/{print $1; exit}')"
  if [ -n "$window" ]; then break; fi
  if ! kill -0 "$pid" 2>/dev/null; then break; fi
  sleep 0.5
done
if [ -z "$window" ]; then cat "$temp/desmume.log"; exit 1; fi
sleep 12
xdotool windowfocus --sync "$window"
press() { xdotool keydown "$1"; sleep 0.3; xdotool keyup "$1"; sleep 0.5; }
# Keep both authored legacy triangles visible at the capture angle.
for _ in 1 2 3 4 5 6; do press k; done
press x; press x; press b
for _ in 1 2 3 4 5 6; do press i; done
xwd -id "$window" -silent -out c306-home.xwd
# First two synthetic Dex species map to distinct matched material textures.
xdotool keydown x; sleep 0.5; xdotool keyup x
sleep 2
xwd -id "$window" -silent -out c306-red.xwd
xdotool keydown d; sleep 0.5; xdotool keyup d
sleep 2
xwd -id "$window" -silent -out c306-blue.xwd
xdotool keydown d; sleep 0.5; xdotool keyup d
sleep 2
xwd -id "$window" -silent -out c306-legacy.xwd
xdotool keydown d; sleep 0.5; xdotool keyup d
sleep 2
xwd -id "$window" -silent -out c306-mixed.xwd
xdotool keydown b; sleep 0.5; xdotool keyup b
sleep 2
xwd -id "$window" -silent -out c306-back.xwd
kill -0 "$pid"
python3 tests/c306_synthetic_texture_frame_gate.py \
  c306-home.xwd c306-red.xwd c306-blue.xwd c306-legacy.xwd c306-mixed.xwd c306-back.xwd
echo "C306 native and mixed legacy texture visual acceptance: PASS"
