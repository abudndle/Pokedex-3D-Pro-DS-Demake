#!/usr/bin/env python3
"""Prepare private 3DS top and bottom UI pages for DS NitroFS; never distribute assets."""
import argparse
import json
import zlib
import wave
import pathlib
import struct
import sys

NAMES = ("home", "dex", "search", "moves", "types", "favorites", "challenge",
         "settings", "album", "ar", "records")
PIXELS = 256 * 192
SIZE = PIXELS * 2

def convert(src: pathlib.Path, dst: pathlib.Path) -> None:
    data = src.read_bytes()
    if len(data) == SIZE:
        out = data
    elif len(data) == PIXELS * 4:
        # Explicit RGBA8888 input, row-major top-to-bottom. DS bit15 enables pixels.
        values = bytearray(SIZE)
        for i in range(PIXELS):
            r, g, b, a = data[4*i:4*i+4]
            rgb = (0x8000 if a else 0) | ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3)
            struct.pack_into("<H", values, 2*i, rgb)
        out = bytes(values)
    else:
        raise ValueError(f"{src}: expected {SIZE} RGB555 or {PIXELS*4} RGBA bytes, got {len(data)}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(out)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=pathlib.Path, help="Private folder with PAGE_NAME.rgb555 or .rgba")
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("nitrofs/ui/pages"))
    args = parser.parse_args()
    count = 0
    # Legacy root files are the original bottom-screen pages. Top-screen art
    # must be provided independently; do not duplicate or fabricate pages.
    # Accept either <source>/top/<name> or <source>/top_<name> for the top.
    for screen in (0, 1):
        for page, name in enumerate(NAMES):
            for ext in (".rgb555", ".rgba"):
                candidates = (
                    (args.source / f"{name}{ext}",) if screen == 0 else
                    (args.source / "top" / f"{name}{ext}",
                     args.source / f"top_{name}{ext}")
                )
                source = next((path for path in candidates if path.is_file()), None)
                if source is not None:
                    destination = args.output / f"t{screen}_{page:02d}_{name}.rgb555"
                    convert(source, destination)
                    print(f"{source} -> {destination}")
                    count += 1
                    break
    # The original title is NOT the home menu. Require two independently
    # recovered 3DS title frames; missing either refuses to fabricate one.
    title_sources = []
    for screen in (0, 1):
        candidates = []
        for ext in (".rgb555", ".rgba"):
            if screen == 0:
                candidates.extend((args.source / f"title{ext}",
                                   args.source / "bottom" / f"title{ext}"))
            else:
                candidates.extend((args.source / "top" / f"title{ext}",
                                   args.source / f"top_title{ext}"))
        title_sources.append(next((p for p in candidates if p.is_file()), None))
    if any(title_sources):
        if not all(title_sources):
            raise ValueError("original 3DS title needs both independent top and bottom source frames")
        for screen, source in enumerate(title_sources):
            destination = args.output.parent / "title" / f"t{screen}_title.rgb555"
            convert(source, destination)
            print(f"{source} -> {destination}")
            count += 1
    # C117: only a PRIVATE source-derived title sequence may animate the
    # already recovered original frame-zero title. This is explicitly
    # provided source timing, never guessed from the DS refresh rate.
    timing = args.source / "title_timeline.json"
    if timing.is_file():
        if not all(title_sources):
            raise ValueError("original 3DS title timeline requires both frame-zero screens")
        manifest = json.loads(timing.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or set(manifest) != {"loop", "frames"}:
            raise ValueError("invalid private 3DS title timing schema")
        if type(manifest["loop"]) is not bool or not isinstance(manifest["frames"], list):
            raise ValueError("invalid original title looping or frame sequence")
        frames = manifest["frames"]
        if not 2 <= len(frames) <= 16:
            raise ValueError("original title animation requires 2..16 frames")
        durations = []
        selected = []
        for i,frame in enumerate(frames):
            if not isinstance(frame,dict) or set(frame)!={"ticks"} or (
                type(frame["ticks"]) is not int or not 1 <= frame["ticks"] <= 3600):
                raise ValueError("invalid source original title frame duration")
            durations.append(frame["ticks"])
            if i==0:continue
            pair=[]
            for screen,subfolder in ((0,"bottom"),(1,"top")):
                options=[args.source/"title_frames"/subfolder/f"{i:02d}{ext}"
                         for ext in (".rgb555",".rgba")]
                found=next((p for p in options if p.is_file()),None)
                if found is None or found.stat().st_size not in (SIZE,PIXELS*4):
                    raise ValueError(f"original 3DS title frame {i} lacks source {subfolder} art")
                pair.append(found)
            selected.append((i,pair))
        title_output = args.output.parent / "title"
        for frame_id,pair in selected:
            for screen,source in enumerate(pair):
                destination=title_output / f"t{screen}_{frame_id:02d}_title.rgb555"
                convert(source,destination)
                count+=1
                print(f"{source} -> {destination}")
        records=b"".join(struct.pack("<HH",i,ticks)
                         for i,ticks in enumerate(durations))
        timeline=struct.pack("<4s4HI",b"P3TL",1,len(frames),
                             int(manifest["loop"]),0,zlib.crc32(records))+records
        (title_output/"timeline.p3tl").write_bytes(timeline)
        print(f"{timing} -> {title_output/'timeline.p3tl'}")
    # Original title sound effects are private short PCM16 mono cues recovered
    # from the owner's 3DS audio. No generic jingle or invented sound is used.
    cues_json=args.source/"title_cues.json"
    if cues_json.is_file():
        if not all(title_sources):
            raise ValueError("source title audio requires both original title screens")
        meta=json.loads(cues_json.read_text(encoding="utf-8"))
        if not isinstance(meta,dict) or set(meta)!={"events"} or (
            not isinstance(meta["events"],list)):
            raise ValueError("invalid source title audio cue schema")
        frame_total=len(frames) if timing.is_file() else 1
        events=meta["events"]
        if not 1<=len(events)<=frame_total:
            raise ValueError("invalid original title cue count")
        last=-1
        resources={}
        records=bytearray()
        for item in events:
            if (not isinstance(item,dict) or set(item)!={"frame","cue"}
                or type(item["frame"]) is not int
                or type(item["cue"]) is not int):
                raise ValueError("invalid original title audio event")
            frame,cue=item["frame"],item["cue"]
            if not last<frame<frame_total or not 1<=cue<=16:
                raise ValueError("invalid source title cue order or number")
            last=frame
            records.extend(struct.pack("<HH",frame,cue))
            if cue in resources:continue
            original=args.source/"title_audio"/f"c{cue:02d}.wav"
            try:
                with wave.open(str(original),"rb") as wav:
                    if (wav.getnchannels()!=1 or wav.getsampwidth()!=2 or
                        wav.getcomptype()!="NONE" or
                        not 8000<=wav.getframerate()<=32000 or
                        not 1<=wav.getnframes()<=16384):
                        raise ValueError("invalid source title PCM16 WAV layout/rate/length")
                    rate=wav.getframerate()
                    nsamples=wav.getnframes()
                    pcm=wav.readframes(nsamples)
            except (FileNotFoundError,wave.Error,EOFError) as exc:
                raise ValueError(f"missing/malformed source title cue {cue}: {exc}") from exc
            if len(pcm)!=nsamples*2:
                raise ValueError("truncated source title PCM16 audio")
            resources[cue]=struct.pack("<4sHHII",b"P3SA",1,rate,
                    nsamples,zlib.crc32(pcm))+pcm
        cue_dir=args.output.parent/"title"
        cue_dir.mkdir(parents=True,exist_ok=True)
        for cue,blob in sorted(resources.items()):
            dst=cue_dir/"audio"/f"c{cue:02d}.p3sa"
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(blob)
            print(f"private source title WAV -> {dst}")
            count+=1
        sequence=struct.pack("<4s4HI",b"P3TC",1,frame_total,
                    len(events),0,zlib.crc32(records))+records
        (cue_dir/"cues.p3tc").write_bytes(sequence)
        print(f"{cues_json} -> {cue_dir/'cues.p3tc'}")
    # An original masked HUD is distinct from the full upper Dex page.
    # Preserve the source alpha bit: clear pixels reveal native BG0 3D.
    # Do not fabricate transparency by guessing at original artwork.
    for page, name in enumerate(NAMES):
        for ext in (".rgb555", ".rgba"):
            candidates = (args.source / "top" / f"{name}_overlay{ext}",
                          args.source / f"top_{name}_overlay{ext}")
            source = next((path for path in candidates if path.is_file()), None)
            if source is None:
                continue
            destination = args.output / f"t1_{page:02d}_{name}_overlay.rgb555"
            data = source.read_bytes()
            if len(data) == SIZE:
                values = data
            elif len(data) == PIXELS * 4:
                values = bytearray(SIZE)
                for i in range(PIXELS):
                    r, g, b, a = data[4*i:4*i+4]
                    pixel = (0x8000 if a else 0) | ((b>>3)<<10) | ((g>>3)<<5) | (r>>3)
                    struct.pack_into("<H",values,i*2,pixel)
            else:
                raise ValueError(f"{source}: invalid transparent UI overlay size")
            # Both an opaque original HUD region and a transparent model
            # viewport are required; this is a binary A1 mask, not ARGB.
            visible = any(values[j+1]&0x80 for j in range(0,SIZE,2))
            cutout = any(not(values[j+1]&0x80) for j in range(0,SIZE,2))
            if not (visible and cutout):
                raise ValueError(f"{source}: original overlay requires opaque UI and transparent 3D cutout")
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(values)
            print(f"{source} -> {destination}")
            count += 1
            break
    if not count:
        print("No original UI/title pages supplied; development ROM will use text fallback.", file=sys.stderr)
        return 1
    print(f"Prepared {count} private UI images ({2*len(NAMES)} independent full-screen pages plus optional source masks).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
