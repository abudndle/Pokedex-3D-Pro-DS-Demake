#!/usr/bin/env bash
# C260: asset-free DS-mode DLDI save/restore acceptance in official melonDS 1.1.
# This test NEVER uses Nintendo BIOS, private source assets or a retail ROM.
set -euo pipefail
full_round="${C264_FULL_ROUND:-0}"
detail_only="${C333_DETAIL_ONLY:-0}"
learnset_only="${C334_LEARNSET_ONLY:-0}"
evolution_only="${C358_EVOLUTION_ONLY:-0}"
if [[ "$evolution_only" != 0 && "$evolution_only" != 1 ]]; then exit 2; fi
if [[ "$learnset_only" != 0 && "$learnset_only" != 1 ]]; then
  echo 'C334_LEARNSET_ONLY must be 0 or 1' >&2
  exit 2
fi
if [[ "$detail_only" != 0 && "$detail_only" != 1 ]]; then
  echo 'C333_DETAIL_ONLY must be 0 or 1' >&2
  exit 2
fi
if [[ "$full_round" != 0 && "$full_round" != 1 ]]; then
  echo 'C264_FULL_ROUND must be 0 or 1' >&2
  exit 2
fi
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
Left = 16777234
Up = 16777235
Down = 16777237
Start = 16777220
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
  # melonDS 1.1 Window.cpp installs SIGINT -> Qt onQuit() via socketpair.
  # This flushes FATStorage on normal teardown; X11 WM_DELETE can leave
  # the emulation process running with no visible window.
  kill -INT "$pid"
  # A completed child can remain a zombie until Bash wait() reaps it.
  # kill -0 succeeds for zombies, so inspect process state before failing.
  local state
  for _ in $(seq 1 40); do
    state="$(ps -o stat= -p "$pid" 2>/dev/null || true)"
    if [[ -z "$state" || "$state" == Z* ]]; then break; fi
    sleep 0.25
  done
  state="$(ps -o stat= -p "$pid" 2>/dev/null || true)"
  if [[ -n "$state" && "$state" != Z* ]]; then
    echo "melonDS did not exit cleanly (process state: $state)" >&2
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
if [[ "$detail_only" == 1 || "$learnset_only" == 1 || "$evolution_only" == 1 ]]; then
  if [[ "$learnset_only" == 1 ]]; then
    # Exercise the actual Right handler, not just its portable helper.
    xdotool windowfocus --sync "$window"
    xdotool keydown Right; sleep 0.3; xdotool keyup Right; sleep 2
    capture c334-melonds-right.xwd
    close_cleanly
    python3 tests/c334_fat_learnset_gate.py "$sd_root/export" --navigation
    launch
    capture c334-melonds-right-resumed.xwd
    xdotool windowfocus --sync "$window"
    xdotool keydown Left; sleep 0.3; xdotool keyup Left; sleep 1
  fi
  xdotool windowfocus --sync "$window"
  xdotool keydown Return
  sleep 0.5
  xdotool keyup Return
  sleep 2
  capture c333-melonds-detail.xwd
  if [[ "$evolution_only" == 1 ]]; then
    tap() {
      xdotool mousemove --window "$window" "$1" "$2"
      xdotool mousedown 1; sleep 0.3; xdotool mouseup 1; sleep 2
    }
    # STATS -> ABILITIES -> EVOLUTIONS, using visible native tab controls.
    tap 210 379; tap 210 379
    capture c358-melonds-source.xwd
    tap 128 307
    capture c358-melonds-target.xwd
    tap 128 323
    capture c358-melonds-terminal-held.xwd
    close_cleanly
    python3 tests/c358_evolution_gate.py --fat "$sd_root/export" 4
    launch
    capture c358-melonds-target-resumed.xwd
    xdotool windowfocus --sync "$window"
    for _ in 1 2 3 4; do
      xdotool keydown Left; sleep 0.3; xdotool keyup Left; sleep 0.5
    done
    capture c358-melonds-source-return.xwd
    tap 128 323
    capture c358-melonds-missing.xwd
    tap 128 307
    capture c358-melonds-missing-held.xwd
    close_cleanly
    python3 tests/c358_evolution_gate.py --fat "$sd_root/export" 648
    launch
    capture c358-melonds-missing-resumed.xwd
    close_cleanly
    python3 tests/c358_evolution_gate.py --fat "$sd_root/export" 648
    python3 tests/c358_evolution_gate.py c358-melonds-{source,target,terminal-held,target-resumed,source-return,missing,missing-held,missing-resumed}.xwd
    exit 0
  fi
  if [[ "$learnset_only" == 1 ]]; then
    # Three visible NEXT TAB touches: STATS -> ABILITIES -> EVOLUTIONS -> LEARNSET.
    for _ in 1 2 3; do
      xdotool mousemove --window "$window" 210 379
      xdotool mousedown 1; sleep 0.3; xdotool mouseup 1; sleep 0.5
    done
    capture c334-melonds-learnset-first.xwd
    # Exercise both keypad pagination and the distinct touchscreen row.
    xdotool keydown Down; sleep 0.3; xdotool keyup Down; sleep 0.5
    capture c334-melonds-learnset-key.xwd
    xdotool keydown Up; sleep 0.3; xdotool keyup Up; sleep 0.5
    capture c334-melonds-learnset-back.xwd
    xdotool mousemove --window "$window" 210 347
    xdotool mousedown 1; sleep 0.3; xdotool mouseup 1; sleep 2
    capture c334-melonds-learnset-page.xwd
    python3 tests/c333_melonds_detail_frame_gate.py \
      c334-melonds-learnset-first.xwd c334-melonds-learnset-key.xwd c334-melonds-learnset-page.xwd
    python3 tests/c333_melonds_detail_frame_gate.py \
      c334-melonds-learnset-page.xwd c334-melonds-learnset-first.xwd c334-melonds-learnset-back.xwd
    close_cleanly
    python3 tests/c334_fat_learnset_gate.py "$sd_root/export"
    launch
    capture c334-melonds-learnset-resumed.xwd
    python3 tests/c333_melonds_detail_frame_gate.py \
      c334-melonds-learnset-first.xwd c334-melonds-learnset-page.xwd c334-melonds-learnset-resumed.xwd
    close_cleanly
    python3 tests/c334_fat_learnset_gate.py "$sd_root/export"
    echo 'C334 real melonDS keypad/touch learnset pagination and exact FAT resume: PASS (synthetic only)'
    exit 0
  fi
  close_cleanly
  python3 tests/c333_fat_detail_gate.py "$sd_root/export"
  launch
  capture c333-melonds-detail-resumed.xwd
  python3 tests/c333_melonds_detail_frame_gate.py \
    c260-melonds-fat-favorite.xwd \
    c333-melonds-detail.xwd \
    c333-melonds-detail-resumed.xwd
  close_cleanly
  python3 tests/c333_fat_detail_gate.py "$sd_root/export"
  echo 'C333 real melonDS exact detail-tab navigation and FAT resume: PASS (asset-free only)'
  exit 0
