"""C248 source contract: geometry-only NitroFS can reach the native pair loader.

This is NOT a substitute for a private asset-integrated emulator test.
"""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / 'source/main.c').read_text()


class GeometryOnlyNitroFsTests(unittest.TestCase):
    def test_legacy_preview_is_still_independently_optional(self):
        self.assertIn('int legacy_preview_found=preview_ready&&resource>=0&&previewStreamLoad(resource);', SOURCE)

    def test_native_pair_load_requires_nitrofs_not_legacy_preview(self):
        start = SOURCE.index('p3dVerifiedGeometryPairClear(&source_geometry_pair);')
        end = SOURCE.index('preview_found=legacy_preview_found||source_geometry_ready;', start)
        block = SOURCE[start:end]
        self.assertIn('if(nitro_ready&&resource>=0){', block)
        self.assertNotIn('if(preview_ready&&resource>=0){', block)
        self.assertIn('p3dVerifiedGeometryPairLoad(', block)
        self.assertIn('"nitro:/geometry/p%03d.p3vx"', block)
        self.assertIn('"nitro:/geometry/p%03d.p3ix"', block)

    def test_native_geometry_only_marks_preview_found(self):
        self.assertIn('preview_found=legacy_preview_found||source_geometry_ready;', SOURCE)

    def test_invalid_native_pair_retains_legacy_fallback(self):
        self.assertIn('if(previewStreamHasModel())previewStreamDraw();', SOURCE)
        self.assertIn('source_geometry_ready=0;', SOURCE)

    def test_geometry_only_ui_reports_native_triangle_count_not_empty_legacy_stream(self):
        self.assertIn('source_geometry_ready ? (unsigned long)source_geometry_pair.triangles', SOURCE)
        self.assertIn('Native geometry: untextured candidate', SOURCE)

    def test_native_loader_does_not_claim_verified_original_renderer(self):
        self.assertIn('CRC/bounds prove transport, NOT original 3DS renderer provenance.', SOURCE)


if __name__ == '__main__':
    unittest.main()
