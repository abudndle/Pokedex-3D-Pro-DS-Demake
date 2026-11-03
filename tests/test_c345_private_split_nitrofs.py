"""C345: synthetic-only private split ZIP security regression tests."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c345_private_split_nitrofs import reconstruct, safe_file, check_zip, ARCHIVES


class C345Tests(unittest.TestCase):
    def test_unsafe_zip_member_paths(self):
        for name in ('../escape','/absolute','x/../outside','a\\b','x//y'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as d:
                path=Path(d)/'archive.zip'
                with zipfile.ZipFile(path,'w') as z:
                    z.writestr(name,b'fixture')
                with self.assertRaises(ValueError): check_zip(path)

    def test_duplicate_zip_member(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'archive.zip'
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                with zipfile.ZipFile(path,'w') as z:
                    z.writestr('same',b'a')
                    z.writestr('same',b'b')
            with self.assertRaises(ValueError): check_zip(path)

    def test_missing_or_corrupt_part_is_atomic(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); parts=root/'parts';parts.mkdir()
            records=[]
            for name in ARCHIVES:
                pn=name+'.part001'
                records.append({'filename':name,'size':1,'sha256':'a'*64,
                                'parts':[{'name':pn,'size':1,'sha256':'b'*64}]})
                (parts/pn).write_bytes(b'x')
            (parts/'manifest.json').write_text(json.dumps({'files':records}))
            output=root/'output'
            with self.assertRaisesRegex(ValueError,'SHA256'):reconstruct(parts,output)
            self.assertFalse(output.exists())

    def test_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); parts=root/'parts';parts.mkdir()
            output=root/'output';output.mkdir()
            (output/'sentinel').write_text('unchanged')
            with self.assertRaises(ValueError):reconstruct(parts,output)
            self.assertEqual((output/'sentinel').read_text(),'unchanged')

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);actual=root/'actual';actual.write_bytes(b'x')
            link=root/'part';link.symlink_to(actual)
            with self.assertRaises(ValueError):safe_file(link,100)


if __name__=='__main__':
    unittest.main()
