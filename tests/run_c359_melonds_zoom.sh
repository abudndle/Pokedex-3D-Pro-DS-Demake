#!/usr/bin/env bash
# Actual pinned melonDS, authored synthetic native geometry only.
set -euo pipefail
rom="${1:?synthetic ROM required}"; app="${2:?pinned melonDS AppRun required}"
source tests/c260_melonds_window.sh
export QT_QPA_PLATFORM=xcb LIBGL_ALWAYS_SOFTWARE=1 SDL_VIDEODRIVER=x11
export XDG_CONFIG_HOME="$(mktemp -d)"
mkdir -p "$XDG_CONFIG_HOME/melonDS"
cat > "$XDG_CONFIG_HOME/melonDS/melonDS.toml" <<'TOML'
[Instance0]
[Instance0.Keyboard]
A = 88
B = 90
Up = 16777235
Down = 16777237
TOML
pid=''
trap 'if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; fi; rm -rf "$XDG_CONFIG_HOME"' EXIT
"$app" "$rom" > "$XDG_CONFIG_HOME/emulator.log" 2>&1 & pid=$!
sleep 15
capture() { window="$(p3d_melonds_capture_live_window "$1" 20 c359-windows.txt)"; }
press() { xdotool windowfocus --sync "$window"; xdotool keydown "$1"; sleep 0.3; xdotool keyup "$1"; sleep 0.5; }
tap() { xdotool mousemove --window "$window" "$1" 327; xdotool mousedown 1; sleep 0.3; xdotool mouseup 1; sleep 0.5; }
capture c359-home.xwd
for _ in 1 2 3 4 5 6; do press Down; done
press x; press x; press z
for _ in 1 2 3 4 5 6; do press Up; done
press x
capture c359-default.xwd
for _ in 1 2 3; do tap 220; done
capture c359-near.xwd
tap 128; capture c359-reset.xwd
for _ in 1 2 3; do tap 30; done
capture c359-far.xwd
tap 128; capture c359-reset-again.xwd
kill -0 "$pid"
python3 tests/c359_zoom_frame_gate.py c359-{default,near,reset,far,reset-again}.xwd
