"""C346: synthetic-only tests of GUI Z5/C5 byte-equivalence gate."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import c346_gui_z5_equivalence as target


class C346EquivalenceTests(unittest.TestCase):
    def inputs(self, folder, raw=b'\x40fixture', decoded=b'\xc5\x78\x00\x01fixture'):
        archive = Path(folder) / 'private-test.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('romfs/gui/gui_title.z5', raw)
            z.writestr('decoded_c5/gui/gui_title.c5', decoded)
        report = {'source_archive_sha256': 'a'*64, 'resources': [
            {'original': 'romfs/gui/gui_title.z5',
             'decoded': 'decoded_c5/gui/gui_title.c5',
             'decoded_sha256': hashlib.sha256(decoded).hexdigest()}]}
        return archive, report

    def test_exact_equivalence_and_unwrapped_offset(self):
        with tempfile.TemporaryDirectory() as root:
            archive, report = self.inputs(root)
            with patch.object(target, 'inventory', return_value=report), \
                 patch.object(target, 'decode_stream', return_value=b'\xc5\x78\x00\x01fixture') as decoder:
                result = target.verify(archive)
            decoder.assert_called_once_with(b'\x40fixture', max_output=target.MAX_C5)
            self.assertEqual(result['original_gui_pairs_verified'], 1)
            self.assertEqual(result['gui_z5_stream_offset'], 0)
            self.assertFalse(result['original_game_release_ready'])
            self.assertFalse(result['original_ui_texture_conversion_complete'])

    def test_mismatched_decoded_output_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            archive, report = self.inputs(root)
            with patch.object(target, 'inventory', return_value=report), \
                 patch.object(target, 'decode_stream', return_value=b'not correct'):
                with self.assertRaisesRegex(ValueError, 'byte mismatch'):
                    target.verify(archive)

    def test_model_header_cannot_masquerade_as_gui_stream(self):
        with tempfile.TemporaryDirectory() as root:
            archive, report = self.inputs(root, raw=b'Z5HEADER'+b'\x40hello')
            with patch.object(target, 'inventory', return_value=report):
                with self.assertRaisesRegex(ValueError, '0x40 tag'):
                    target.verify(archive)

    def test_decoder_error_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            archive, report = self.inputs(root)
            with patch.object(target, 'inventory', return_value=report), \
                 patch.object(target, 'decode_stream', side_effect=target.DecodeError('bad')):
                with self.assertRaisesRegex(ValueError, 'decompression failed'):
                    target.verify(archive)


if __name__ == '__main__':
    unittest.main()
