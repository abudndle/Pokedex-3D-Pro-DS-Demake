"""C335 structural guard for Nitro Engine opt-in and legacy non-rewrite."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class NativeAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main=(ROOT/'source/main.c').read_text()
        cls.bridge=(ROOT/'source/nitro_source_bridge.c').read_text()
        cls.makefile=(ROOT/'Makefile.native').read_text()

    def test_libnds_2d_stays_in_charge(self):
        self.assertIn('consoleInit(&bottom_console',self.main)
        self.assertIn('videoSetModeSub(MODE_0_2D)',self.main)
        self.assertIn('glInit();',self.main)
        self.assertNotIn('NE_Init3D();',self.main) # avoid 2D VRAM reset
        self.assertIn('NE_ModelSystemReset',self.bridge)
        self.assertIn('NE_AnimationSystemReset',self.bridge)

    def test_existing_source_geometry_renderer_preserved(self):
        self.assertIn('p3dVerifiedGeometryPairLoad(',self.main)
        self.assertIn('p3dVerifiedPrimitiveDraw(',self.main)
        self.assertIn('p3dDsMaterialUvDraw(',self.main)
        self.assertIn('!native_material_ready && p3dNitroBridgeDraw()',self.main)

    def test_nitro_engine_and_dsma_actually_called(self):
        for method in ('NE_ModelLoadStaticMesh(','NE_ModelLoadDSM(','NE_AnimationLoad(',
                       'NE_ModelSetAnimation','NE_ModelDraw',
                       'NE_ModelAnimateAll'):
            self.assertIn(method,self.bridge)
        self.assertIn('P3D_USE_NITRO_ENGINE',self.makefile)
        self.assertIn('-lNE',self.makefile)

    def test_original_geometry_pair_gates_engine_assets(self):
        self.assertIn('if(source_geometry_ready)',self.main)
        self.assertIn('source_geometry_pair.vx,source_geometry_pair.vx_size',self.main)
        self.assertIn('source_geometry_pair.ix,source_geometry_pair.ix_size',self.main)
        self.assertIn('p3dNitroManifestValidate',self.bridge)
        self.assertIn('p3dNitroPayloadValidate',self.bridge)

if __name__=='__main__':unittest.main()
