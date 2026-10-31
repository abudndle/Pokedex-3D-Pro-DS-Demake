#include "bmp_loader.h"
#include <stdio.h>
#include <stdint.h>
static unsigned rd16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
static uint32_t rd32(const unsigned char *p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
int p3dBmpDecode24(const char *path,uint16_t *pixels,size_t capacity,int *out_width,int *out_height){
 unsigned char h[54],bgr[3];FILE *f;uint32_t offset,header,w,raw_h;int height,top_down;
 if(!path||!pixels||!out_width||!out_height)return 0;
 f=fopen(path,"rb");if(!f)return 0;
 if(fread(h,1,54,f)!=54||h[0]!='B'||h[1]!='M'){fclose(f);return 0;}
 offset=rd32(h+10);header=rd32(h+14);w=rd32(h+18);raw_h=rd32(h+22);
 if(header!=40||w==0||w>256||raw_h==0||raw_h==0x80000000u||rd16(h+26)!=1||
 rd16(h+28)!=24||rd32(h+30)!=0||offset<54){fclose(f);return 0;}
 top_down=(raw_h&0x80000000u)!=0;
 height=top_down?(int)(0u-raw_h):(int)raw_h;
 if(height>192||(size_t)w*(size_t)height>capacity){fclose(f);return 0;}
 unsigned rowbytes=(unsigned)(((w*3u)+3u)&~3u);
 for(int y=0;y<height;y++){
  int src_y=top_down?y:height-1-y;
  long position=(long)offset+(long)rowbytes*src_y;
  if(fseek(f,position,SEEK_SET)!=0){fclose(f);return 0;}
  for(uint32_t x=0;x<w;x++){
   if(fread(bgr,1,3,f)!=3){fclose(f);return 0;}
   pixels[(size_t)y*w+x]=(uint16_t)(0x8000u|((bgr[2]>>3)<<10)|((bgr[1]>>3)<<5)|(bgr[0]>>3));
  }
 }
 fclose(f);*out_width=(int)w;*out_height=height;return 1;
}
