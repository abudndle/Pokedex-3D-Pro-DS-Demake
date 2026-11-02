"""Synthetic packer contract for original C5 owner bindings; no game assets."""
import pathlib
import struct
import sys
import unittest
import zlib
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import c151_original_track_bindings as c151

class OriginalTrackPackerTests(unittest.TestCase):
    def data(self,tracks=None):
        node={'source_nodes':2,'animated_nodes':1,
              'original_source_nodes':[
                  {'original_name_offset':9,'source_name':'Base'},
                  {'original_name_offset':0,'source_name':'BoneRoot'}]}
        track={'source_owner_token':1,'name_offset_in_original_C5_strings':0,
               'source_first_track_record':3,'original_node_name':'BoneRoot'}
        if tracks is None:tracks=[track]
        return node,tracks
    def test_pack_exact_name_owner_crc(self):
        node,tracks=self.data()
        with patch.object(c151,'inspect_source_nodes',return_value=node), \
             patch.object(c151,'inspect_tracks',return_value={'original_source_named_node_tracks':tracks}), \
             patch.object(c151,'packed_skeleton',return_value=b'P3SK'+b'X'*16+b'rig'):
            packed=c151.pack_binding(14,b'synthetic source',b'P3SK'+b'X'*16+b'rig')
        self.assertEqual(len(packed),20+112)
        self.assertEqual(struct.unpack_from('<H',packed,8)[0],1)
        self.assertEqual(struct.unpack_from('<I',packed,12)[0],zlib.crc32(b'rig'))
        self.assertEqual(struct.unpack_from('<I',packed,16)[0],zlib.crc32(packed[20:]))
        self.assertEqual(struct.unpack_from('<HHI',packed,20),(1,0,3))
        self.assertEqual(packed[28:36],b'BoneRoot')
    def test_reject_wrong_skeleton_name_and_owner(self):
        node,tracks=self.data()
        with patch.object(c151,'inspect_source_nodes',return_value=node), \
             patch.object(c151,'inspect_tracks',return_value={'original_source_named_node_tracks':tracks}), \
             patch.object(c151,'packed_skeleton',return_value=b'expected'):
            with self.assertRaises(ValueError):
                c151.pack_binding(14,b'synthetic',b'wrong')
            tracks[0]['original_node_name']='Wrong'
            with self.assertRaises(ValueError):
                c151.pack_binding(14,b'synthetic',b'expected')
    def test_reject_duplicate_and_nonmonotonic_tracks(self):
        node,tracks=self.data()
        node['animated_nodes']=2
        tracks.append(dict(tracks[0],source_first_track_record=6))
        with patch.object(c151,'inspect_source_nodes',return_value=node), \
             patch.object(c151,'inspect_tracks',return_value={'original_source_named_node_tracks':tracks}), \
             patch.object(c151,'packed_skeleton',return_value=b'expected'):
            with self.assertRaises(ValueError):
                c151.pack_binding(14,b'synthetic',b'expected')
    def test_reject_owner_index_and_original_string_offset_mismatch(self):
        for field,value in [('source_owner_token',9),
                            ('name_offset_in_original_C5_strings',8)]:
            node,tracks=self.data()
            tracks[0][field]=value
            with patch.object(c151,'inspect_source_nodes',return_value=node), \
                 patch.object(c151,'inspect_tracks',return_value={'original_source_named_node_tracks':tracks}), \
                 patch.object(c151,'packed_skeleton',return_value=b'expected'):
                with self.subTest(field=field), self.assertRaises(ValueError):
                    c151.pack_binding(14,b'synthetic',b'expected')

    def test_reject_nonmonotonic_first_track_record(self):
        node,tracks=self.data()
        node['animated_nodes']=2
        second=dict(tracks[0],source_owner_token=0,
                    name_offset_in_original_C5_strings=9,
                    source_first_track_record=2,original_node_name='Base')
        tracks.append(second)
        with patch.object(c151,'inspect_source_nodes',return_value=node), \
             patch.object(c151,'inspect_tracks',return_value={'original_source_named_node_tracks':tracks}), \
             patch.object(c151,'packed_skeleton',return_value=b'expected'):
            with self.assertRaisesRegex(ValueError,'duplicate, out-of-range or unsorted'):
                c151.pack_binding(14,b'synthetic',b'expected')

    def test_reject_non_ascii_and_overlong_original_node_names(self):
        for name in ['BoneRøot','N'*97]:
            node,tracks=self.data()
            node['original_source_nodes'][1]['source_name']=name
            tracks[0]['original_node_name']=name
            with patch.object(c151,'inspect_source_nodes',return_value=node), \
                 patch.object(c151,'inspect_tracks',return_value={'original_source_named_node_tracks':tracks}), \
                 patch.object(c151,'packed_skeleton',return_value=b'expected'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    c151.pack_binding(14,b'synthetic',b'expected')

    def test_empty_source_tracks_do_not_invent_animations(self):
        node,tracks=self.data([])
        node['animated_nodes']=0
        with patch.object(c151,'inspect_source_nodes',return_value=node), \
             patch.object(c151,'inspect_tracks',return_value={'original_source_named_node_tracks':tracks}), \
             patch.object(c151,'packed_skeleton',return_value=b'expected'):
            self.assertEqual(c151.pack_binding(14,b'synthetic',b'expected'),b'')

if __name__=='__main__':unittest.main()
