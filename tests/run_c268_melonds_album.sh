#!/usr/bin/env bash
# C268: real melonDS 1.1 DLDI FolderSync Album browse/page/delete/reboot.
# No Nintendo data, private ROMs or camera access; the PNGs are generated fixtures.
set -euo pipefail
viewer_only="${C355_VIEWER_ONLY:-0}"
resume_only="${C356_RESUME_ONLY:-0}"
slideshow_only="${C357_SLIDESHOW_ONLY:-0}"
if [[ "$slideshow_only" != 0 && "$slideshow_only" != 1 ]]; then exit 2; fi
if [[ "$resume_only" != 0 && "$resume_only" != 1 ]]; then exit 2; fi
if [[ "$viewer_only" != 0 && "$viewer_only" != 1 ]]; then exit 2; fi
rom="${1:?asset-free BlocksDS ROM required}"
app_run="${2:?SHA-pinned melonDS 1.1 AppRun required}"
test -s "$rom" && test -x "$app_run"
source tests/c260_melonds_window.sh
export QT_QPA_PLATFORM=xcb LIBGL_ALWAYS_SOFTWARE=1 SDL_VIDEODRIVER=x11
export XDG_CONFIG_HOME="$(mktemp -d)"
sd_root="$(mktemp -d)"
mkdir -m 700 "$XDG_CONFIG_HOME/melonDS" "$sd_root/export"
# Generate real, independently authored 1x1 PNGs; the native Album reads only
# filenames, but no private Nintendo images or meaningless zero-byte files.
python3 - "$sd_root/export" <<'PY'
import pathlib, struct, sys, zlib
root = pathlib.Path(sys.argv[1]) / 'Pokedex 3D Pro' / 'Photos'
root.mkdir(parents=True)
def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
for n in range(1, 10):
    rgb = bytes((n * 17 % 256, n * 29 % 256, n * 41 % 256))
    scanline = b'\0' + rgb
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)) +
           chunk(b'IDAT', zlib.compress(scanline)) + chunk(b'IEND', b''))
    (root / f'AR_{n:04d}.png').write_bytes(png)
PY
python3 tests/c268_fat_album_gate.py "$sd_root/export"
cat > "$XDG_CONFIG_HOME/melonDS/melonDS.toml" <<TOML
[Instance0]
[Instance0.Keyboard]
A = 88
B = 90
X = 83
Left = 16777234
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
        echo 'C268 melonDS exited before Album capture' >&2
        return 1
    fi
}
capture() {
    if ! window="$(p3d_melonds_capture_live_window "$1" 20 c268-melonds-windows.txt)"; then
        tail -60 "$sd_root/melonds.log" >&2 || true
        echo 'C268 no live melonDS window' >&2
        return 1
    fi
}
press() {
    xdotool windowfocus --sync "$window"
    xdotool keydown "$1"
    sleep 0.4
    xdotool keyup "$1"
    sleep 2
}
close_cleanly() {
    # SIGINT is melonDS 1.1's Qt onQuit handler; allow FolderSync to flush.
    kill -INT "$pid"
    local state
    for _ in $(seq 1 40); do
        state="$(ps -o stat= -p "$pid" 2>/dev/null || true)"
        if [[ -z "$state" || "$state" == Z* ]]; then break; fi
        sleep 0.25
    done
    state="$(ps -o stat= -p "$pid" 2>/dev/null || true)"
    if [[ -n "$state" && "$state" != Z* ]]; then
        echo "C268 melonDS did not exit cleanly: $state" >&2
        return 1
    fi
    wait "$pid" || { echo 'C268 melonDS exited with error' >&2; return 1; }
    pid=""
}
launch
capture c268-melonds-home.xwd
python3 tests/c253_melonds_frame_gate.py c268-melonds-home.xwd
# HOME's fifth unscrolled entry is Album: verified C256 touch y=366.
xdotool windowfocus --sync "$window"
xdotool mousemove --window "$window" 55 366
xdotool mousedown 1
sleep 0.5
xdotool mouseup 1
sleep 2
capture c268-melonds-album-first.xwd
if [[ "$slideshow_only" == 1 ]]; then
    press x
    capture c357-melonds-open.xwd
    press x
    capture c357-melonds-playing.xwd
    sleep 3.5
    press x
    capture c357-melonds-paused.xwd
    sleep 6
    capture c357-melonds-held.xwd
    # Touch the visible play/pause row, then manual next must pause playback.
    xdotool mousemove --window "$window" 128 355
    xdotool mousedown 1; sleep 0.4; xdotool mouseup 1; sleep 2
    capture c357-melonds-touch.xwd
    sleep 3.5
    press x
    capture c357-melonds-touch-advanced.xwd
    press Right
    capture c357-melonds-manual.xwd
    sleep 6
    capture c357-melonds-manual-held.xwd
    press x
    close_cleanly
    launch
    capture c357-melonds-restored.xwd
    press x
    sleep 3.5
    press x
    capture c357-melonds-restarted.xwd
    press z
    capture c357-melonds-list.xwd
    close_cleanly
    python3 tests/c357_slideshow_gate.py --fat "$sd_root/export"
    python3 tests/c357_slideshow_gate.py c357-melonds-{open,playing,paused,held,touch,touch-advanced,manual,manual-held,restored,restarted,list}.xwd
    exit 0
