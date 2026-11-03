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
            for bad in (str(root / ".." / "elsewhere" / "Photos"),
                        str(root / "." / "Photos")):
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
