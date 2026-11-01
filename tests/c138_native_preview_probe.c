/* C138: run the EXACT native previewStreamLoad/Draw path under host nds.h.
 * No original asset bytes are embedded. Driver receives local/private NitroFS.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "preview_stream.h"

#define MAX_TRI 600
static int16_t expected_xyz[MAX_TRI*9];
static int16_t expected_uv[MAX_TRI*6];
static unsigned char expected_rgb[MAX_TRI*3];
static int expected_xyz_words,expected_uv_words;
static int vertex_calls,uv_calls,color_calls,failed;

void glBegin(int mode){if(mode!=1)failed=1;}
void glEnd(void){}
void glColor3b(unsigned char r,unsigned char g,unsigned char b){
    if(color_calls==0){
        if(r!=192||g!=224||b!=232)failed=1;
    }else{
        int at=(color_calls-1)*3;
        if(at+2>=MAX_TRI*3||r!=expected_rgb[at]||
           g!=expected_rgb[at+1]||b!=expected_rgb[at+2])failed=1;
    }
    color_calls++;
}
void glVertex3v16(short x,short y,short z){
    int at=vertex_calls*3;
    if(at+2>=expected_xyz_words||x!=expected_xyz[at]||
       y!=expected_xyz[at+1]||z!=expected_xyz[at+2])failed=1;
    vertex_calls++;
}
void glTexCoord2t16(short u,short v){
    int at=uv_calls*2;
    if(at+1>=expected_uv_words||u!=expected_uv[at]||v!=expected_uv[at+1])failed=1;
    uv_calls++;
}
static unsigned read16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
static unsigned read32(const unsigned char *p){return read16(p)|(read16(p+2)<<16);}

int main(int argc,char **argv){
    if(argc!=2){fputs("usage: c138_probe <expected_uv_count>\n",stderr);return 2;}
    const int expected_uv_count=atoi(argv[1]);
    if(expected_uv_count!=0&&expected_uv_count!=49){fputs("expected UV count must be 0 or 49\n",stderr);return 2;}
    if(!previewStreamInit()){fputs("previewStreamInit failed\n",stderr);return 1;}
    int loaded=0, paired=0;
    for(int id=0;id<734;id++){
        if(id>=721&&id<=724)continue;
        char filename[96];
        if(snprintf(filename,sizeof(filename),"nitrofs/preview/p%03d.ds3m",id)>= (int)sizeof(filename))return 1;
        FILE *f=fopen(filename,"rb");
        if(!f){fprintf(stderr,"missing DS3M p%03d\n",id);return 1;}
        unsigned char header[16];
        if(fread(header,1,16,f)!=16||memcmp(header,"DS3M",4)||read16(header+4)!=2||
           read32(header+8)!=0){fprintf(stderr,"invalid native DS3M header p%03d\n",id);fclose(f);return 1;}
        unsigned tri=read16(header+6),original=read32(header+12);
        if(tri<1||tri>MAX_TRI||original<tri||original>0x7fffffff){
            fprintf(stderr,"invalid triangle count p%03d\n",id);fclose(f);return 1;
        }
        expected_xyz_words=(int)tri*9;
        if(fread(expected_xyz,sizeof(expected_xyz[0]),(size_t)expected_xyz_words,f)!=(size_t)expected_xyz_words ||
           fread(expected_rgb,3,tri,f)!=(size_t)tri || fgetc(f)!=EOF){fclose(f);return 1;}
        fclose(f);
        if(!previewStreamLoad(id)||previewStreamIsChunked()||!previewStreamHasModel()||
           previewStreamTriangleCount()!=(int)tri||previewStreamOriginalTriangleCount()!=(int)original){
            fprintf(stderr,"native previewStreamLoad mismatch p%03d\n",id);return 1;
        }
        const int has_uv=previewStreamHasUv();
        expected_uv_words=0;
        if(has_uv){
            if(snprintf(filename,sizeof(filename),"nitrofs/preview/p%03d.p3uv",id)>=(int)sizeof(filename))return 1;
            f=fopen(filename,"rb");
            unsigned char h[8];
            if(!f||fread(h,1,8,f)!=8||memcmp(h,"P3UV",4)||read16(h+4)!=1||read16(h+6)!=tri){
                fprintf(stderr,"invalid UV companion p%03d\n",id);if(f)fclose(f);return 1;
            }
            expected_uv_words=(int)tri*6;
            if(fread(expected_uv,sizeof(expected_uv[0]),(size_t)expected_uv_words,f)!=(size_t)expected_uv_words){fclose(f);return 1;}
            fclose(f);
            if(!previewStreamUvRangeUnit(0,(int)tri)){
                fprintf(stderr,"nonunit UV accepted p%03d\n",id);return 1;
            }
            paired++;
        }
        vertex_calls=uv_calls=color_calls=failed=0;
        previewStreamDraw();
        if(failed||color_calls!=(int)(tri+1)||vertex_calls!=(int)(tri*3)||
           uv_calls!=(has_uv?(int)(tri*3):0)){
            fprintf(stderr,"native GL emission differs from source geometry p%03d: vertices=%d expected=%u uv=%d\n",
                    id,vertex_calls,tri*3,uv_calls);
            return 1;
        }
        loaded++;
    }
    for(int id=721;id<=724;id++){
        if(previewStreamLoad(id)||previewStreamHasModel()){
            fprintf(stderr,"unexpected source model p%03d\n",id);return 1;
        }
    }
    if(loaded!=730||paired!=expected_uv_count){
        fprintf(stderr,"unexpected coverage loaded=%d uv=%d expected_uv=%d\n",loaded,paired,expected_uv_count);
        return 1;
    }
    printf("C138 native preview loader: PASS 730/730 models; UV %d; exact XYZ/RGB/UV GL emission matched\n",paired);
    return 0;
}