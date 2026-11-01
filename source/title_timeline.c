#include "title_timeline.h"
#include <stdio.h>
#include <string.h>
static unsigned le16(const unsigned char *p){
    return (unsigned)p[0]|((unsigned)p[1]<<8);
}
static unsigned le32(const unsigned char *p){
    return le16(p)|(le16(p+2)<<16);
}
static unsigned crc32_bytes(const unsigned char *data,unsigned length){
    unsigned crc=0xffffffffu;
    for(unsigned i=0;i<length;i++){
        crc^=data[i];
        for(unsigned bit=0;bit<8;bit++)
            crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
    }
    return crc^0xffffffffu;
}
int p3dTitleTimelineLoad(P3DTitleTimeline *out,const char *path){
    unsigned char bytes[16+4*P3D_TITLE_MAX_FRAMES];
    unsigned count,flags,size;
    FILE *f;
    if(!out)return 0;
    memset(out,0,sizeof(*out));
    if(!path)return 0;
    f=fopen(path,"rb");
    if(!f)return 0;
    size=(unsigned)fread(bytes,1,sizeof(bytes),f);
    if(ferror(f)||fgetc(f)!=EOF){fclose(f);return 0;}
    fclose(f);
    if(size<20||memcmp(bytes,"P3TL",4)!=0||le16(bytes+4)!=1)
        return 0;
    count=le16(bytes+6);flags=le16(bytes+8);
    if(count<2||count>P3D_TITLE_MAX_FRAMES||flags>1||
       le16(bytes+10)!=0||size!=16+4*count||
       le32(bytes+12)!=crc32_bytes(bytes+16,4*count))
        return 0;
    for(unsigned i=0;i<count;i++){
        unsigned frame=le16(bytes+16+i*4);
        unsigned ticks=le16(bytes+18+i*4);
        if(frame!=i||ticks<1||ticks>3600)return 0;
        out->ticks[i]=(uint16_t)ticks;
    }
    out->frames=(uint16_t)count;
    out->loop=(uint8_t)flags;
    out->ready=1;
    return 1;
}
int p3dTitleTimelineAdvance(P3DTitleTimeline *out){
    if(!out||!out->ready||out->current>=out->frames)return -1;
    if(++out->elapsed<out->ticks[out->current])return -1;
    out->elapsed=0;
    if(out->current+1<out->frames){
        out->current++;
    }else if(out->loop){
        out->current=0;
    }else{
        /* Hold final frame, never make up an exit/transition animation. */
        out->elapsed=out->ticks[out->current];
        return -1;
    }
    return (int)out->current;
}
