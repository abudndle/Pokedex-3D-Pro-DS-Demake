#include "source_material_map.h"
#include <stdio.h>
#include <string.h>
#define HEADER_BYTES 16u
#define RANGE_BYTES 12u
static unsigned rd16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
static unsigned rd32(const unsigned char *p){return rd16(p)|(rd16(p+2)<<16);}
static unsigned crc32_data(const unsigned char *p,unsigned n){
    unsigned c=0xffffffffu;
    for(unsigned i=0;i<n;i++){
        c^=p[i];
        for(unsigned bit=0;bit<8;bit++)c=(c>>1)^((c&1u)?0xedb88320u:0u);
    }
    return c^0xffffffffu;
}
int p3dSourceMaterialLoad(P3DSourceMaterialMap *out,const char *path,
                          unsigned expected_model_id,unsigned expected_triangles){
    unsigned char b[HEADER_BYTES+RANGE_BYTES*P3D_SOURCE_MATERIAL_MAX_RANGES];
    unsigned got,tri,count,cursor=0;
    FILE *f;
    if(!out)return 0;
    memset(out,0,sizeof(*out));
    if(!path||expected_model_id>=738||!expected_triangles||expected_triangles>600)return 0;
    f=fopen(path,"rb");if(!f)return 0;
    got=(unsigned)fread(b,1,sizeof(b),f);
    if(ferror(f)||fgetc(f)!=EOF){fclose(f);return 0;}
    fclose(f);
    if(got<HEADER_BYTES||memcmp(b,"P3MR",4)!=0||rd16(b+4)!=1||
       rd16(b+6)!=expected_model_id||rd16(b+8)!=expected_triangles)return 0;
    tri=rd16(b+8);count=rd16(b+10);
    if(!count||count>P3D_SOURCE_MATERIAL_MAX_RANGES||
       got!=HEADER_BYTES+count*RANGE_BYTES||
       rd32(b+12)!=crc32_data(b+HEADER_BYTES,count*RANGE_BYTES))return 0;
    for(unsigned i=0;i<count;i++){
        unsigned p=HEADER_BYTES+i*RANGE_BYTES;
        P3DSourceMaterialRange *r=&out->ranges[i];
        r->first_triangle=(uint16_t)rd16(b+p);
        r->triangle_count=(uint16_t)rd16(b+p+2);
        r->material_index=(uint16_t)rd16(b+p+4);
        r->source_texture0=(uint16_t)rd16(b+p+6);
        r->source_texture1=(uint16_t)rd16(b+p+8);
        r->source_pass=(uint16_t)rd16(b+p+10);
        if(r->source_pass!=0x0c02u||r->material_index>255u||
           !r->triangle_count||r->first_triangle!=cursor||
           r->triangle_count>tri-cursor)return 0;
        cursor+=r->triangle_count;
    }
    if(cursor!=tri)return 0;
    out->model_id=(uint16_t)expected_model_id;
    out->triangle_count=(uint16_t)tri;
    out->count=(uint16_t)count;
    out->ready=1;
    return 1;
}
