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
    if(fread(h,1,8,f)!=8||memcmp(h,"P3AN",4)!=0||(rd16(h+4)!=1&&rd16(h+4)!=2)||
       rd16(h+6)==0||rd16(h+6)>P3D_ANIMATION_MAX_FRAMES){fclose(f);return 0;}
    tmp.version=rd16(h+4);
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

/* DS fixed-angle rotations use 32768 units per turn. Cast only after
 * reducing the difference into the shortest signed half-circle; this
 * avoids discontinuities when interpolation crosses the rotation seam. */
static int16_t p3dInterpolateAngle(int16_t a,int16_t b,
                                  unsigned elapsed,unsigned duration){
    unsigned shortest=((unsigned)((int)b-(int)a)+16384u)&32767u;
    int delta=(int)shortest-16384;
    int value=(int)a+(int)((int32_t)delta*(int32_t)elapsed/(int32_t)duration);
    return (int16_t)(value&32767);
}
int p3dAnimationPoseAt(const P3DAnimationClip *clip,unsigned tick,
                       P3DAnimationFrame *pose){
    if(!pose||!clip||!clip->ready||!clip->count||
       clip->count>P3D_ANIMATION_MAX_FRAMES||!clip->total_ticks||
       (clip->version!=1&&clip->version!=2))return 0;
    tick%=clip->total_ticks;
    for(unsigned i=0;i<clip->count;i++){
        const P3DAnimationFrame *current=&clip->frames[i];
        if(!current->duration)return 0;
        if(tick<current->duration){
            *pose=*current;
            if(clip->version==2 && clip->count>1){
                const P3DAnimationFrame *next=&clip->frames[(i+1)%clip->count];
                pose->yaw=p3dInterpolateAngle(current->yaw,next->yaw,tick,current->duration);
                pose->pitch=p3dInterpolateAngle(current->pitch,next->pitch,tick,current->duration);
                pose->roll=p3dInterpolateAngle(current->roll,next->roll,tick,current->duration);
            }
            return 1;
        }
        tick-=current->duration;
    }
    return 0;
}
