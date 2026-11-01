import pathlib
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
    overlay = (dst / "t1_01_dex_overlay.rgb555").read_bytes()
    assert len(overlay) == 256 * 192 * 2
    assert overlay[:4] == b"\x1f\x80\x00\x00"
    assert "Prepared 6 private UI images" in result.stdout
    # Never accept an opaque original UI page as a fake transparent HUD.
    (top / "records_overlay.rgb555").write_bytes(b"\x34\x92" * (256 * 192))
    invalid = subprocess.run(
        [sys.executable, "tools/package_private_ui.py", str(source),
         "--output", str(root / "invalid")],
        capture_output=True, text=True)
    assert invalid.returncode != 0
    assert "original overlay requires opaque UI and transparent 3D cutout" in invalid.stderr
print("Private UI page packaging: PASS")