fi
if [[ "$resume_only" == 1 ]]; then
    press x
    press Right
    capture c356-melonds-photo-open.xwd
    close_cleanly
    python3 tests/c356_photo_resume_gate.py --fat "$sd_root/export" saved
    launch
    capture c356-melonds-photo-resumed.xwd
    close_cleanly
    python3 tests/c356_photo_resume_gate.py --fat "$sd_root/export" saved
    python3 - "$sd_root/export" <<'PY'
from pathlib import Path
import sys
sys.path.insert(0,'tests')
from c355_album_view_gate import synthetic_photo
(Path(sys.argv[1])/'Pokedex 3D Pro'/'Photos'/'AR_0010.png').write_bytes(synthetic_photo(10))
PY
    launch
    capture c356-melonds-photo-reordered.xwd
    close_cleanly
    python3 tests/c356_photo_resume_gate.py --fat "$sd_root/export" reordered
    python3 - "$sd_root/export" <<'PY'
from pathlib import Path
import sys
sys.path.insert(0,'tests')
from c355_album_view_gate import synthetic_photo
(Path(sys.argv[1])/'Pokedex 3D Pro'/'Photos'/'AR_0008.png').write_bytes(synthetic_photo(7))
PY
    launch
    capture c356-melonds-photo-changed.xwd
    close_cleanly
    python3 tests/c356_photo_resume_gate.py --fat "$sd_root/export" changed
    python3 tests/c356_photo_resume_gate.py c356-melonds-photo-{open,resumed,reordered,changed}.xwd
    echo 'C356 real melonDS exact-photo resume, reordered roster and changed-media rejection: PASS (synthetic only)'
    exit 0
fi
if [[ "$viewer_only" == 1 ]]; then
    press x
    capture c355-melonds-photo-first.xwd
    press Right
    capture c355-melonds-photo-next.xwd
    press Left
    capture c355-melonds-photo-return.xwd
    xdotool mousemove --window "$window" 220 379
    xdotool mousedown 1; sleep 0.4; xdotool mouseup 1; sleep 2
    capture c355-melonds-photo-touch.xwd
    xdotool mousemove --window "$window" 128 379
    xdotool mousedown 1; sleep 0.4; xdotool mouseup 1; sleep 2
    xdotool mousemove --window "$window" 128 391
    xdotool mousedown 1; sleep 0.4; xdotool mouseup 1; sleep 2
    capture c355-melonds-photo-reopen.xwd
    press z
    capture c355-melonds-photo-list.xwd
    close_cleanly
    python3 tests/c355_album_view_gate.py --fat "$sd_root/export"
    launch
    capture c355-melonds-photo-resumed.xwd
    close_cleanly
    python3 tests/c355_album_view_gate.py --fat "$sd_root/export"
    python3 tests/c355_album_view_gate.py \
        c355-melonds-photo-first.xwd c355-melonds-photo-next.xwd \
        c355-melonds-photo-return.xwd c355-melonds-photo-touch.xwd \
        c355-melonds-photo-reopen.xwd c355-melonds-photo-list.xwd \
        c355-melonds-photo-resumed.xwd
    echo 'C355 real melonDS PNG pixels, keypad/touch, B/list and unchanged media: PASS (synthetic only)'
    exit 0
fi
press Right
capture c268-melonds-album-second.xwd
press Left
capture c268-melonds-album-return.xwd
# melonDS Qt X=83 (S key), A=88 (X key). No simulated filesystem delete.
press s
capture c268-melonds-album-confirm.xwd
press x
capture c268-melonds-album-deleted.xwd
close_cleanly
# Prove the emulator itself deleted AR_0009.png on its mounted FAT folder.
python3 tests/c268_fat_album_gate.py "$sd_root/export" --after-delete
launch
capture c268-melonds-album-resumed.xwd
close_cleanly
python3 tests/c268_fat_album_gate.py "$sd_root/export" --after-delete
python3 tests/c268_melonds_album_frame_gate.py \
    c268-melonds-home.xwd c268-melonds-album-first.xwd \
    c268-melonds-album-second.xwd c268-melonds-album-return.xwd \
    c268-melonds-album-confirm.xwd c268-melonds-album-deleted.xwd \
    c268-melonds-album-resumed.xwd
echo 'C268 real melonDS 1.1 DS-mode FAT Album browse/page/X+A delete/reboot: PASS (synthetic media only)'
