"""C358 tests: material/texture/node provenance with zero original assets."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from c358_synthetic_fixtures import fake_c5,fake_archive
from c358_gui_material_mesh_bindings import extract_source_bindings,recover


class C358Tests(unittest.TestCase):
    def test_all_16_source_like_rosters(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'source.zip';fake_archive(path)
            r=recover(path)
            self.assertEqual([r[k] for k in (
                'original_C5_resources','original_scene_nodes','original_texture_entries',
                'original_material_records','original_mesh_draw_records',
                'source_textured_draw_records','draw_records_without_static_texture')],
                [16,78,132,35,51,45,6])
            self.assertEqual(r['identical_EN_JP_numbered_material_and_mesh_pairs'],6)
            self.assertFalse(r['release_ready'])

    def test_material_to_named_source_atlas_to_node(self):
        r=extract_source_bindings(fake_c5('gui_common'))
        d=r['draws'][0]
        self.assertEqual((d['material_index'],d['source_texture_index'],
                          d['source_texture_name'],d['scene_node_index']),
                          (3,3,'atlas_3',0))
        self.assertEqual(r['draws'][4]['source_texture_name'],'atlas_2')
        self.assertTrue(d['static_texture_binding_evidence'])

    def test_two_untextured_materials_do_not_fake_atlas(self):
        r=extract_source_bindings(fake_c5('gui_title'))
        self.assertEqual(r['source_textured_draw_records'],0)
        self.assertEqual(r['draw_records_without_static_texture'],6)
        self.assertTrue(all(x['source_texture_name'] is None for x in r['draws']))

    def test_3d_source_bounds_not_mistaken_for_DS_projection(self):
        r=extract_source_bindings(fake_c5('en/gui01'))
        d=r['draws'][0]
        self.assertEqual(d['original_bounds_xyz_min'],[0.0,-16.0,0.0])
        self.assertEqual(d['original_bounds_xyz_max'],[32.0,0.0,0.0])
        self.assertEqual(d['scene_node_translation'],[10.0,-1.0,0.0])
        self.assertFalse(d['texture_UV_or_draw_order_verified'])
        self.assertTrue(d['source_space_bounds_not_projected_DS_pixels'])

    def test_reject_source_material_using_nonexistent_atlas(self):
        with self.assertRaisesRegex(ValueError,'texture outside'):
            extract_source_bindings(fake_c5('en/gui01',problem='texture'))

    def test_reject_out_of_range_material_slot(self):
        with self.assertRaisesRegex(ValueError,'material/draw/buffer/node'):
            extract_source_bindings(fake_c5('gui_common',problem='material'))

    def test_reject_out_of_range_scene_node(self):
        with self.assertRaisesRegex(ValueError,'material/draw/buffer/node'):
            extract_source_bindings(fake_c5('en/gui01',problem='node'))

    def test_reject_out_of_range_geometry_buffer(self):
        with self.assertRaisesRegex(ValueError,'material/draw/buffer/node'):
            extract_source_bindings(fake_c5('en/gui01',problem='buffer'))

    def test_reject_inverted_native_geometry_bounds(self):
        with self.assertRaisesRegex(ValueError,'draw bounds'):
            extract_source_bindings(fake_c5('en/gui01',problem='bounds'))

    def test_reject_empty_source_primitive_count(self):
        with self.assertRaisesRegex(ValueError,'material/draw/buffer/node'):
            extract_source_bindings(fake_c5('gui_common',problem='primitive'))

    def test_reject_corrupt_material_section_boundary(self):
        raw=bytearray(fake_c5('gui_common'))
        pos=struct.unpack_from('<I',raw,0x68)[0]
        off=struct.unpack_from('<I',raw,pos+0x38)[0]
        struct.pack_into('<I',raw,pos+0x38,off+1)
        with self.assertRaises(ValueError):
            extract_source_bindings(bytes(raw))

    def test_reject_numbered_jp_en_material_disagreement(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'source.zip';fake_archive(src,mismatch=True)
            with self.assertRaisesRegex(ValueError,'English/Japanese'):
                recover(src)

    def test_reject_missing_original_C5(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'source.zip'
            fake_archive(src,omit='decoded_c5/gui/en/gui01.c5')
            with self.assertRaisesRegex(ValueError,'missing original'):
                recover(src)

    def test_reject_duplicate_member(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'source.zip';fake_archive(src,duplicate=True)
            with self.assertRaisesRegex(ValueError,'duplicate'):
                recover(src)

    def test_reject_symlink_original_archive(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'source.zip';fake_archive(src)
            link=Path(d)/'alias.zip';link.symlink_to(src)
            with self.assertRaisesRegex(ValueError,'symlink'):
                recover(link)


if __name__=='__main__':
    unittest.main()
