"""C250 synthetic end-to-end host test: P3SM -> actual C native P3VX/P3IX loader."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
from c249_private_geometry_nitrofs import stage
from test_c249_private_geometry_nitrofs import fixture

SOURCES = [
    'source/species_model_map.c',
    'source/verified_vertex_stream.c',
    'source/verified_primitive_stream.c',
    'source/verified_primitive_bridge.c',
    'source/verified_geometry_pair.c',
    'tests/c250_native_species_geometry_probe.c',
]


class C250NativeSpeciesGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='c250-native-')
        cls.probe = Path(cls.temp.name) / 'c250-probe'
        command = [os.environ.get('CC', 'cc'), '-std=c11', '-Wall', '-Wextra',
                   '-Werror', '-O2', '-Isource', *SOURCES, '-o', str(cls.probe)]
        subprocess.run(command, cwd=ROOT, check=True, capture_output=True, timeout=90)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setup_stage(self, root):
        source, mapping, dest = fixture(root)
        stage(source, mapping, dest)
        return dest

    def invoke(self, dest, species, model, triangles):
        return subprocess.run([str(self.probe), str(dest), str(species),
                               str(model), str(triangles)],
                              capture_output=True, text=True, timeout=15)

    def test_native_c_resolves_two_diagnostic_species_and_missing_slot(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = self.setup_stage(Path(tmp))
            for species, model, triangles in ((1, 2, 1), (649, 3, 1), (2, -1, 0)):
                with self.subTest(species=species):
                    result = self.invoke(dest, species, model, triangles)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('PASS', result.stdout)

    def test_wrong_species_resource_binding_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = self.setup_stage(Path(tmp))
            self.assertNotEqual(self.invoke(dest, 1, 3, 1).returncode, 0)

    def test_corrupt_native_geometry_fails_after_mapping_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = self.setup_stage(Path(tmp))
            path = dest / 'geometry/p002.p3vx'
            data = bytearray(path.read_bytes())
            data[-1] ^= 1
            path.write_bytes(data)
            self.assertNotEqual(self.invoke(dest, 1, 2, 1).returncode, 0)

    def test_corrupt_private_p3sm_fails_before_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = self.setup_stage(Path(tmp))
            path = dest / 'models/species_map.p3sm'
            data = bytearray(path.read_bytes())
            data[0] ^= 1
            path.write_bytes(data)
            self.assertNotEqual(self.invoke(dest, 1, 2, 1).returncode, 0)

    def test_missing_private_geometry_fails_after_mapping_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = self.setup_stage(Path(tmp))
            (dest / 'geometry/p003.p3ix').unlink()
            self.assertNotEqual(self.invoke(dest, 649, 3, 1).returncode, 0)


if __name__ == '__main__':
    unittest.main()
