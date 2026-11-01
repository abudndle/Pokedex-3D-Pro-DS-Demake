#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp" <<'PY'
from pathlib import Path
import struct,sys,zlib
folder=Path(sys.argv[1])
def mapped(events,frames=2):
    payload=b"".join(struct.pack("<HH",*e) for e in events)
    return struct.pack("<4s4HI",b"P3TC",1,frames,len(events),0,
                       zlib.crc32(payload))+payload
def sound(rate=16000,samples=32):
    pcm=struct.pack("<%dh"%samples,*range(samples))
    return struct.pack("<4sHHII",b"P3SA",1,rate,samples,zlib.crc32(pcm))+pcm
good=mapped([(0,1),(1,2)])
(folder/"good.p3tc").write_bytes(good)
(folder/"static.p3tc").write_bytes(mapped([(0,1)],1))
(folder/"wrongcrc.p3tc").write_bytes(good[:-1]+bytes([good[-1]^1]))
(folder/"unordered.p3tc").write_bytes(mapped([(1,1),(0,2)]))
(folder/"wrongframes.p3tc").write_bytes(mapped([(0,1),(1,2)],3))
(folder/"extra.p3tc").write_bytes(good+b"\0")
(folder/"sound.p3sa").write_bytes(sound())
bad=bytearray(sound());bad[-1]^=1
(folder/"badcrc.p3sa").write_bytes(bad)
(folder/"extra.p3sa").write_bytes(sound()+b"\0")
(folder/"badfreq.p3sa").write_bytes(sound(rate=2000))
(folder/"huge.p3sa").write_bytes(struct.pack("<4sHHII",b"P3SA",1,16000,16385,0))
PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
   source/title_audio.c tests/test_c118_title_audio.c -o "$tmp/test"
"$tmp/test" "$tmp/good.p3tc" "$tmp/static.p3tc" \
 "$tmp/wrongcrc.p3tc" "$tmp/unordered.p3tc" \
 "$tmp/wrongframes.p3tc" "$tmp/extra.p3tc" \
 "$tmp/sound.p3sa" "$tmp/badcrc.p3sa" \
 "$tmp/extra.p3sa" "$tmp/badfreq.p3sa" "$tmp/huge.p3sa"
