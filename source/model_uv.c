#include "model_uv.h"
#include <stdio.h>
#include <string.h>

/* Decode 16 faces per NitroFS read instead of one fread for every UV word.
 * Keep the ARM9 stack bounded to 192 bytes and avoid partial visible state. */
#define P3D_UV_READ_BATCH_TRIANGLES 16u
static unsigned rd16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
int p3dUvLoad(P3DUvMap *map,const char *path,unsigned model_triangles){
 unsigned char h[8],batch[P3D_UV_READ_BATCH_TRIANGLES*12u];
 FILE *f; unsigned count;
 if(!map)return 0;
 /* No stale coordinates, triangle count, or readiness on any failure. */
 memset(map,0,sizeof(*map));
 if(!path||!model_triangles||model_triangles>P3D_UV_MAX_TRIANGLES)return 0;
 f=fopen(path,"rb");if(!f)return 0;
 if(fread(h,1,sizeof(h),f)!=sizeof(h)||memcmp(h,"P3UV",4)!=0||rd16(h+4)!=1)
   goto fail;
 count=rd16(h+6);
 if(count!=model_triangles)goto fail;
 for(unsigned first=0;first<count;first+=P3D_UV_READ_BATCH_TRIANGLES){
   unsigned take=count-first;
   if(take>P3D_UV_READ_BATCH_TRIANGLES)take=P3D_UV_READ_BATCH_TRIANGLES;
   if(fread(batch,1,take*12u,f)!=take*12u)goto fail;
   for(unsigned j=0;j<take*6u;j++)
     map->uv[first*6u+j]=(int16_t)rd16(batch+j*2u);
 }
 if(fgetc(f)!=EOF||ferror(f))goto fail;
 if(fclose(f)!=0){memset(map,0,sizeof(*map));return 0;}
 map->triangles=count;map->ready=1;return 1;
fail:
 fclose(f);
 memset(map,0,sizeof(*map));
 return 0;
}
