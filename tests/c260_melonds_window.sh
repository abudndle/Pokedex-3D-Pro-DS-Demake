#!/usr/bin/env bash
# C260: recapture the *current* melonDS X11 window after Qt startup.
# Qt may replace its splash/top-level window during ROM initialization.
# A cached XID can therefore disappear between xwininfo and xwd.
p3d_melonds_capture_live_window() {
    local output="${1:?output XWD required}" attempts="${2:-12}"
    local tree="${3:-c253-melonds-windows.txt}" candidate tmp n
    tmp="${output}.pending.$$"
    rm -f "$tmp"
    for ((n=0; n<attempts; n++)); do
        if xwininfo -root -tree > "$tree" 2>/dev/null; then
            candidate="$(awk 'tolower($0) ~ /"melonds/ {print $1; exit}' "$tree")"
            if [[ -n "$candidate" ]] &&
               xwininfo -id "$candidate" >/dev/null 2>&1 &&
               xwd -id "$candidate" -silent -out "$tmp" >/dev/null 2>&1 &&
               [[ -s "$tmp" ]]; then
                mv -f "$tmp" "$output"
                printf '%s\n' "$candidate"
                return 0
            fi
        fi
        rm -f "$tmp"
        sleep 0.5
    done
    rm -f "$tmp"
    return 1
}
