#!/usr/bin/env python3
"""Decode a user's PRIVATE original 3DS CWAV DSP ADPCM to PCM16 WAV.

Source-only, opt-in diagnostic conversion. No commercial audio is bundled.
Does not implement original 3DS sound routing or Nintendo DS audio playback.
"""
import argparse
import hashlib
import json
import struct
import wave
import zipfile
from pathlib import Path

def u16(blob,at):return struct.unpack_from("<H",blob,at)[0]
def u32(blob,at):return struct.unpack_from("<I",blob,at)[0]

def reference(blob,at,expected,base):
    kind,reserved,offset=struct.unpack_from("<HHI",blob,at)
    if kind!=expected or reserved or offset==0xffffffff:
        raise ValueError("incorrect original-source block reference")
    return base+offset

def decode_dsp_adpcm(data,coefficient_pairs,sample_count,hist1=0,hist2=0):
    if len(coefficient_pairs)!=16 or sample_count<1 or sample_count>1000000:
        raise ValueError("unsupported original DSP sample length/coefficients")
    values=[];cursor=0
    while len(values)<sample_count:
        if cursor+8>len(data):raise ValueError("truncated DSP ADPCM frame")
        frame=data[cursor:cursor+8]
        cursor+=8
        predictor=frame[0]>>4
        shift=frame[0]&15
        if predictor>=8 or shift>12:
            raise ValueError("invalid Nintendo DSP predictor/shift")
        coef1,coef2=coefficient_pairs[2*predictor:2*predictor+2]
        for byte in frame[1:]:
            for nibble in (byte>>4,byte&15):
                delta=nibble-16 if nibble>=8 else nibble
                sample=((delta*(1<<shift)<<11)+coef1*hist1+coef2*hist2+1024)>>11
                sample=max(-32768,min(32767,sample))
                hist2,hist1=hist1,sample
                values.append(sample)
                if len(values)==sample_count:break
            if len(values)==sample_count:break
    return values

def decode_cwav(data):
    if (len(data)<64 or data[:6]!=b"CWAV\xff\xfe" or
        u16(data,6)!=64 or u32(data,12)!=len(data)):
        raise ValueError("original CWAV header invalid")
    info=reference(data,20,0x7000,0)
    block=reference(data,32,0x7001,0)
    if data[info:info+4]!=b"INFO" or data[block:block+4]!=b"DATA":
        raise ValueError("original CWAV INFO/DATA missing")
    if data[info+8]!=2 or data[info+9]!=0:
        raise ValueError("unsupported source codec/loop mode")
    rate=u32(data,info+12)
    samples=u32(data,info+20)
    channels=u32(data,info+28)
    if not 4000<=rate<=48000 or not 1<=channels<=2 or not 0<samples<=1000000:
        raise ValueError("unsupported source channel/rate/sample count")
    decoded=[]
    for i in range(channels):
        entry=reference(data,info+32+i*8,0x7100,info+28)
        audio_start=reference(data,entry,0x1f00,block+8)
        adpcm=reference(data,entry+8,0x0300,entry)
        if adpcm<info+8 or adpcm+0x2c>info+u32(data,info+4):
            raise ValueError("original source ADPCM parameters invalid")
        coeff=struct.unpack_from("<16h",data,adpcm)
        hist1,hist2=struct.unpack_from("<2h",data,adpcm+0x22)
        byte_count=((samples+13)//14)*8
        if audio_start<block+8 or audio_start+byte_count>block+u32(data,block+4):
            raise ValueError("original ADPCM sample frame outside DATA section")
        decoded.append(decode_dsp_adpcm(
            data[audio_start:audio_start+byte_count],coeff,samples,hist1,hist2))
    interleaved=[decoded[ch][i] for i in range(samples) for ch in range(channels)]
    return rate,channels,samples,struct.pack("<%dh"%len(interleaved),*interleaved)

def preview(private_archive,private_output_dir,max_files=5):
    if max_files<1 or max_files>100:
        raise ValueError("diagnostic batch must contain 1 to 100 original sounds")
    private_output_dir=Path(private_output_dir)
    private_output_dir.mkdir(parents=True,exist_ok=True)
    result=[]
    with zipfile.ZipFile(private_archive) as z:
        originals=[x for x in z.namelist() if x.startswith("original_audio/cwav/") and x.endswith(".cwav")]
        for i,name in enumerate(originals[:max_files]):
            rate,channels,samples,pcm=decode_cwav(z.read(name))
            path=private_output_dir/("original_audio_%03d.wav"%i)
            with wave.open(str(path),"wb") as w:
                w.setnchannels(channels);w.setsampwidth(2)
                w.setframerate(rate);w.writeframes(pcm)
            result.append({"source_private_member":name,"samples":samples,
                "sample_rate_hz":rate,"channels":channels,
                "decoded_pcm_sha256":hashlib.sha256(pcm).hexdigest(),
                "private_preview_path":str(path)})
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-original-audio-zip",type=Path,required=True)
    p.add_argument("--private-preview-dir",type=Path,required=True)
    p.add_argument("--max-files",type=int,default=5)
    args=p.parse_args()
    print(json.dumps(preview(args.private_original_audio_zip,
                              args.private_preview_dir,args.max_files),indent=2))
if __name__=="__main__":main()
