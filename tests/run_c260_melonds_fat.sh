#!/usr/bin/env bash
# C260: asset-free DS-mode DLDI save/restore acceptance in official melonDS 1.1.
# This test NEVER uses Nintendo BIOS, private source assets or a retail ROM.
set -euo pipefail
rom="${1:?expected asset-free BlocksDS ROM}"
app_run="${2:?expected SHA-pinned melonDS AppRun}"
test -s "$rom" && test -x "$app_run"
source tests/c260_melonds_window.sh
export QT_QPA_PLATFORM=xcb LIBGL_ALWAYS_SOFTWARE=1 SDL_VIDEODRIVER=x11
export XDG_CONFIG_HOME="$(mktemp -d)"
sd_root="$(mktemp -d)"
mkdir -m 700 "$XDG_CONFIG_HOME/melonDS" "$sd_root/export"
# Verified from melonDS 1.1 Config.cpp and EmuInstance::getSDCardArgs:
# DLDI.Enable, ImagePath, ImageSize (1=256MiB), ReadOnly and FolderSync.
cat > "$XDG_CONFIG_HOME/melonDS/melonDS.toml" <<TOML
[Instance0]
[Instance0.Keyboard]
A = 88
B = 90
Right = 16777236
[DLDI]
Enable = true
ImagePath = "$sd_root/dldi.bin"
ImageSize = 1
ReadOnly = false
FolderSync = true
FolderPath = "$sd_root/export"
TOML
chmod 600 "$XDG_CONFIG_HOME/melonDS/melonDS.toml"
pid=""
cleanup() {
  if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; fi
  rm -rf "$XDG_CONFIG_HOME" "$sd_root"
}
trap cleanup EXIT
launch() {
  "$app_run" "$rom" > "$sd_root/melonds.log" 2>&1 &
  pid=$!
  sleep 15
  if ! kill -0 "$pid" 2>/dev/null; then
    tail -60 "$sd_root/melonds.log" >&2 || true
    echo 'melonDS exited before FAT capture' >&2
    return 1
  fi
}
capture() {
  local dest="$1"
  if ! window="$(p3d_melonds_capture_live_window "$dest" 20 c260-melonds-windows.txt)"; then
    tail -60 "$sd_root/melonds.log" >&2 || true
    cat c260-melonds-windows.txt >&2 || true
    echo 'no live melonDS window for FAT test' >&2
    return 1
  fi
}
close_cleanly() {
  xdotool windowclose "$window"
  for _ in $(seq 1 30); do
    if ! kill -0 "$pid" 2>/dev/null; then break; fi
    sleep 0.25
  done
  if kill -0 "$pid" 2>/dev/null; then
    echo 'melonDS did not exit cleanly; cannot assert FAT flush' >&2
    return 1
  fi
  wait "$pid" || { echo 'melonDS exited with an error' >&2; return 1; }
  pid=""
}
launch
capture c260-melonds-fat-home.xwd
python3 tests/c253_melonds_frame_gate.py c260-melonds-fat-home.xwd
xdotool windowfocus --sync "$window"
xdotool mousemove --window "$window" 50 300
xdotool mousedown 1
sleep 0.5
xdotool mouseup 1
sleep 2
capture c260-melonds-fat-dex.xwd
python3 tests/c253_melonds_frame_gate.py c260-melonds-fat-home.xwd c260-melonds-fat-dex.xwd
xdotool windowfocus --sync "$window"
xdotool keydown x
sleep 0.4
xdotool keyup x
sleep 4
capture c260-melonds-fat-favorite.xwd
close_cleanly
python3 tests/c260_fat_slot_gate.py "$sd_root/export"
# Relaunch with the same FAT image and folder, proving cross-boot restoration.
launch
capture c260-melonds-fat-resumed.xwd
python3 tests/c253_melonds_frame_gate.py c260-melonds-fat-home.xwd c260-melonds-fat-resumed.xwd
close_cleanly
python3 tests/c260_fat_slot_gate.py "$sd_root/export"
echo 'C260 real melonDS DLDI P3SV/P3RV save and reboot resume: PASS (asset-free DS mode only)'
