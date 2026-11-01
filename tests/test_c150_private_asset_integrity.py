"""Asset-free synthetic regressions for private Pokédex source-integrity tools."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib

ROOT=Path(__file__).resolve().parents[1]
# In GitHub checkout the script resides under tools; the test under tests.
for candidate in (ROOT/'tools'/'c150_private_asset_integrity.py',ROOT/'public_source'/'c150_private_asset_integrity.py'):
    if candidate.exists():break
else:raise RuntimeError('missing C150 verifier source')
spec=importlib.util.spec_from_file_location('c150_private_asset_integrity',candidate)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PrivateIntegrityFixtures(unittest.TestCase):
    def test_zip_integrity_and_path_safety(self):
        with tempfile.TemporaryDirectory() as temp:
            good=Path(temp)/'good.zip'
            with zipfile.ZipFile(good,'w') as z:
                z.writestr('textures/p000/t000.p3px',b'P3PX'+b'\x00'*8)
            result=mod.audit_zip(good)
            self.assertEqual(result['zip_entries'],1)
            self.assertTrue(result['zip_full_crc_passed'])
            self.assertEqual(result['sha256'],hashlib.sha256(good.read_bytes()).hexdigest())
            bad=Path(temp)/'unsafe.zip'
            with zipfile.ZipFile(bad,'w') as z:z.writestr('../private/payload',b'unsafe')
            with self.assertRaisesRegex(ValueError,'unsafe'):
                mod.audit_zip(bad)
            duplicate=Path(temp)/'dupes.zip'
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                with zipfile.ZipFile(duplicate,'w') as z:
                    z.writestr('same',b'a');z.writestr('same',b'b')
            with self.assertRaisesRegex(ValueError,'duplicate'):
                mod.audit_zip(duplicate)

    def test_exact_native_skeleton_source_byte_link_and_crc(self):
        raw=bytearray(0x120)
        struct.pack_into('<I',raw,0x10,1<<16)
        struct.pack_into('<I',raw,0x38,0x78)
        struct.pack_into('<I',raw,0x3c,0x78+56)
        struct.pack_into('<I',raw,0x64,0x100)
        matrix=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.]
        node=struct.pack('<12fHHI',*matrix,65535,1,0)
        raw[0x78:0x78+56]=node
        name=b'OriginalNode\0'
        raw[0x100:0x100+len(name)]=name
        content=node+name
        p3sk=struct.pack('<4sHHHHII',b'P3SK',1,14,1,1,len(name),zlib.crc32(content))+content
        self.assertEqual(mod.read_p3sk(p3sk,14,raw),(1,1))
        with self.assertRaisesRegex(ValueError,'CRC'):
            mod.read_p3sk(p3sk[:-1]+b'X',14,raw)
        with self.assertRaisesRegex(ValueError,'header'):
            mod.read_p3sk(p3sk,15,raw)
        changed=bytearray(raw);changed[0x78]^=1
        with self.assertRaisesRegex(ValueError,'byte-exact'):
            mod.read_p3sk(p3sk,14,changed)

    def test_original_c98_p3cs_crc_and_bounds_reject_corruption(self):
        # Minimal valid C98 chunk with one triangle's 33-byte record.
        payload=b'\0'*33
        table=struct.pack('<IHHII',0,1,0,40,zlib.crc32(payload))
        blob=struct.pack('<4s4H3I',b'P3CS',1,7,1,0,1,1,zlib.crc32(table))+table+payload
        self.assertEqual(mod.inspect_p3cs(blob,7),(1,1))
        for case,modified in (
            ('wrong model',8),('truncated',None)):
            with self.assertRaisesRegex(ValueError,'P3CS'):
                mod.inspect_p3cs(blob[:-1] if modified is None else blob,modified if modified is not None else 7)
        damaged=bytearray(blob);damaged[-1]=1
        with self.assertRaisesRegex(ValueError,'CRC'):
            mod.inspect_p3cs(damaged,7)
        padded=bytearray(blob);padded.extend(b'\0')
        with self.assertRaisesRegex(ValueError,'final'):
            mod.inspect_p3cs(padded,7)

    def test_recovered_c84_contents_match_original_members_and_embedded_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'archives').mkdir();(root/'recovered').mkdir()
            source=root/'archives/C86_PRIVATE_COMBINED_NITROFS_WITH_PREVIEWS.zip'
            target=root/'recovered/C84_CONTENT_RECOVERED_FROM_C86_NOT_ORIGINAL_ARCHIVE.zip'
            ui=b'RGB-ORIGINAL-UI';move=b'ORIGINAL-MOVES'
            manifest={'original_gui_sha256':{'ui/pages/t0_00_home.rgb555':hashlib.sha256(ui).hexdigest()},
                      'moves_sha256':hashlib.sha256(move).hexdigest()}
            contents={'ui/pages/t0_00_home.rgb555':ui,'moves.p3dm':move,
                      'PRIVATE_STAGE_C84_MANIFEST.json':json.dumps(manifest).encode(),
                      'textures/p000/t000.p3px':b'pixels','preview/p000.ds3m':b'geometry',
                      'C86_STAGING_README.txt':b'new stage'}
            with zipfile.ZipFile(source,'w') as z:
                for k,v in contents.items():z.writestr(k,v)
            with zipfile.ZipFile(target,'w') as z:
                for k,v in contents.items():
                    if k not in ('preview/p000.ds3m','C86_STAGING_README.txt'):z.writestr(k,v)
            x=mod.audit_c84_content(root)
            self.assertTrue(x['verified']);self.assertEqual(x['members_compared'],4)
            self.assertFalse(x['original_C84_ZIP_recovered'])
            # A modified move payload is NOT considered original C84 content.
            with zipfile.ZipFile(target,'w') as z:
                for k,v in contents.items():
                    if k not in ('preview/p000.ds3m','C86_STAGING_README.txt'):
                        z.writestr(k,b'BAD' if k=='moves.p3dm' else v)
            with self.assertRaisesRegex(ValueError,'mismatch'):
                mod.audit_c84_content(root)

if __name__=='__main__':unittest.main()