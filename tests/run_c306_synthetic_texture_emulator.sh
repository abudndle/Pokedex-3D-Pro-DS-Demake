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
xwd -id "$window" -silent -out c306-home.xwd
if [[ "${C359_ZOOM_ONLY:-0}" == 1 ]]; then
  press() { xdotool keydown "$1"; sleep 0.2; xdotool keyup "$1"; sleep 0.5; }
  tap() { xdotool mousemove --window "$window" "$1" 300; xdotool mousedown 1; sleep 0.2; xdotool mouseup 1; sleep 0.5; }
  # Disable auto-rotation through real Settings input; no emulator memory edits.
  for _ in 1 2 3 4 5 6; do press k; done
  press x; press x; press b
  for _ in 1 2 3 4 5 6; do press i; done
  press x
  xwd -id "$window" -silent -out c359-default.xwd
  for _ in 1 2 3; do tap 220; done
  xwd -id "$window" -silent -out c359-near.xwd
  tap 128
  xwd -id "$window" -silent -out c359-reset.xwd
  for _ in 1 2 3; do tap 30; done
  xwd -id "$window" -silent -out c359-far.xwd
  tap 128
  xwd -id "$window" -silent -out c359-reset-again.xwd
  python3 tests/c359_zoom_frame_gate.py c359-{default,near,reset,far,reset-again}.xwd
  exit 0
fi
# First two synthetic Dex species map to distinct matched material textures.
xdotool keydown x; sleep 0.5; xdotool keyup x
sleep 2
xwd -id "$window" -silent -out c306-red.xwd
xdotool keydown d; sleep 0.5; xdotool keyup d
sleep 2
xwd -id "$window" -silent -out c306-blue.xwd
xdotool keydown b; sleep 0.5; xdotool keyup b
sleep 2
xwd -id "$window" -silent -out c306-back.xwd
kill -0 "$pid"
python3 tests/c306_synthetic_texture_frame_gate.py \
  c306-home.xwd c306-red.xwd c306-blue.xwd c306-back.xwd
echo "C306 two-species synthetic native material texture visual acceptance: PASS"
