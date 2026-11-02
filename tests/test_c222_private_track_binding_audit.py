"""C222 private 730-model C5/P3SK audit; synthetic fixtures only."""
import csv, hashlib, io, json, pathlib, struct, tempfile, unittest, zipfile, zlib
from tools.c222_private_track_binding_audit import audit, _build_model, P3SK_HEADER, CHANNEL_CODES

def fixture_model(model):
    raw=bytearray(0x270)
    raw[:2]=b"\xc5\x78"
    struct.pack_into("<I",raw,0x10,2<<16)
    struct.pack_into("<II",raw,0x38,0x200,0x270)
    struct.pack_into("<II",raw,0x48,0x80,0xb0)
    struct.pack_into("<I",raw,0x64,0x190)
    for i,code in enumerate(CHANNEL_CODES):
        struct.pack_into("<4I",raw,0x80+i*16,0x100+i*16,1,1,code)
    raw[0x190:0x190+14]=b"BoneRoot\0Base\0"
    ident=(1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.)
    struct.pack_into("<12fII",raw,0x200,*ident,(1<<16)|0xffff,9)
    struct.pack_into("<12fII",raw,0x238,*ident,(1<<16)|0,0)
    raw=bytes(raw)
    content=raw[0x200:0x270]+b"BoneRoot\0Base\0"
    p3sk=P3SK_HEADER.pack(b"P3SK",1,model,2,1,14,zlib.crc32(content)&0xffffffff)+content
    return raw,p3sk

class C222PrivateTrackBindingAuditTests(unittest.TestCase):
    def test_native_format_exact_binding(self):
        raw,sk=fixture_model(14)
        tb,counts=_build_model(raw,14,sk,1)
        self.assertEqual(counts,{"nodes":2,"roots":1,"links":1,"track_records":3,"suffix_names":0})
        self.assertEqual(tb[:4],b"P3TB")
        self.assertEqual(struct.unpack_from("<HHHH",tb,4),(1,14,1,0))
        node,offset,first,name=struct.unpack_from("<HHI104s",tb,20)
        self.assertEqual((node,offset,first,name.split(b"\0")[0]),(1,0,0,b"BoneRoot"))

    def test_reject_source_or_sidecar_model_mismatch(self):
        raw,sk=fixture_model(14)
        with self.assertRaisesRegex(ValueError,"model ID or node count"):
            _build_model(raw,14,fixture_model(15)[1],1)
        with self.assertRaisesRegex(ValueError,"count differs"):
            _build_model(raw,14,sk,2)

    def test_reject_corrupt_skeleton_and_bad_owner(self):
        raw,sk=fixture_model(14)
        damaged=bytearray(sk);damaged[-1]^=1
        with self.assertRaisesRegex(ValueError,"CRC"):
            _build_model(raw,14,bytes(damaged),1)
        wrong=bytearray(raw);struct.pack_into("<I",wrong,0x80+4,2)
        with self.assertRaisesRegex(ValueError,"exact source node"):
            _build_model(bytes(wrong),14,sk,1)

    def test_full_730_model_roster_synthetic_audit_and_private_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);parts=[]
            roster=set(range(734))-{721,722,723,724}
            refs=[];checks=[]
            for part_index,(lo,hi) in enumerate(((0,249),(250,499),(500,733))):
                path=root/f"part{part_index}.zip"
                with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
                    for model in range(lo,hi+1):
                        if model not in roster: continue
                        raw,sk=fixture_model(model);label=f"p{model:03d}"
                        digest=hashlib.sha256(raw).hexdigest()
                        z.writestr(f"decoded_c5/{label}.c5",raw)
                        refs.append({"model":label,"decoded_bytes":str(len(raw)),"sha256":digest})
                        checks.append({"model":label,"c56_sha256":digest,"named_animation_to_node_links":1})
                parts.append(path)
            decoder=root/"decoder.zip"
            with zipfile.ZipFile(decoder,"w") as z:
                out=io.StringIO();w=csv.DictWriter(out,fieldnames=["model","decoded_bytes","sha256"])
                w.writeheader();w.writerows(refs);z.writestr("C56_validation.csv",out.getvalue())
            skzip=root/"skeletons.zip"
            with zipfile.ZipFile(skzip,"w",compression=zipfile.ZIP_DEFLATED) as z:
                for model in sorted(roster):
                    _,sk=fixture_model(model);z.writestr(f"skeleton/p{model:03d}.p3sk",sk)
            cross=root/"cross.json";cross.write_text(json.dumps({"model_checks":checks}))
            output=root/"private-p3tb.zip"
            result=audit(parts,decoder,skzip,cross,output)
            self.assertEqual(result["models"],730)
            self.assertEqual(result["nodes"],1460)
            self.assertEqual(result["links"],730)
            self.assertEqual(result["track_records"],2190)
            self.assertEqual(result["p3tb_private_sidecars_written"],730)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(len(z.namelist()),730)
                self.assertIsNone(z.testzip())
                self.assertEqual(z.read("bindings/p000.p3tb")[:4],b"P3TB")

if __name__=="__main__": unittest.main()
