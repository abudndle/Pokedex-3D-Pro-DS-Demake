#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
python3 - "$tmp" <<'PY'
from pathlib import Path
import struct,sys,zlib
root=Path(sys.argv[1])
ranges=((0,2,10,2),(2,1,12,7))
(root/"material.p3mt").write_bytes(
    struct.pack("<4sHH",b"P3MT",1,len(ranges))+
    b"".join(struct.pack("<4H",*row) for row in ranges))
tx=((2,8,8,1),(7,8,8,1),(8,8,8,1))
(root/"textures.p3tx").write_bytes(
    struct.pack("<4sHH",b"P3TX",1,len(tx))+
    b"".join(struct.pack("<4H",*row) for row in tx))
source=((0,2,10,2,65535,0x0c02),(2,1,12,7,65535,0x0c02))
body=b"".join(struct.pack("<6H",*row) for row in source)
(root/"original.p3mr").write_bytes(
    struct.pack("<4s4HI",b"P3MR",1,25,3,len(source),zlib.crc32(body))+body)
shaders=[]
for i in range(13):
    if i==10:shaders.append((i,0,2,65535,1))   # original CF_COLORMAP
    elif i==12:shaders.append((i,1,7,65535,1))
    else:shaders.append((i,0,65535,65535,0))
payload=b"".join(struct.pack("<5H",*row) for row in shaders)
good=struct.pack("<4s4HI",b"P3SC",2,25,len(shaders),0,zlib.crc32(payload))+payload
legacy=struct.pack("<4s4HI",b"P3SC",1,25,len(shaders),0,zlib.crc32(payload))+payload
(root/"legacy_v1.p3sc").write_bytes(legacy)
unknown=bytearray(good)
struct.pack_into("<H",unknown,16+10*10+8,0x8000)
struct.pack_into("<I",unknown,12,zlib.crc32(unknown[16:]))
(root/"unknown_cap.p3sc").write_bytes(unknown)
(root/"original.p3sc").write_bytes(good)
bad=bytearray(good)
bad[-1]^=1
(root/"badcrc.p3sc").write_bytes(bad)
(root/"truncated.p3sc").write_bytes(good[:-1])
(root/"extra.p3sc").write_bytes(good+b'\0')
# C113 private P3SW v1: preserve all thirteen raw C5 dwords per material.
material_words=[]
for i in range(13):
    shader=0 if i!=12 else 1
    references=0xffffffff
    if i==10:references=(65535<<16)|2
    elif i==12:references=(65535<<16)|7
    material_words.append((shader,references,*([0]*6),52,0,0,0,0))
word_bytes=b"".join(struct.pack("<13I",*row) for row in material_words)
p3sw=struct.pack("<4s4HI",b"P3SW",1,25,13,0,zlib.crc32(word_bytes))+word_bytes
(root/"original.p3sw").write_bytes(p3sw)
badwords=bytearray(p3sw);badwords[-1]^=1
(root/"badcrc.p3sw").write_bytes(badwords)
(root/"truncated.p3sw").write_bytes(p3sw[:-1])
(root/"wrongmodel.p3sw").write_bytes(
    p3sw[:6]+struct.pack("<H",26)+p3sw[8:])
# A valid CRC does not prove the correct original 3DS texture references.
wrong_refs=bytearray(p3sw)
struct.pack_into("<I",wrong_refs,16+10*52+4,(65535<<16)|8)
struct.pack_into("<I",wrong_refs,12,zlib.crc32(wrong_refs[16:]))
(root/"mismatch.p3sw").write_bytes(wrong_refs)

PY
cc -std=c11 -O2 -Wall -Wextra -Werror -Isource \
   source/model_materials.c source/model_textures.c \
   source/model_material_texture.c source/source_material_map.c \
   source/source_material_texture_match.c source/source_shader_caps.c \
   source/source_material_words.c \
   tests/test_c110_shader_caps.c -o "$tmp/c110"
"$tmp/c110" "$tmp/material.p3mt" "$tmp/textures.p3tx" \
  "$tmp/original.p3mr" "$tmp/original.p3sc" \
  "$tmp/badcrc.p3sc" "$tmp/truncated.p3sc" "$tmp/extra.p3sc" \
  "$tmp/legacy_v1.p3sc" "$tmp/unknown_cap.p3sc" \
  "$tmp/original.p3sw" "$tmp/badcrc.p3sw" \
  "$tmp/truncated.p3sw" "$tmp/wrongmodel.p3sw" "$tmp/mismatch.p3sw"
