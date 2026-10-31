#include "model_animation.h"
#include <stdio.h>
#include <string.h>
static unsigned rd16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
int p3dAnimationLoad(P3DAnimationClip *clip,const char *path){
    unsigned char h[8],b[8]; P3DAnimationClip tmp={0}; FILE *f;
    if(!clip)return 0;
    clip->ready=0;
    if(!path)return 0;
    f=fopen(path,"rb");if(!f)return 0;
    if(fread(h,1,8,f)!=8||memcmp(h,"P3AN",4)!=0||rd16(h+4)!=1||
       rd16(h+6)==0||rd16(h+6)>P3D_ANIMATION_MAX_FRAMES){fclose(f);return 0;}
    tmp.count=rd16(h+6);
    for(unsigned i=0;i<tmp.count;i++){
        if(fread(b,1,8,f)!=8){fclose(f);return 0;}
        tmp.frames[i].yaw=(int16_t)rd16(b);
        tmp.frames[i].pitch=(int16_t)rd16(b+2);
        tmp.frames[i].roll=(int16_t)rd16(b+4);
        tmp.frames[i].duration=(uint16_t)rd16(b+6);
        if(!tmp.frames[i].duration){fclose(f);return 0;}
        tmp.total_ticks+=tmp.frames[i].duration;
    }
    if(fgetc(f)!=EOF){fclose(f);return 0;}
    fclose(f);tmp.ready=1;*clip=tmp;return 1;
}
int p3dAnimationFrameAt(const P3DAnimationClip *clip,unsigned tick){
    if(!clip||!clip->ready||!clip->count||!clip->total_ticks)return -1;
    tick%=clip->total_ticks;
    for(unsigned i=0;i<clip->count;i++){
        if(tick<clip->frames[i].duration)return (int)i;
        tick-=clip->frames[i].duration;
    }
    return -1;
}
