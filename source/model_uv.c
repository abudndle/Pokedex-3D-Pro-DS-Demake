#include "model_uv.h"
#include <stdio.h>
#include <string.h>
static unsigned rd16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
int p3dUvLoad(P3DUvMap *map,const char *path,unsigned model_triangles){
 unsigned char h[8],b[2];
 FILE *f; unsigned count;
 if(!map)return 0;
 /* A failed or truncated load must not expose stale UVs from a previous model. */
 map->ready=0;
 map->triangles=0;
 if(!path||!model_triangles||model_triangles>P3D_UV_MAX_TRIANGLES)return 0;
 f=fopen(path,"rb");if(!f)return 0;
 if(fread(h,1,8,f)!=8||memcmp(h,"P3UV",4)!=0||rd16(h+4)!=1){
   fclose(f);return 0;
 }
 count=rd16(h+6);
 if(count!=model_triangles){fclose(f);return 0;}
 for(unsigned i=0;i<count*6;i++){
   if(fread(b,1,2,f)!=2){fclose(f);return 0;}
   map->uv[i]=(int16_t)rd16(b);
 }
 if(fgetc(f)!=EOF){fclose(f);return 0;}
 fclose(f);map->triangles=count;map->ready=1;return 1;
}
