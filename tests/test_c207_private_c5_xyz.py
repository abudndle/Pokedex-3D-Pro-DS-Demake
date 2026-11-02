"""Asset-free synthetic regression tests for uniquely matched private C5 XYZ."""
import importlib.util
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('c207', ROOT/'tools/c207_private_c5_xyz.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture(vertices, duplicate=False, stride=28):
    descriptors = 2 if duplicate else 1
    a = 0x78
    b = a+20*descriptors
    c = b
    data = bytearray(c)
    data[:2] = b'\xc5\x78'
    struct.pack_into('<HH', data, 0x14, descriptors, 0)
    struct.pack_into('<3I', data, 0x3c, a, b, c)
    for i in range(descriptors):
        off = len(data)
        struct.pack_into('<5I', data, a+20*i, off, 0, len(vertices)|(stride<<16), 0, 0)
        for v in vertices:
            data.extend(struct.pack('<3f', *v)+bytes(stride-12))
    return bytes(data)


def obj(vertices):
    return ('\n'.join('v %s %s %s' % v for v in vertices)+'\n').encode()


class SourceXyzTest(unittest.TestCase):
    def setUp(self):
        self.v = [(0.25, 0.0, -0.5), (1.0, 2.0, 3.0), (-1.0, 0.5, 1.0)]

    def test_exact_unique_source_and_native_crc(self):
        descriptor, p3vx = mod.convert(fixture(self.v), obj(self.v), 14)
        self.assertEqual(descriptor, [(0, 0)])
        self.assertEqual(struct.unpack_from('<4sHHHH', p3vx), (b'P3VX', 1, 14, 1, 0))
        self.assertEqual(struct.unpack_from('<HHI', p3vx, 16), (0, 3, 0))
        self.assertEqual(struct.unpack_from('<I', p3vx, 12)[0], zlib.crc32(p3vx[16:]) & 0xffffffff)
        self.assertEqual(struct.unpack_from('<9h', p3vx, 24),
                         (1024, 0, -2048, 4096, 8192, 12288, -4096, 2048, 4096))

    def test_native_c_decoder_accepts_output_and_rejects_bad_crc(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory)/'c207-probe'
            source = Path(directory)/'p014.p3vx'
            subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                            '-Isource', 'source/verified_vertex_stream.c',
                            'tests/c207_native_vertex_probe.c', '-o', str(executable)],
                           cwd=ROOT, check=True, capture_output=True, timeout=60)
            source.write_bytes(mod.convert(fixture(self.v), obj(self.v), 14)[1])
            self.assertEqual(subprocess.run([str(executable), str(source)],
                                            check=False, timeout=15).returncode, 0)
            damaged = bytearray(source.read_bytes())
            damaged[-1] ^= 1
            source.write_bytes(damaged)
            self.assertNotEqual(subprocess.run([str(executable), str(source)],
                                               check=False, timeout=15).returncode, 0)

    def test_mismatch_rejected(self):
        different = [(0.3, 0, -0.5)] + self.v[1:]
        with self.assertRaisesRegex(ValueError, 'no independently'):
            mod.convert(fixture(self.v), obj(different), 14)

    def test_ambiguous_descriptors_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unique'):
            mod.convert(fixture(self.v, duplicate=True), obj(self.v), 14)

    def test_non_28_stride_not_assumed(self):
        with self.assertRaisesRegex(ValueError, 'unique'):
            mod.convert(fixture(self.v, stride=32), obj(self.v), 14)

    def test_partial_source_mesh_and_nonzero_xyz_offset(self):
        data = bytearray(fixture(self.v, duplicate=True))
        first = struct.unpack_from('<I', data, 0x78)[0]
        second = struct.unpack_from('<I', data, 0x78 + 20)[0]
        for j, row in enumerate(self.v):
            data[first+j*28:first+(j+1)*28] = b'\xff'*8 + struct.pack('<3f', *row) + b'\xff'*8
            other = tuple(v+0.75 for v in row)
            data[second+j*28:second+(j+1)*28] = b'\xff'*8 + struct.pack('<3f', *other) + b'\xff'*8
        matched, output = mod.convert(bytes(data), obj(self.v), 14)
        self.assertEqual(matched, [(0, 8)])
        self.assertEqual(struct.unpack_from('<HHI', output, 16), (0, 3, 0))
        self.assertEqual(struct.unpack_from('<9h', output, 24),
                         (1024, 0, -2048, 4096, 8192, 12288, -4096, 2048, 4096))

    def test_ds_coordinate_overflow_rejected(self):
        v = [(9.0, 0, 0)] + self.v[1:]
        with self.assertRaisesRegex(ValueError, 'outside DS'):
            mod.convert(fixture(v), obj(v), 14)

    def test_nan_obj_rejected(self):
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            mod.convert(fixture(self.v), b'v nan 0 0\nv 1 2 3\nv 0 0 0\n', 14)

    def test_model_roster_hole_rejected(self):
        with self.assertRaisesRegex(ValueError, 'model ID'):
            mod.convert(fixture(self.v), obj(self.v), 721)

    def test_invalid_descriptor_bounds_rejected(self):
        data = bytearray(fixture(self.v))
        struct.pack_into('<I', data, 0x3c, 0xfffffff0)
        with self.assertRaisesRegex(ValueError, 'descriptor bounds'):
            mod.convert(bytes(data), obj(self.v), 14)

    def test_private_repo_path_guard(self):
        with self.assertRaisesRegex(ValueError, 'outside public repository'):
            mod.private_path(ROOT/'nitrofs'/'p014.p3vx')

    def test_symlink_input_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory)/'p014.c5'
            original.write_bytes(fixture(self.v))
            link = Path(directory)/'link.c5'
            link.symlink_to(original)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                mod.read_bounded(link)


if __name__ == '__main__':
    unittest.main()
