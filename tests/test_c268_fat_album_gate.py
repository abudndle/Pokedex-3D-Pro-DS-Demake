import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from c268_fat_album_gate import check


class AlbumFatGate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'Pokedex 3D Pro' / 'Photos'
        self.folder.mkdir(parents=True)
        for i in range(1, 10):
            (self.folder / f'AR_{i:04d}.png').write_bytes(b'fixture')
        self.all = tuple(f'AR_{i:04d}.png' for i in range(1, 10))

    def test_nine_photos(self):
        result = check(self.root, self.all)
        self.assertEqual(result['photos'], 9)
        self.assertEqual(result['newest'], 'AR_0009.png')
        self.assertFalse(result['emulator_ui_verified'])

    def test_deleted_newest(self):
        (self.folder / 'AR_0009.png').unlink()
        self.assertEqual(check(self.root, self.all[:-1])['photos'], 8)

    def test_missing_photo(self):
        (self.folder / 'AR_0005.png').unlink()
        with self.assertRaises(ValueError): check(self.root, self.all)

    def test_unexpected_photo(self):
        (self.folder / 'AR_0010.png').write_bytes(b'fixture')
        with self.assertRaises(ValueError): check(self.root, self.all)

    def test_malformed_photo_name(self):
        (self.folder / 'AR_00A1.png').write_bytes(b'fixture')
        with self.assertRaises(ValueError): check(self.root, self.all)

    def test_photo_directory(self):
        (self.folder / 'AR_0003.png').unlink()
        (self.folder / 'AR_0003.png').mkdir()
        with self.assertRaises(ValueError): check(self.root, self.all)

    def test_symlinked_photo(self):
        (self.folder / 'AR_0002.png').unlink()
        (self.folder / 'AR_0002.png').symlink_to(self.folder / 'AR_0001.png')
        with self.assertRaises(ValueError): check(self.root, self.all)

    def test_symlinked_folder(self):
        import shutil
        shutil.rmtree(self.folder)
        self.folder.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError): check(self.root, self.all)

    def test_symlinked_parent(self):
        import shutil
        parent = self.folder.parent
        shutil.move(str(parent), str(self.root / 'real_parent'))
        parent.symlink_to(self.root / 'real_parent', target_is_directory=True)
        with self.assertRaises(ValueError): check(self.root, self.all)

    def test_symlinked_export_root(self):
        import shutil
        real = self.root.parent / (self.root.name + '_real')
        shutil.move(str(self.root), str(real))
        self.root.symlink_to(real, target_is_directory=True)
        self.addCleanup(lambda: (self.root.unlink(missing_ok=True), shutil.move(str(real), str(self.root))))
        with self.assertRaises(ValueError): check(self.root, self.all)

    def test_irrelevant_files_ignored(self):
        (self.folder / 'README.txt').write_text('synthetic')
        self.assertEqual(check(self.root, self.all)['photos'], 9)


if __name__ == '__main__':
    unittest.main()
