"""Host regression for photo-album directory traversal and symlink rejection.

Uses only temporary synthetic files; no original game assets.
"""
import ctypes
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class Album(ctypes.Structure):
    _fields_ = [("folder", ctypes.c_char * 320)]


class AlbumPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory()
        so = pathlib.Path(cls.build.name) / "libalbum.so"
        subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-shared", "-fPIC", "-Isource", "source/photo_album.c",
                        "-o", str(so)], cwd=ROOT, check=True)
        cls.lib = ctypes.CDLL(str(so))
        cls.lib.p3dPhotoAlbumOpen.argtypes = [ctypes.POINTER(Album), ctypes.c_char_p]
        cls.lib.p3dPhotoAlbumOpen.restype = ctypes.c_int
        cls.lib.p3dPhotoAlbumPage.argtypes = [ctypes.POINTER(Album), ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        cls.lib.p3dPhotoAlbumPage.restype = ctypes.c_size_t
        cls.lib.p3dPhotoAlbumDelete.argtypes = [ctypes.POINTER(Album), ctypes.c_char_p]
        cls.lib.p3dPhotoAlbumDelete.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.build.cleanup()

    def open_album(self, album, path):
        return self.lib.p3dPhotoAlbumOpen(ctypes.byref(album), str(path).encode())

    def test_regular_album_and_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            folder = root / "Photos"
            album = Album()
            self.assertEqual(self.open_album(album, folder), 1)
            self.assertTrue(folder.is_dir())
            self.assertEqual(self.open_album(album, folder), 1)
            self.assertEqual(album.folder.decode(), str(folder))

    def test_traversal_fails_without_creating_or_deleting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            album = Album()
            good = root / "Photos"
            self.assertEqual(self.open_album(album, good), 1)
            for bad in (str(root) + "/../elsewhere/Photos",
                        str(root) + "/./Photos"):
                self.assertEqual(self.open_album(album, bad), 0)
                self.assertEqual(album.folder.decode(), "")
                self.assertEqual(self.lib.p3dPhotoAlbumDelete(ctypes.byref(album), b"AR_0001.png"), 0)

    def test_symlinked_parent_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            actual = root / "actual"
            actual.mkdir()
            (root / "linked").symlink_to(actual, target_is_directory=True)
            album = Album()
            self.assertEqual(self.open_album(album, root / "linked" / "Photos"), 0)
            self.assertFalse((actual / "Photos").exists())

    def test_nested_symlink_ancestor_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            actual = root / "actual"
            actual.mkdir()
            outer = root / "outer"
            outer.mkdir()
            (outer / "linked").symlink_to(actual, target_is_directory=True)
            album = Album()
            self.assertEqual(self.open_album(album, outer / "linked" / "nested" / "Photos"), 0)
            self.assertFalse((actual / "nested").exists())
            self.assertEqual(album.folder.decode(), "")

    def test_parent_replaced_with_symlink_after_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            parent = root / "safe"
            parent.mkdir()
            album = Album()
            self.assertEqual(self.open_album(album, parent / "Photos"), 1)
            (parent / "Photos" / "AR_0001.png").write_bytes(b"synthetic")
            parent.rename(root / "old")
            target = root / "target"
            (target / "Photos").mkdir(parents=True)
            photo = target / "Photos" / "AR_0001.png"
            photo.write_bytes(b"protected")
            parent.symlink_to(target, target_is_directory=True)
            count = ctypes.c_size_t(123)
            names = (ctypes.c_char * (7 * 32))()
            self.assertEqual(self.lib.p3dPhotoAlbumPage(ctypes.byref(album), names, 7, 0, ctypes.byref(count)), 0)
            self.assertEqual(count.value, 0)
            self.assertEqual(self.lib.p3dPhotoAlbumDelete(ctypes.byref(album), b"AR_0001.png"), 0)
            self.assertEqual(photo.read_bytes(), b"protected")

    def test_symlinked_album_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            actual = root / "actual"
            actual.mkdir()
            (root / "Photos").symlink_to(actual, target_is_directory=True)
            album = Album()
            self.assertEqual(self.open_album(album, root / "Photos"), 0)
            self.assertEqual(album.folder.decode(), "")


if __name__ == "__main__":
    unittest.main()
