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
    dst = root / "nitrofs/ui/pages"
    result = subprocess.run(
        [sys.executable, "tools/package_private_ui.py", str(source), "--output", str(dst)],
        capture_output=True, text=True, check=True)
    home = (dst / "t0_00_home.rgb555").read_bytes()
    dex = (dst / "t0_01_dex.rgb555").read_bytes()
    assert len(home) == len(dex) == 256 * 192 * 2
    assert home[:2] == b"\x1f\x80"
    assert dex[:2] == b"\x1f\x80"
    assert "Prepared 2/10" in result.stdout
print("Private UI page packaging: PASS")
