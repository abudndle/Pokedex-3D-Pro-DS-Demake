#include "model_materials.h"
#include <stdio.h>
#include <string.h>
static unsigned rd16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
int p3dMaterialMapLoad(P3DMaterialMap *map,const char *path,unsigned model_triangles){
 unsigned char h[8],b[8];P3DMaterialMap tmp={0};FILE *f;
 if(!map)return 0;
 map->ready=0;
 if(!path||model_triangles==0||model_triangles>600)return 0;
 f=fopen(path,"rb");if(!f)return 0;
 if(fread(h,1,8,f)!=8||memcmp(h,"P3MT",4)!=0||rd16(h+4)!=1||
    rd16(h+6)==0||rd16(h+6)>P3D_MATERIAL_MAX){fclose(f);return 0;}
 tmp.count=rd16(h+6);
 unsigned cursor=0;
 for(unsigned i=0;i<tmp.count;i++){
   if(fread(b,1,8,f)!=8){fclose(f);return 0;}
   P3DMaterialRange *r=&tmp.ranges[i];
   r->first_triangle=(uint16_t)rd16(b);
   r->triangle_count=(uint16_t)rd16(b+2);
   r->material_id=(uint16_t)rd16(b+4);
   r->texture_id=(uint16_t)rd16(b+6);
   if(!r->triangle_count||r->first_triangle!=cursor||
      r->triangle_count>model_triangles-cursor){fclose(f);return 0;}
   cursor+=r->triangle_count;
 }
 if(cursor!=model_triangles||fgetc(f)!=EOF){fclose(f);return 0;}
 fclose(f);tmp.ready=1;*map=tmp;return 1;
}
int p3dMaterialForTriangle(const P3DMaterialMap *map,unsigned triangle){
 if(!map||!map->ready)return -1;
 for(unsigned i=0;i<map->count;i++){
   const P3DMaterialRange *r=&map->ranges[i];
   if(triangle>=r->first_triangle &&
      triangle-(unsigned)r->first_triangle<r->triangle_count)return (int)r->material_id;
 }
 return -1;
}
