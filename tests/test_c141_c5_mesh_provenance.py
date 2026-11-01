"""C141 synthetic private C56 -> native DS3M source mesh provenance tests."""
import csv
import hashlib
import io
import pathlib
import struct
import sys
import tempfile
import unittest
import zipfile

TOOLS = pathlib.Path(__file__).resolve().parents[1] / "tools"
if not TOOLS.is_dir():
    TOOLS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from c141_c5_mesh_provenance import (
    PART_RANGES, ROSTER, audit, preview_header, repair_preview_source_counts,
)


def c5(triangles=1, flag=0):
    blob = bytearray(0xb0)
    blob[:2] = b"\xc5\x78"
    struct.pack_into("<H", blob, 0x14, 1)
    struct.pack_into("<H", blob, 0x16, 1)
    for off, value in ((0x3c,0x78),(0x40,0x8c),(0x44,0x98),
                       (0x48,0x98),(0x4c,0x98)):
        struct.pack_into("<I", blob, off, value)
    struct.pack_into("<5I", blob, 0x78, 0x98, 0,
                     (4 << 16) | 1, 0, flag)
    struct.pack_into("<3I", blob, 0x8c, 0x9c, 0,
                     (2 << 16) | (triangles * 3))
    return bytes(blob)


def preview(source_count=1):
    return struct.pack("<4sHHII",b"DS3M",2,1,0,source_count) + \
        struct.pack("<9h",*(range(9))) + bytes([31,53,97])


def make_fixture(root):
    rows, archives = [], []
    preview_zip=root/'private.zip'
    with zipfile.ZipFile(preview_zip,'w') as out:
        for model in sorted(ROSTER):
            out.writestr(f'preview/p{model:03d}.ds3m',
                         preview(1))
        out.writestr('notes/test.txt',b'no original assets in synthetic fixture')
    for part_id,(first,last) in enumerate(PART_RANGES):
        path=root/f'c56part{part_id}.zip'
        with zipfile.ZipFile(path,'w') as out:
            for model in range(first,last+1):
                if model not in ROSTER:continue
                source=c5(triangles=2 if model==561 else 1,
                          flag=0x26 if model==76 else 0)
                label=f'p{model:03d}'
                out.writestr(f'decoded_c5/{label}.c5',source)
                rows.append({'model':label,'sha256':hashlib.sha256(source).hexdigest(),
                             'decoded_bytes':str(len(source)),
                             'status':'valid_with_0x26_flag_warning' if model==76 else 'strict_valid',
                             '0x26_descriptor_flags':'1' if model==76 else '0',
                             'primary_descriptor_count':'1'})
        archives.append(path)
    bundle=root/'decoder.zip'
    output=io.StringIO()
    writer=csv.DictWriter(output,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
    with zipfile.ZipFile(bundle,'w') as z:
        z.writestr('C56_validation.csv',output.getvalue())
    return archives,bundle,preview_zip


class C141Tests(unittest.TestCase):
    def test_exact_730_original_mesh_groups_detect_one_metadata_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            parts,bundle,pack=make_fixture(pathlib.Path(d))
            r=audit(parts,bundle,pack)
            self.assertEqual(r['original_c56_models_verified'],730)
            self.assertEqual(r['source_mesh_groups_total'],730)
            self.assertEqual(r['source_face_count_matches'],729)
            self.assertEqual([m['model'] for m in r['source_face_count_mismatches']],['p561'])
            self.assertEqual(r['models']['p561']['source_triangle_count'],2)
            self.assertEqual(r['models']['p076']['c56_status'],'valid_with_0x26_flag_warning')
            self.assertEqual(r['original_face_to_material_indices_verified'],0)
            self.assertEqual(r['certified_original_textured_models'],0)

    def test_private_repair_changes_only_4byte_header_and_preserves_assets(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            parts,bundle,pack=make_fixture(root)
            report=audit(parts,bundle,pack)
            dest=root/'corrected.zip'
            meta=repair_preview_source_counts(pack,dest,report,['p561'])
            self.assertEqual(meta['repaired_source_triangle_metadata'],['p561'])
            with zipfile.ZipFile(pack) as old,zipfile.ZipFile(dest) as new:
                self.assertEqual(old.namelist(),new.namelist())
                for name in old.namelist():
                    raw,corrected=old.read(name),new.read(name)
                    if name=='preview/p561.ds3m':
                        self.assertEqual(corrected[:12]+corrected[16:],raw[:12]+raw[16:])
                        self.assertEqual(preview_header(corrected),(1,2))
                    else:self.assertEqual(raw,corrected)
            self.assertEqual(audit(parts,bundle,dest)['source_face_count_matches'],730)
            with self.assertRaisesRegex(ValueError,'overwrite'):
                repair_preview_source_counts(pack,dest,report,['p561'])

    def test_fail_closed_on_unexpected_mismatch_and_corrupt_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            parts,bundle,pack=make_fixture(root)
            r=audit(parts,bundle,pack)
            with self.assertRaisesRegex(ValueError,'unexpected source count'):
                repair_preview_source_counts(pack,root/'nope.zip',r,['p560'])
            with self.assertRaisesRegex(ValueError,'displaced'):
                audit(parts[::-1],bundle,pack)
            with zipfile.ZipFile(parts[0]) as z:
                entries={name:z.read(name) for name in z.namelist()}
            entries['decoded_c5/p000.c5']+=b'X'
            with zipfile.ZipFile(parts[0],'w') as z:
                for name,data in entries.items():z.writestr(name,data)
            with self.assertRaisesRegex(ValueError,'hash/size mismatch'):
                audit(parts,bundle,pack)

    def test_bad_native_preview_format_not_classified_as_material(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            parts,bundle,pack=make_fixture(root)
            with zipfile.ZipFile(pack) as z:
                entries={name:z.read(name) for name in z.namelist()}
            bad=bytearray(entries['preview/p010.ds3m']);bad[8]=1
            entries['preview/p010.ds3m']=bytes(bad)
            with zipfile.ZipFile(pack,'w') as z:
                for name,data in entries.items():z.writestr(name,data)
            with self.assertRaisesRegex(ValueError,'native DS3M'):
                audit(parts,bundle,pack)


if __name__=='__main__':unittest.main()