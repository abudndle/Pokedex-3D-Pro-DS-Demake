#include "title_audio.h"
#include <stdio.h>
#include <string.h>
static unsigned rd16(const unsigned char *p){
    return (unsigned)p[0]|((unsigned)p[1]<<8);
}
static uint32_t rd32(const unsigned char *p){
    return (uint32_t)rd16(p)|((uint32_t)rd16(p+2)<<16);
}
static uint32_t crc32_buf(const unsigned char *p,unsigned len){
    uint32_t crc=0xffffffffu;
    for(unsigned i=0;i<len;i++){
        crc^=p[i];
        for(unsigned j=0;j<8;j++)
            crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
    }
    return crc^0xffffffffu;
}
int p3dTitleCuesLoad(P3DTitleCues *out,const char *path,
                     unsigned expected_frames){
    unsigned char data[16+P3D_TITLE_AUDIO_MAX_FRAMES*4u];
    unsigned size,frames,count;
    FILE *f;
    if(!out)return 0;
    memset(out,0,sizeof(*out));
    if(!path||expected_frames<1||expected_frames>P3D_TITLE_AUDIO_MAX_FRAMES)
        return 0;
    f=fopen(path,"rb");
    if(!f)return 0;
    size=(unsigned)fread(data,1,sizeof(data),f);
    if(ferror(f)||fgetc(f)!=EOF){fclose(f);return 0;}
    fclose(f);
    if(size<20||memcmp(data,"P3TC",4)!=0||rd16(data+4)!=1||
       rd16(data+10)!=0)return 0;
    frames=rd16(data+6);count=rd16(data+8);
    if(frames!=expected_frames||count<1||count>frames||
       size!=16+count*4u||
       rd32(data+12)!=crc32_buf(data+16,count*4u))
        return 0;
    for(unsigned i=0;i<count;i++){
        unsigned frame=rd16(data+16+i*4u);
        unsigned cue=rd16(data+18+i*4u);
        if(frame>=frames||cue<1||cue>P3D_TITLE_AUDIO_MAX_FRAMES||
           (i>0 && frame<=rd16(data+12+i*4u))){
            memset(out,0,sizeof(*out));
            return 0;
        }
        out->cue[frame]=(uint8_t)cue;
    }
    out->frames=(uint8_t)frames;
    out->ready=1;
    return 1;
}
unsigned p3dTitleCueForFrame(const P3DTitleCues *cues,unsigned frame){
    if(!cues||!cues->ready||frame>=cues->frames)return 0;
    return cues->cue[frame];
}
int p3dTitleAudioLoad(P3DTitleAudio *out,const char *path){
    unsigned char header[16];
    unsigned rate,samples;
    FILE *f;
    if(!out)return 0;
    out->ready=0;out->sample_count=0;out->rate=0;
    if(!path)return 0;
    f=fopen(path,"rb");
    if(!f)return 0;
    if(fread(header,1,sizeof(header),f)!=sizeof(header)||
       memcmp(header,"P3SA",4)!=0||rd16(header+4)!=1)
        goto fail;
    rate=rd16(header+6);samples=(unsigned)rd32(header+8);
    if(rate<8000||rate>32000||samples<1||
       samples>P3D_TITLE_AUDIO_MAX_SAMPLES)goto fail;
    if(fread(out->pcm,2,samples,f)!=samples ||
       fgetc(f)!=EOF||ferror(f)||
       crc32_buf((const unsigned char *)out->pcm,samples*2u)!=rd32(header+12))
        goto fail;
    fclose(f);
    out->sample_count=samples;
    out->rate=(uint16_t)rate;
    out->ready=1;
    return 1;
fail:
    fclose(f);
    out->sample_count=0;out->rate=0;
    return 0;
}
