"""Synthetic original C5 56-byte node hierarchy + private P3SK ZIP regression."""
import csv,hashlib,io,json,math
from pathlib import Path
import struct,sys,tempfile,unittest,zipfile,zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from c148_c5_skeleton_hierarchy import inspect_source_nodes,packed_skeleton,audit,SKELETON_HEADER
from c140_c5_shader_inventory import ROSTER,PART_RANGES
from test_c147_c5_named_nodes import named_source


def synth_source():
    b=bytearray(named_source())
    b.extend(b'\0'*0x100)
    # C147's named group uses owner token ABCD; point at actual node index1.
    for i in range(3):struct.pack_into('<I',b,0x80+16*i+4,1)
    b[0x190:0x190+14]=b'BoneRoot\0Base\0'
    original=struct.unpack_from('<I',b,0x10)[0]
    struct.pack_into('<I',b,0x10,(2<<16)|(original&65535))
    struct.pack_into('<I',b,0x38,0x200)
    struct.pack_into('<I',b,0x3c,0x200+2*56)
    identity=(1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.)
    struct.pack_into('<12fII',b,0x200,*identity,(1<<16)|65535,9)
    shifted=(1.,0.,0.,2.,0.,1.,0.,3.,0.,0.,1.,4.)
    struct.pack_into('<12fII',b,0x200+56,*shifted,(1<<16)|0,0)
    return bytes(b)


def fixture(root):
    raw=synth_source();digest=hashlib.sha256(raw).hexdigest()
    parts=[];rows=[];baseline={}
    for i,(lo,hi) in enumerate(PART_RANGES):
        path=root/f'part{i}.zip'
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for model in range(lo,hi+1):
                if model not in ROSTER:continue
                label=f'p{model:03d}'
                z.writestr(f'decoded_c5/{label}.c5',raw)
                rows.append({'model':label,'sha256':digest,'decoded_bytes':str(len(raw))})
                baseline[label]={'source_sha256':digest,'original_named_transform_track_groups':1}
        parts.append(path)
    out=io.StringIO();writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    tool=root/'decoder.zip'
    with zipfile.ZipFile(tool,'w') as z:z.writestr('C56_validation.csv',out.getvalue())
    summary=root/'c147.json';summary.write_text(json.dumps({'original_C56_models_verified':730,
          'source_C5_named_node_tracks_verified':730,'models':baseline}))
    return parts,tool,summary

class C148Tests(unittest.TestCase):
    def test_node_parents_and_named_animation_owner(self):
        info=inspect_source_nodes(synth_source(),detailed=True)
        self.assertEqual((info['source_nodes'],info['root_nodes'],info['parent_edges'],info['animated_nodes']),(2,1,1,1))
        nodes=info['original_source_nodes']
        self.assertEqual([n['source_name'] for n in nodes],['Base','BoneRoot'])
        self.assertEqual([n['parent_index'] for n in nodes],[None,0])
        self.assertEqual(nodes[1]['source_affine_3x4'][3],2)
        self.assertFalse(info['source_skeletal_skin_weights_verified'])

    def test_private_p3sk_keeps_exact_node_transform_bits_and_crc(self):
        raw=synth_source();info=inspect_source_nodes(raw)
        binary=packed_skeleton(123,info)
        magic,ver,model,n,roots,names_len,crc=SKELETON_HEADER.unpack_from(binary)
        self.assertEqual((magic,ver,model,n,roots), (b'P3SK',1,123,2,1))
        self.assertEqual(crc,zlib.crc32(binary[SKELETON_HEADER.size:])&0xffffffff)
        self.assertEqual(binary[SKELETON_HEADER.size:SKELETON_HEADER.size+112],raw[0x200:0x270])
        self.assertEqual(binary[-names_len:],b'BoneRoot\0Base\0')

    def test_reject_bad_node_parent_record_name_matrix_and_owner(self):
        for mutate in ('parent','kind','matrix','owner','stride'):
            raw=bytearray(synth_source())
            if mutate=='parent':struct.pack_into('<I',raw,0x200+56+48,(1<<16)|2)
            if mutate=='kind':struct.pack_into('<I',raw,0x200+56+48,(2<<16)|0)
            if mutate=='matrix':struct.pack_into('<f',raw,0x200+56,math.nan)
            if mutate=='owner':
                for i in range(3):struct.pack_into('<I',raw,0x80+16*i+4,0)
            if mutate=='stride':struct.pack_into('<I',raw,0x3c,0x200+55)
            with self.assertRaisesRegex(ValueError,'parent|kind|nonfinite|owner|stride'):
                inspect_source_nodes(bytes(raw))

    def test_730_models_source_sha_and_private_nitrofs_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);parts,decoder,summary=fixture(root)
            output=root/'private-original-skeletons.zip'
            report=audit(parts,decoder,summary,private_zip=output)
            self.assertEqual(report['source_models_verified'],730)
            self.assertEqual(report['original_node_records_verified'],1460)
            self.assertEqual(report['source_parent_edges_verified'],730)
            self.assertEqual(report['original_animated_nodes_linked_to_skeleton'],730)
            self.assertEqual(report['private_skeleton_sidecar_files'],730)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(len(z.namelist()),730)
                self.assertIsNone(z.testzip())
                self.assertTrue(z.read('skeleton/p000.p3sk').startswith(b'P3SK'))
            with self.assertRaisesRegex(ValueError,'overwrite'):
                audit(parts,decoder,summary,private_zip=output)
            with self.assertRaisesRegex(ValueError,'displaced'):
                audit(parts[::-1],decoder,summary)

if __name__=='__main__':unittest.main()