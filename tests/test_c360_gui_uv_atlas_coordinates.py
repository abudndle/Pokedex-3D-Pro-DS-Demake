"""C360 synthetic source UV/atlas rational mapping tests; no original bytes."""
import copy
import pathlib
import sys
import tempfile
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'tools'))
from c360_gui_uv_atlas_coordinates import exact, link_atlas_uv, read_catalog

HASH = 'a' * 64
ARCHIVE = 'b' * 64

def vertex(index, uv=None, color=None):
    v = {'index': index}
    if uv is not None: v['original_unsigned_uv_words'] = list(uv)
    if color is not None: v['original_vertex_color_bytes'] = list(color)
    return v

def make_source():
    common = [(0,0),(2048,0),(2048,2048),(0,2048)]
    title_uv = [(0,1312),(1440,1312),(1440,2048),(0,2048)]
    root = {'source_archive_sha256': ARCHIVE, 'resources': {
        'gui_common': {
            'source_c5_sha256': HASH,
            'draws':[{'draw_slot':0,'source_texture_name':'tex00',
                      'scene_node_index':0,'vertex_attribute_source_tag':'4420',
                      'vertices':[vertex(i,u) for i,u in enumerate(common)]}]},
        'en/gui_title': {
            'source_c5_sha256': HASH,
            'draws':[
                {'draw_slot':0,'source_texture_name':None,
                 'scene_node_index':1,'vertex_attribute_source_tag':'7520',
                 'vertices':[vertex(i,color=(0,20,40,255)) for i in range(4)]},
                {'draw_slot':1,'source_texture_name':'titlepro_en',
                 'scene_node_index':2,'vertex_attribute_source_tag':'4420',
                 'vertices':[vertex(i,uv) for i,uv in enumerate(title_uv)]},
            ]}}}
    manifest = {'private_source_archive_sha256':ARCHIVE, 'entries':[
        {'original_source':'decoded_c5/gui/gui_common.c5','name':'tex00',
         'width':1024,'height':1024,'original_c5_sha256':HASH,
         'png_path':'gui_common/t00_tex00.png','png_sha256':'1'*64},
        {'original_source':'decoded_c5/gui/en/gui_title.c5','name':'titlepro_en',
         'width':256,'height':256,'original_c5_sha256':HASH,
         'png_path':'en/gui_title/t00_titlepro_en.png','png_sha256':'2'*64},
    ]}
    return root, manifest

class TestC360(unittest.TestCase):
    def setUp(self):
        self.topology, self.manifest = make_source()

    def test_rational_q11_coordinates_exact(self):
        self.assertEqual(exact(1440,256),{'numerator':180,'denominator':1})
        self.assertEqual(exact(1312,256),{'numerator':164,'denominator':1})
        self.assertEqual(exact(1,256),{'numerator':1,'denominator':8})
        self.assertEqual(exact(2048,1024),{'numerator':1024,'denominator':1})

    def test_english_title_crop_matches_source_180x92(self):
        r=link_atlas_uv(self.topology,self.manifest)
        self.assertTrue(r['english_title_180x92_source_pixel_rect_match'])
        rect=r['resources']['en/gui_title']['draws'][1]['candidate_atlas_pixel_rect_exact']
        self.assertEqual(rect['top'],{'numerator':164,'denominator':1})
        self.assertEqual(rect['bottom'],{'numerator':256,'denominator':1})
        self.assertFalse(r['GPU_runtime_UV_normalization_and_origin_verified'])
        self.assertFalse(r['release_ready'])

    def test_full_atlas_corners_are_source_evidence(self):
        r=link_atlas_uv(self.topology,self.manifest)
        self.assertEqual(r['source_full_atlas_2048_corner_quads'],1)
        self.assertEqual(r['source_draws_with_atlas'],2)
        self.assertEqual(r['source_draws_without_atlas'],1)
        self.assertEqual(r['source_raw_uv_vertex_records'],8)
        self.assertEqual(r['source_color_vertex_records'],4)

    def test_do_not_treat_untextured_color_as_uv(self):
        r=link_atlas_uv(self.topology,self.manifest)
        self.assertFalse(r['resources']['en/gui_title']['draws'][0]['source_uv_mapping_available'])

    def test_reject_cross_archive_input(self):
        self.manifest['private_source_archive_sha256']='c'*64
        with self.assertRaisesRegex(ValueError,'mismatched'):
            link_atlas_uv(self.topology,self.manifest)

    def test_reject_cross_c5_source_hash(self):
        self.manifest['entries'][0]['original_c5_sha256']='d'*64
        with self.assertRaisesRegex(ValueError,'source hash'):
            link_atlas_uv(self.topology,self.manifest)

    def test_reject_duplicate_named_original_texture(self):
        self.manifest['entries'].append(copy.deepcopy(self.manifest['entries'][0]))
        with self.assertRaisesRegex(ValueError,'duplicate'):
            link_atlas_uv(self.topology,self.manifest)

    def test_reject_out_of_range_raw_uv_word(self):
        self.topology['resources']['gui_common']['draws'][0]['vertices'][0]['original_unsigned_uv_words']=[2049,0]
        with self.assertRaisesRegex(ValueError,'u16 UV'):
            link_atlas_uv(self.topology,self.manifest)

    def test_reject_noninteger_uv_word(self):
        self.topology['resources']['gui_common']['draws'][0]['vertices'][0]['original_unsigned_uv_words']=[0,1.5]
        with self.assertRaisesRegex(ValueError,'u16 UV'):
            link_atlas_uv(self.topology,self.manifest)

    def test_reject_named_source_missing_texture(self):
        self.topology['resources']['gui_common']['draws'][0]['source_texture_name']='unknown'
        with self.assertRaisesRegex(ValueError,'matching original texture'):
            link_atlas_uv(self.topology,self.manifest)

    def test_reject_missing_original_color_fields(self):
        self.topology['resources']['en/gui_title']['draws'][0]['vertices'][0].pop('original_vertex_color_bytes')
        with self.assertRaisesRegex(ValueError,'cannot be treated as UVs'):
            link_atlas_uv(self.topology,self.manifest)

    def test_reject_wrong_source_vertex_attribute(self):
        self.topology['resources']['gui_common']['draws'][0]['vertex_attribute_source_tag']='7520'
        with self.assertRaisesRegex(ValueError,'matching original texture'):
            link_atlas_uv(self.topology,self.manifest)

    def test_reject_unsafe_atlas_dimensions(self):
        self.manifest['entries'][0]['width']=300
        with self.assertRaisesRegex(ValueError,'source dimensions'):
            link_atlas_uv(self.topology,self.manifest)

    def test_reject_skipped_source_draw_slot(self):
        self.topology['resources']['en/gui_title']['draws'][1]['draw_slot']=3
        with self.assertRaisesRegex(ValueError,'draw/vertex'):
            link_atlas_uv(self.topology,self.manifest)

    def test_catalog_file_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            src=pathlib.Path(td)/'source.json'
            src.write_text('{}')
            link=pathlib.Path(td)/'linked.json'
            link.symlink_to(src)
            with self.assertRaisesRegex(ValueError,'private source catalog'):
                read_catalog(link)

if __name__=='__main__':
    unittest.main()
