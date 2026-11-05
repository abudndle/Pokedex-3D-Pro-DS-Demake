"""Original-GUI indexed geometry tests using completely synthetic C5 sources."""
import pathlib
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from c359_synthetic_fixtures import source,archive
from c359_gui_vertex_uv_topology import recover,recover_geometry

class C359Tests(unittest.TestCase):
    def test_source_uv_vertices_and_triangles(self):
        r=recover_geometry(source('gui_common'))
        self.assertEqual((r['draw_records'],r['original_vertices'],r['original_triangle_indices']),(5,20,30))
        self.assertEqual(r['draws'][0]['vertices'][1]['original_unsigned_uv_words'],[512,512])
        self.assertEqual(r['draws'][0]['triangle_vertex_indices'][0],[0,1,2])
        self.assertFalse(r['original_uv_coordinate_scale_and_origin_verified'])

    def test_color_vertex_tail_not_assumed_uv(self):
        r=recover_geometry(source('gui_title'))
        self.assertEqual(r['color_byte_vertex_records'],392)
        self.assertEqual(r['uv_word_vertex_records'],0)
        self.assertEqual(r['draws'][0]['vertices'][0]['original_vertex_color_bytes'],[3,7,11,255])

    def test_all_original_like_geometry_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            p=pathlib.Path(temp)/'src.zip'
            archive(p)
            r=recover(p)
            self.assertEqual((r['original_gui_resources'],r['draw_records']), (16,51))
            self.assertEqual((r['original_vertices'],r['original_triangle_indices']), (2352,3864))
            self.assertEqual((r['original_indexed_triangles'],r['color_byte_vertex_records']), (1288,392))
            self.assertEqual(r['identical_numbered_jp_en_geometry_pairs'],6)
            self.assertEqual(r['required_release_files_missing'],16)
            self.assertFalse(r['release_ready'])

if __name__=='__main__': unittest.main()
