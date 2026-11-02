#!/usr/bin/env python3
"""C222: audit original C5 animation-owner links against native P3SK rigs.

Run only on owner-authorized private archives. This tool emits P3TB v1
sidecars for verified source owner-to-node associations. It does not infer
animation clips, keyframes, interpolation, FPS, skin weights, or playback.
Never publish original archives, sidecars, source hashes, or detailed reports.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, re, struct, zipfile, zlib
from pathlib import Path

ROSTER = set(range(734)) - {721, 722, 723, 724}
PART_RANGES = ((0, 249), (250, 499), (500, 733))
CHANNEL_CODES = (0x00040071, 0x00030053, 0x00030054)
C5_NAME = re.compile(r"decoded_c5/p([0-9]{3})\.c5\Z")
P3SK_HEADER = struct.Struct("<4sHHHHII")
P3TB_HEADER = struct.Struct("<4sHHHHII")
P3TB_RECORD = struct.Struct("<HHI104s")
MAX_C5_BYTES = 16 * 1024 * 1024
MAX_NODES = 160
MAX_NAME = 96

def _crc(data: bytes) -> int:
    return zlib.crc32(data) & 0xffffffff

def _read_refs(decoder_zip: Path) -> dict:
    with zipfile.ZipFile(decoder_zip) as z:
        names = z.namelist()
        if names.count("C56_validation.csv") != 1 or len(names) != len(set(names)):
            raise ValueError("ambiguous C56 validation catalog")
        payload = z.read("C56_validation.csv")
    refs = {}
    for row in csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))):
        label = row.get("model", "")
        if not re.fullmatch(r"p[0-9]{3}", label) or label in refs:
            raise ValueError("invalid/duplicate C56 catalog model")
        if not re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")):
            raise ValueError("invalid C56 source SHA-256")
        refs[label] = row
    if set(refs) != {f"p{i:03d}" for i in ROSTER}:
        raise ValueError("C56 validation catalog is not the complete 730-model roster")
    return refs

def _node_table(raw: bytes):
    if len(raw) < 0x78 or raw[:2] != b"\xc5\x78":
        raise ValueError("not a decoded C5 source model")
    count = struct.unpack_from("<I", raw, 0x10)[0] >> 16
    start, stop = struct.unpack_from("<II", raw, 0x38)
    strings = struct.unpack_from("<I", raw, 0x64)[0]
    if not 1 <= count <= MAX_NODES or start < 0x78 or stop > len(raw) or stop-start != count*56:
        raise ValueError("C5 node table boundary/count mismatch")
    if not 0x78 <= strings < len(raw):
        raise ValueError("C5 string table outside source model")
    nodes, unique = [], set()
    for index in range(count):
        at = start + index*56
        matrix = struct.unpack_from("<12f", raw, at)
        if any(not __import__("math").isfinite(v) for v in matrix):
            raise ValueError("nonfinite source node transform")
        flags, offset = struct.unpack_from("<II", raw, at+48)
        parent, kind = flags & 0xffff, flags >> 16
        if kind != 1 or (parent != 0xffff and parent >= index):
            raise ValueError("invalid original node kind/parent")
        if offset > 16384 or strings+offset >= len(raw):
            raise ValueError("source node name offset outside C5 strings")
        pos = strings + offset
        end = raw.find(b"\0", pos, min(len(raw), pos+MAX_NAME+1))
        if end <= pos:
            raise ValueError("empty/unterminated original node name")
        name = raw[pos:end]
        if len(name) > MAX_NAME or any(c < 32 or c > 126 for c in name):
            raise ValueError("invalid original node name")
        if name in unique:
            raise ValueError("duplicate original node name")
        unique.add(name)
        nodes.append((offset, name))
    return count, start, stop, strings, nodes

def _build_model(raw: bytes, model_id: int, skeleton: bytes, expected_links: int):
    count, node_start, node_stop, string_start, nodes = _node_table(raw)
    if len(skeleton) < P3SK_HEADER.size:
        raise ValueError("truncated P3SK sidecar")
    magic, version, sk_model, sk_nodes, roots, string_len, expected_crc = P3SK_HEADER.unpack_from(skeleton)
    if (magic, version, sk_model, sk_nodes) != (b"P3SK", 1, model_id, count):
        raise ValueError("P3SK model ID or node count mismatch")
    content = skeleton[P3SK_HEADER.size:]
    if len(content) != count*56 + string_len or _crc(content) != expected_crc:
        raise ValueError("P3SK length/CRC mismatch")
    if content[:count*56] != raw[node_start:node_stop]:
        raise ValueError("P3SK node records differ from original C5 source")
    sk_strings = content[count*56:]
    for offset, name in nodes:
        if offset >= string_len:
            raise ValueError("P3SK string table does not cover original name offset")
        end = sk_strings.find(b"\0", offset, min(string_len, offset+MAX_NAME+1))
        if end < offset or sk_strings[offset:end] != name:
            raise ValueError("P3SK name differs from exact C5 source name")
    track_start, track_stop = struct.unpack_from("<II", raw, 0x48)
    if track_start < 0x78 or track_stop < track_start or track_stop > len(raw) or (track_stop-track_start)%16:
        raise ValueError("C5 track table boundary mismatch")
    track_count = (track_stop-track_start)//16
    tracks = [struct.unpack_from("<4I", raw, track_start+16*i) for i in range(track_count)]
    records, used_nodes, previous = [], set(), -1
    i = 0
    while i < track_count:
        if tracks[i][3] != CHANNEL_CODES[0]:
            i += 1
            continue
        triple = tracks[i:i+3]
        if len(triple) != 3 or tuple(x[3] for x in triple) != CHANNEL_CODES:
            raise ValueError("incomplete original three-channel owner group")
        if len({x[1] for x in triple}) != 1 or len({x[2]&0xffff for x in triple}) != 1:
            raise ValueError("original track group owner/control mismatch")
        owner = triple[0][1]
        node, offset = owner & 0xffff, owner >> 16
        if node >= count or nodes[node][0] != offset:
            raise ValueError("original track owner does not identify exact source node")
        if node in used_nodes or i <= previous:
            raise ValueError("duplicate/out-of-order original animated node")
        name = nodes[node][1]
        if len(name) > MAX_NAME:
            raise ValueError("original node name exceeds P3TB bound")
        records.append(P3TB_RECORD.pack(node, offset, i, name.ljust(104, b"\0")))
        used_nodes.add(node)
        previous = i
        i += 3
    if len(records) != expected_links:
        raise ValueError("original track-to-node count differs from independent C150 audit")
    payload = b"".join(records)
    header = P3TB_HEADER.pack(b"P3TB", 1, model_id, len(records), 0,
                              _crc(content), _crc(payload))
    return header + payload, {"nodes": count, "roots": roots,
                              "links": len(records), "track_records": track_count,
                              "suffix_names": sum(1 for off,_ in nodes if off and raw[string_start+off-1] != 0)}

def audit(parts, decoder_zip, p3sk_zip, cross_stage_report, output_zip=None):
    if len(parts) != 3:
        raise ValueError("exactly three ordered C56 archives are required")
    refs = _read_refs(decoder_zip)
    prior = json.loads(Path(cross_stage_report).read_text(encoding="utf-8"))
    checks = prior.get("model_checks", [])
    baseline = {x.get("model"): x for x in checks}
    if len(baseline) != 730 or set(baseline) != set(refs):
        raise ValueError("independent C150 per-model audit is incomplete")
    if output_zip is not None and Path(output_zip).exists():
        raise ValueError("refusing to overwrite private P3TB archive")
    seen, summary, sidecars = set(), {"models":0,"nodes":0,"links":0,"track_records":0,"suffix_names":0}, {}
    sk = zipfile.ZipFile(p3sk_zip)
    try:
        sk_names = sk.namelist()
        if len(sk_names) != 730 or len(sk_names) != len(set(sk_names)):
            raise ValueError("P3SK archive roster is not exactly 730 unique sidecars")
        for part_index, part in enumerate(parts):
            low, high = PART_RANGES[part_index]
            with zipfile.ZipFile(part) as z:
                entries = z.infolist()
                if len(entries) != len({e.filename for e in entries}):
                    raise ValueError("duplicate C56 archive members")
                for entry in entries:
                    match = C5_NAME.fullmatch(entry.filename)
                    if not match:
                        raise ValueError("unexpected C56 archive member")
                    model_id = int(match.group(1)); label = f"p{model_id:03d}"
                    if model_id not in ROSTER or not low <= model_id <= high or label in seen:
                        raise ValueError("displaced or duplicate C56 model")
                    if not 0x78 <= entry.file_size <= MAX_C5_BYTES:
                        raise ValueError("C5 source file size outside bounds")
                    raw = z.read(entry); digest = hashlib.sha256(raw).hexdigest()
                    ref = refs[label]; cross = baseline[label]
                    if digest != ref["sha256"] or len(raw) != int(ref["decoded_bytes"]) or digest != cross["c56_sha256"]:
                        raise ValueError("C56 SHA/size differs from independent source audit")
                    sk_path = f"skeleton/{label}.p3sk"
                    if sk_path not in sk_names:
                        raise ValueError("missing model-matched P3SK sidecar")
                    sidecar, counts = _build_model(raw, model_id, sk.read(sk_path),
                                                   int(cross["named_animation_to_node_links"]))
                    sidecars[f"bindings/{label}.p3tb"] = sidecar
                    summary["models"] += 1
                    for key in ("nodes","links","track_records","suffix_names"):
                        summary[key] += counts[key]
                    seen.add(label)
        if seen != set(refs) or summary["models"] != 730:
            raise ValueError("incomplete original 730-model source roster")
        if output_zip is not None:
            dst = Path(output_zip); dst.parent.mkdir(parents=True, exist_ok=True)
            tmp = dst.with_suffix(dst.suffix+".partial")
            if tmp.exists(): raise ValueError("partial output archive already exists")
            try:
                with zipfile.ZipFile(tmp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as out:
                    for name,data in sorted(sidecars.items()):
                        out.writestr(name,data)
                tmp.replace(dst)
            except BaseException:
                tmp.unlink(missing_ok=True)
                raise
    finally:
        sk.close()
    summary.update({"source_sha_crosscheck":"C56 catalog + C150 independent model report",
                    "p3sk_original_node_bytes_exact":True,
                    "p3sk_original_name_offsets_exact":True,
                    "owner_node_index_and_name_verified":True,
                    "p3tb_private_sidecars_written":len(sidecars) if output_zip else 0,
                    "clip_semantics_verified":False,"keyframe_playback_verified":False,
                    "skin_weights_verified":False,"DS_animation_playback_verified":False})
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--parts",nargs=3,type=Path,required=True)
    p.add_argument("--decoder-zip",type=Path,required=True)
    p.add_argument("--p3sk-zip",type=Path,required=True)
    p.add_argument("--cross-stage-report",type=Path,required=True)
    p.add_argument("--private-p3tb-zip",type=Path)
    p.add_argument("--private-report",type=Path,required=True)
    a=p.parse_args()
    if a.private_report.exists(): p.error("refusing to overwrite private report")
    result=audit(a.parts,a.decoder_zip,a.p3sk_zip,a.cross_stage_report,a.private_p3tb_zip)
    a.private_report.parent.mkdir(parents=True,exist_ok=True)
    a.private_report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
