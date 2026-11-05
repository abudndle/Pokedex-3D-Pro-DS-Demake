#!/usr/bin/env python3
"""Exercise the ACTUAL upstream Nitro Engine obj2dl converter on SYNTHETIC data."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'tests'))
from c335_private_nitro_engine_stage import export_obj,manifest_bytes
from test_c335_nitro_converter import source_pair

def main(converter:Path):
    if not converter.is_file() or converter.name!='obj2dl.py':
        raise ValueError('actual Nitro Engine obj2dl.py is required')
    vx,ix=source_pair()
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)
        obj=folder/'synthetic-original-order.obj'
        dl=folder/'synthetic-original-order.dl'
        obj.write_text(export_obj(vx,ix,25),encoding='utf-8')
        subprocess.run([sys.executable,str(converter),
            '--input',str(obj),'--output',str(dl),'--texture','8','8'],
            check=True,capture_output=True,text=True,timeout=30)
        data=dl.read_bytes()
        manifest=manifest_bytes(vx,ix,25,data)
        assert len(data)>=8
        assert struct.unpack_from('<I',data,0)[0]==len(data)//4-1
        assert manifest[4]==1 and manifest[5]==1
        assert struct.unpack_from('<I',manifest,20)[0]==zlib.crc32(data)
    print('C335 real upstream Nitro Engine OBJ2DL conversion: PASS (synthetic original-order geometry)')
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: c335_official_nitro_tool_smoke.py /path/to/obj2dl.py')
    main(Path(sys.argv[1]))