fi
close_cleanly
python3 tests/c260_fat_slot_gate.py "$sd_root/export"
python3 tests/c263_fat_records_gate.py "$sd_root/export"
# Relaunch with the same FAT image and folder, proving cross-boot restoration.
launch
capture c260-melonds-fat-resumed.xwd
python3 tests/c253_melonds_frame_gate.py c260-melonds-fat-home.xwd c260-melonds-fat-resumed.xwd
# C261: from resumed Dex, B returns HOME. Enter Challenge with a real
# stylus tap and answer once. The save must retain the earlier favorite.
xdotool windowfocus --sync "$window"
xdotool keydown z
sleep 0.4
xdotool keyup z
sleep 2
xdotool mousemove --window "$window" 55 334
xdotool mousedown 1
sleep 0.4
xdotool mouseup 1
sleep 2
for stage in question review continued; do
  xdotool keydown x
  sleep 0.4
  xdotool keyup x
  sleep 2
  xwd -id "$window" -silent -out "c261-melonds-challenge-$stage.xwd"
done
# C262: actual captured question/review/continued touchscreen UI must change.
# A nonzero FAT score alone cannot prove the three visual phases advanced.
python3 tests/c262_melonds_challenge_phase_gate.py \
  c261-melonds-challenge-question.xwd \
  c261-melonds-challenge-review.xwd \
  c261-melonds-challenge-continued.xwd
if [[ "$full_round" == 1 ]]; then
  # The first three A presses selected mode, answered #1, and continued
  # into question #2. Nine remaining questions need answer+continue each.
  for _ in $(seq 1 18); do
    xdotool keydown x
    sleep 0.3
    xdotool keyup x
    sleep 0.7
  done
  capture c264-melonds-challenge-results.xwd
fi
sleep 3
close_cleanly
if [[ "$full_round" == 1 ]]; then
  python3 tests/c264_fat_completed_round_gate.py "$sd_root/export"
else
  python3 tests/c261_fat_challenge_gate.py --require-active "$sd_root/export"
fi
# Third real emulator launch must restore Challenge from the FAT checkpoint.
launch
capture c261-melonds-challenge-resumed.xwd
python3 tests/c253_melonds_frame_gate.py c260-melonds-fat-home.xwd c261-melonds-challenge-resumed.xwd
if [[ "$full_round" == 0 ]]; then
  # C332: same exact source-backed answer options / selected question
  # must survive real FAT media teardown and the third melonDS launch.
  python3 tests/c332_melonds_resume_frame_gate.py \
    c261-melonds-challenge-continued.xwd \
    c261-melonds-challenge-resumed.xwd
fi
close_cleanly
if [[ "$full_round" == 1 ]]; then
  python3 tests/c264_fat_completed_round_gate.py "$sd_root/export"
  echo 'C264 real melonDS complete ten-question Challenge, P3RC round and third-boot FAT persistence: PASS (asset-free DS mode only)'
else
  python3 tests/c261_fat_challenge_gate.py --require-active "$sd_root/export"
  # C263: real P3RC Records visit must survive the third emulator boot.
  python3 tests/c263_fat_records_gate.py "$sd_root/export"
  echo 'C261 real melonDS FAT Challenge progress, favorite retention and cross-boot resume: PASS (asset-free DS mode only)'
fi
