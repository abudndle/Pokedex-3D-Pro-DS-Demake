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
# C254: melonDS 1.1 uses Qt key codes, not SDL keycodes. Its fresh
# [Instance0.Keyboard] table defaults to zero (unbound) for each button.
# Source: melonDS 1.1 Config.cpp / EmuInstanceInput.cpp / main.cpp.
# Only write this isolated CI config for the SHA-pinned official AppImage.
mkdir -m 700 "$XDG_CONFIG_HOME/melonDS"
cat > "$XDG_CONFIG_HOME/melonDS/melonDS.toml" <<'TOML'
# melonDS 1.1 TOML serializer requires an explicit parent table; an
# implicit [Instance0] can abort on Save() after launch.
[Instance0]
[Instance0.Keyboard]
A = 88
B = 90
Right = 16777236
TOML
chmod 600 "$XDG_CONFIG_HOME/melonDS/melonDS.toml"
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
# C255: in DS mode, AR Viewer must remain disabled, even when touched.
# The 6th HOME row is at DS y=168 / Qt window y=379; do not infer DSi.
xdotool mousemove --window "$window" 55 382
xdotool mousedown 1
sleep 0.4
xdotool mouseup 1
sleep 2
xwd -id "$window" -silent -out c255-melonds-ar-disabled.xwd
# After selecting disabled AR, HOME scrolls up one 16px row; Move Dex
# is now the first visible row at Qt y=302 (not the old y=318).
xdotool mousemove --window "$window" 55 302
xdotool mousedown 1
sleep 0.4
xdotool mouseup 1
sleep 2
xwd -id "$window" -silent -out c255-melonds-move-dex.xwd
xdotool keydown z
sleep 0.4
xdotool keyup z
sleep 2
xwd -id "$window" -silent -out c255-melonds-move-back.xwd
python3 tests/c255_melonds_ds_ar_gate.py \
  c253-melonds-boot.xwd c255-melonds-ar-disabled.xwd \
  c255-melonds-move-dex.xwd c255-melonds-move-back.xwd
echo "C255 real melonDS DS-mode disabled AR and Move Dex/B: PASS (not DSi camera)"
# C256: HOME has returned from Move Dex; challenge/records/album are
# visible rows 3/4/5. Verify each genuine touchscreen entry and B exit.
for spec in 'challenge:334' 'records:350' 'album:366'; do
  name="${spec%%:*}"
  y="${spec##*:}"
  xdotool mousemove --window "$window" 55 "$y"
  xdotool mousedown 1
  sleep 0.4
  xdotool mouseup 1
  sleep 2
  xwd -id "$window" -silent -out "c256-melonds-$name.xwd"
  xdotool keydown z
  sleep 0.4
  xdotool keyup z
  sleep 2
  xwd -id "$window" -silent -out "c256-melonds-$name-back.xwd"
done
python3 tests/c256_melonds_menu_gate.py \
  c253-melonds-boot.xwd \
  c256-melonds-challenge.xwd c256-melonds-challenge-back.xwd \
  c256-melonds-records.xwd c256-melonds-records-back.xwd \
  c256-melonds-album.xwd c256-melonds-album-back.xwd
echo "C256 real melonDS Challenge/Records/Album touchscreen/B: PASS (asset-free only)"
# C257: Settings is the seventh HOME entry. Select disabled AR (sixth)
# first to scroll the six-row text menu, then tap the last visible row.
# Compare against this scrolled HOME, not the original unscrolled capture.
xdotool mousemove --window "$window" 55 382
xdotool mousedown 1
sleep 0.4
xdotool mouseup 1
sleep 2
xwd -id "$window" -silent -out c257-melonds-home-scrolled.xwd
xdotool mousemove --window "$window" 55 382
xdotool mousedown 1
sleep 0.4
xdotool mouseup 1
sleep 2
xwd -id "$window" -silent -out c257-melonds-settings.xwd
xdotool keydown x
sleep 0.4
xdotool keyup x
sleep 2
xwd -id "$window" -silent -out c257-melonds-settings-toggled.xwd
xdotool keydown z
sleep 0.4
xdotool keyup z
sleep 2
xwd -id "$window" -silent -out c257-melonds-settings-back.xwd
python3 tests/c257_melonds_settings_gate.py \
  c257-melonds-home-scrolled.xwd c257-melonds-settings.xwd \
  c257-melonds-settings-toggled.xwd c257-melonds-settings-back.xwd
echo "C257 real melonDS Settings/A rotation/B: PASS (asset-free, no save proof)"
# C258: Records is HOME index 3. The current scrolled HOME starts at
# index 1, so the third visible row is Records (Qt y=334).
xdotool mousemove --window "$window" 55 334
xdotool mousedown 1
sleep 0.4
xdotool mouseup 1
sleep 2
xwd -id "$window" -silent -out c258-melonds-records-regions.xwd
for tab in recent quizzes; do
  xdotool keydown Right
  sleep 0.4
  xdotool keyup Right
  sleep 2
  xwd -id "$window" -silent -out "c258-melonds-records-$tab.xwd"
done
xdotool keydown z
sleep 0.4
xdotool keyup z
sleep 2
xwd -id "$window" -silent -out c258-melonds-records-back.xwd
python3 tests/c258_melonds_records_tabs_gate.py \
  c253-melonds-boot.xwd c258-melonds-records-regions.xwd \
  c258-melonds-records-recent.xwd c258-melonds-records-quizzes.xwd \
  c258-melonds-records-back.xwd
echo "C258 real melonDS Records Regions/Recent/Quizzes/B: PASS (asset-free)"
echo "C253 melonDS 1.1 DS boot + real touchscreen navigation: PASS (not DSi or original assets)"
