#!/usr/bin/env bash
# C253: independent official melonDS 1.1 DS-mode boot probe.
# This uses only an asset-free development ROM and public emulator binaries.
set -euo pipefail
rom="${1:?expected development ROM}"
app_run="${2:?expected verified melonDS AppRun}"
test -s "$rom"
test -x "$app_run"
export QT_QPA_PLATFORM=xcb
export LIBGL_ALWAYS_SOFTWARE=1
export SDL_VIDEODRIVER=x11
export XDG_CONFIG_HOME="$(mktemp -d)"
temp="$(mktemp -d)"
trap 'if [ -n "${pid:-}" ]; then kill "$pid" 2>/dev/null || true; fi; rm -rf "$temp" "$XDG_CONFIG_HOME"' EXIT
"$app_run" "$rom" >"$temp/melonds.log" 2>&1 &
pid=$!
window=""
for attempt in $(seq 1 40); do
  xwininfo -root -tree >c253-melonds-windows.txt
  window="$(awk 'tolower($0) ~ /"melonds/ {print $1; exit}' c253-melonds-windows.txt)"
  if [ -n "$window" ]; then break; fi
  if ! kill -0 "$pid" 2>/dev/null; then break; fi
  sleep 0.5
done
if [ -z "$window" ]; then
  echo "melonDS window not found" >&2
  tail -50 "$temp/melonds.log" || true
  exit 1
fi
sleep 12
if ! kill -0 "$pid" 2>/dev/null; then
  echo "melonDS exited before DS boot capture" >&2
  tail -50 "$temp/melonds.log" || true
  exit 1
fi
xwd -id "$window" -silent -out c253-melonds-boot.xwd
test -s c253-melonds-boot.xwd
python3 tests/c253_melonds_frame_gate.py c253-melonds-boot.xwd
# Real touch input: first HOME menu entry is Pokédex, inside the lower DS
# display. Hold stylus long enough to be sampled by the emulated touch scan.
xdotool windowfocus --sync "$window"
xdotool mousemove --window "$window" 50 300
xdotool mousedown 1
sleep 0.5
xdotool mouseup 1
sleep 3
xwd -id "$window" -silent -out c253-melonds-dex.xwd
python3 tests/c253_melonds_frame_gate.py c253-melonds-boot.xwd c253-melonds-dex.xwd
# C254: independently exercise the actual melonDS 1.1 keyboard path.
# Never substitute a synthetic frame or inferred DS keypad state for proof.
# If the emulator has no default keyboard binding, fail closed and diagnose.
xdotool windowfocus --sync "$window"
xdotool keydown Right
sleep 0.5
xdotool keyup Right
sleep 2
xwd -id "$window" -silent -out c254-melonds-right.xwd
xdotool keydown z
sleep 0.5
xdotool keyup z
sleep 2
xwd -id "$window" -silent -out c254-melonds-back.xwd
python3 tests/c254_melonds_nav_gate.py \
  c253-melonds-boot.xwd c253-melonds-dex.xwd \
  c254-melonds-right.xwd c254-melonds-back.xwd
echo "C254 melonDS 1.1 real Right/B navigation: PASS (DS-mode asset-free only)"
echo "C253 melonDS 1.1 DS boot + real touchscreen navigation: PASS (not DSi or original assets)"
