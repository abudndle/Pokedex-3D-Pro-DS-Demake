import pathlib
import json
import struct
import zlib
import subprocess
import sys
import tempfile

with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    source = root / "private"
    source.mkdir()
    (source / "home.rgba").write_bytes(bytes((255, 0, 0, 255)) * (256 * 192))
    (source / "dex.rgb555").write_bytes(b"\x1f\x80" * (256 * 192))
    (source / "records.rgb555").write_bytes(b"\x00\x00" * (256 * 192))
    top = source / "top"
    top.mkdir()
    # Title art is separately recovered from the 3DS boot scene.
    (source / "title.rgba").write_bytes(
        bytes((255, 255, 0, 255)) * (256 * 192))
    (top / "title.rgba").write_bytes(
        bytes((0, 255, 255, 255)) * (256 * 192))
    (source / "title_timeline.json").write_text(
        json.dumps({"loop":False,"frames":[{"ticks":2},{"ticks":3}]}))
    low_frames=source/"title_frames"/"bottom"
    high_frames=source/"title_frames"/"top"
    low_frames.mkdir(parents=True)
    high_frames.mkdir(parents=True)
    (low_frames/"01.rgb555").write_bytes(b"\x21\x4b"*(256*192))
    (high_frames/"01.rgb555").write_bytes(b"\xab\x54"*(256*192))
    (top / "home.rgba").write_bytes(bytes((0, 0, 255, 255)) * (256 * 192))
    (top / "records.rgb555").write_bytes(b"\x00\x02" * (256 * 192))
    # Explicit original-art alpha: one visible UI pixel, remaining cutout.
    (top / "dex_overlay.rgba").write_bytes(
        bytes((255, 0, 0, 255)) + bytes((0, 0, 0, 0)) * (256 * 192 - 1))
    dst = root / "nitrofs/ui/pages"
    result = subprocess.run(
        [sys.executable, "tools/package_private_ui.py", str(source), "--output", str(dst)],
        capture_output=True, text=True, check=True)
    home = (dst / "t0_00_home.rgb555").read_bytes()
    dex = (dst / "t0_01_dex.rgb555").read_bytes()
    assert len(home) == len(dex) == 256 * 192 * 2
    assert home[:2] == b"\x1f\x80"
    assert dex[:2] == b"\x1f\x80"
    records = (dst / "t0_10_records.rgb555").read_bytes()
    assert len(records) == 256 * 192 * 2
    assert records[:2] == b"\x00\x00"
    upper_home = (dst / "t1_00_home.rgb555").read_bytes()
    upper_records = (dst / "t1_10_records.rgb555").read_bytes()
    assert len(upper_home) == len(upper_records) == 256 * 192 * 2
    assert upper_home[:2] == b"\x00\xfc"  # blue, opaque A1 RGB555
    assert upper_records[:2] == b"\x00\x02"
    title_low = (dst.parent / "title/t0_title.rgb555").read_bytes()
    title_high = (dst.parent / "title/t1_title.rgb555").read_bytes()
    assert len(title_low) == len(title_high) == 256 * 192 * 2
    assert title_low[:2] == b"\xff\x83"  # yellow A1RGB555
    assert title_high[:2] == b"\xe0\xff"  # cyan A1RGB555
    assert title_low != home and title_high != upper_home
    assert (dst.parent/"title/t0_01_title.rgb555").read_bytes()[:2] == b"\x21\x4b"
    assert (dst.parent/"title/t1_01_title.rgb555").read_bytes()[:2] == b"\xab\x54"
    timeline=(dst.parent/"title/timeline.p3tl").read_bytes()
    assert struct.unpack_from("<4s4HI",timeline)[:5]==(b"P3TL",1,2,0,0)
    assert struct.unpack_from("<4H",timeline,16)==(0,2,1,3)
    assert zlib.crc32(timeline[16:]) == struct.unpack_from("<I",timeline,12)[0]
    overlay = (dst / "t1_01_dex_overlay.rgb555").read_bytes()
    assert len(overlay) == 256 * 192 * 2
    assert overlay[:4] == b"\x1f\x80\x00\x00"
    assert "Prepared 10 private UI images" in result.stdout
    # Never accept an opaque original UI page as a fake transparent HUD.
    (top / "records_overlay.rgb555").write_bytes(b"\x34\x92" * (256 * 192))
    invalid = subprocess.run(
        [sys.executable, "tools/package_private_ui.py", str(source),
         "--output", str(root / "invalid")],
        capture_output=True, text=True)
    assert invalid.returncode != 0
    assert "original overlay requires opaque UI and transparent 3D cutout" in invalid.stderr
    # Removing only one original 3DS title source must be rejected even
    # when full HOME pages are available. Never substitute HOME for TITLE.
    (top / "records_overlay.rgb555").unlink()
    (top / "title.rgba").unlink()
    partial = subprocess.run(
        [sys.executable, "tools/package_private_ui.py", str(source),
         "--output", str(root / "partial" / "pages")],
        capture_output=True, text=True)
    assert partial.returncode != 0
    assert "needs both independent top and bottom" in partial.stderr
    # Malformed source timing is not silently replaced by a guessed 60 Hz loop.
    (top/"title.rgba").write_bytes(bytes((0,255,255,255))*(256*192))
    (source/"title_timeline.json").write_text(
        json.dumps({"loop":False,"frames":[{"ticks":2},{"ticks":0}]}))
    bad_timing=subprocess.run(
        [sys.executable,"tools/package_private_ui.py",str(source),
         "--output",str(root/"bad_timing"/"pages")],
        capture_output=True,text=True)
    assert bad_timing.returncode!=0
    assert "invalid source original title frame duration" in bad_timing.stderr
print("Private UI page packaging: PASS")
