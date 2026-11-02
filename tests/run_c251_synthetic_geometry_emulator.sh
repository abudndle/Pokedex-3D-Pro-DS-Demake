#!/usr/bin/env bash
# C251: asset-free synthetic P3VX/P3IX NitroFS ROM, real DeSmuME input/captures.
set -euo pipefail
rom="${1:?expected synthetic ROM path}"
test -s "$rom"
case "$(dpkg-query -W -f='${Version}' desmume)" in
  0.9.13-*) ;;
  *) echo "Unsupported DeSmuME SDL key ABI; fail closed" >&2; exit 1 ;;
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
xwd -id "$window" -silent -out c251-home.xwd
# HOME highlights Pokédex first; species #001 maps to synthetic p002.
xdotool keydown x
sleep 0.5
xdotool keyup x
sleep 2
xwd -id "$window" -silent -out c251-mapped.xwd
# #002 is explicitly unavailable in synthetic P3SM; no geometry fallback.
xdotool keydown d
sleep 0.5
xdotool keyup d
sleep 2
xwd -id "$window" -silent -out c251-unmapped.xwd
xdotool keydown b
sleep 0.5
xdotool keyup b
sleep 2
xwd -id "$window" -silent -out c251-back.xwd
kill -0 "$pid"
python3 tests/c251_synthetic_geometry_frame_gate.py \
  c251-home.xwd c251-mapped.xwd c251-unmapped.xwd c251-back.xwd
echo "C251 synthetic NitroFS ROM navigation and dual-screen frame gate: PASS"
