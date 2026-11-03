#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "verified_geometry_pair.h"
#include "verified_vertex_uv.h"
static P3DVerifiedGeometryPair g;
static P3DVerifiedVertexUv uv;
static uint8_t vx[16+8+18];
static uint8_t ix[]={ 'P','3','I','X',1,0,14,0,1,0,
                      7,0,1,0,0,0,0,0,1,0,2,0 };
static uint8_t vu[20+8+12];
static void wr16(uint8_t *p,uint16_t n){p[0]=(uint8_t)n;p[1]=(uint8_t)(n>>8);}
static void wr32(uint8_t *p,uint32_t n){wr16(p,(uint16_t)n);wr16(p+2,(uint16_t)(n>>16));}
static uint32_t crc(const uint8_t *p,size_t n){
    uint32_t c=0xffffffffu;
    for(size_t i=0;i<n;i++){
        c^=p[i];for(unsigned j=0;j<8;j++)c=(c>>1)^((c&1u)?0xedb88320u:0u);
    }
    return c^0xffffffffu;
}
static void write_file(const char *path,const void *data,size_t n){
    FILE *f=fopen(path,"wb");assert(f);assert(fwrite(data,1,n,f)==n);assert(!fclose(f));
}
static void refresh_vu(void){wr32(vu+16,crc(vu+20,sizeof(vu)-20));}
static void denied(const char *path){
    int16_t u=999,v=999;
    memset(&uv,0xa5,sizeof(uv));
    assert(!p3dVerifiedVertexUvLoad(&uv,path,&g));
    const uint8_t *p=(const uint8_t *)&uv;
    for(size_t i=0;i<sizeof(uv);i++)assert(p[i]==0);
    assert(!p3dVerifiedVertexUvGet(&uv,0,0,&u,&v));
    assert(u==999&&v==999);
}
int main(int argc,char **argv){
    int16_t u=0,v=0;
    assert(argc==4);
    memcpy(vx,"P3VX",4);wr16(vx+4,1);wr16(vx+6,14);
    wr16(vx+8,1);wr16(vx+16,7);wr16(vx+18,3);
    for(unsigned i=0;i<9;i++)wr16(vx+24+i*2,(uint16_t)(i*11));
    wr32(vx+12,crc(vx+16,sizeof(vx)-16));
    write_file(argv[1],vx,sizeof(vx));write_file(argv[2],ix,sizeof(ix));
    assert(p3dVerifiedGeometryPairLoad(&g,argv[1],argv[2],14));
    assert(g.vx_size==sizeof(vx));
    memcpy(vu,"P3VU",4);wr16(vu+4,1);wr16(vu+6,14);wr16(vu+8,1);
    wr32(vu+12,crc(vx,sizeof(vx)));wr16(vu+20,7);wr16(vu+22,3);
    wr16(vu+28,0);wr16(vu+30,0);
    wr16(vu+32,4096);wr16(vu+34,0);
    wr16(vu+36,0);wr16(vu+38,4096);refresh_vu();
    write_file(argv[3],vu,sizeof(vu));
    assert(p3dVerifiedVertexUvLoad(&uv,argv[3],&g));
    assert(uv.ready&&uv.model==14&&uv.mesh_count==1&&uv.vertex_count==3);
    assert(p3dVerifiedVertexUvGet(&uv,0,1,&u,&v)&&u==4096&&v==0);
    assert(!p3dVerifiedVertexUvGet(&uv,0,3,&u,&v));
    assert(!p3dVerifiedVertexUvGet(&uv,1,0,&u,&v));
    assert(!p3dVerifiedVertexUvGet(&uv,0,0,NULL,&v));
    assert(u==4096&&v==0);
    /* Exact byte identity of the original vertex transport is required. */
    wr32(vu+12,0);write_file(argv[3],vu,sizeof(vu));denied(argv[3]);
    wr32(vu+12,crc(vx,sizeof(vx)));
    wr16(vu+6,15);refresh_vu();write_file(argv[3],vu,sizeof(vu));denied(argv[3]);
    wr16(vu+6,14);wr16(vu+20,8);refresh_vu();write_file(argv[3],vu,sizeof(vu));denied(argv[3]);
    wr16(vu+20,7);wr32(vu+24,1);refresh_vu();write_file(argv[3],vu,sizeof(vu));denied(argv[3]);
    wr32(vu+24,0);wr16(vu+22,2);refresh_vu();write_file(argv[3],vu,sizeof(vu));denied(argv[3]);
    wr16(vu+22,3);wr16(vu+32,4097);refresh_vu();write_file(argv[3],vu,sizeof(vu));denied(argv[3]);
    wr16(vu+32,4096);refresh_vu();write_file(argv[3],vu,sizeof(vu));
    assert(p3dVerifiedVertexUvLoad(&uv,argv[3],&g));
    vu[38]^=1;write_file(argv[3],vu,sizeof(vu));denied(argv[3]);
    vu[38]^=1;refresh_vu();write_file(argv[3],vu,sizeof(vu)-1);denied(argv[3]);
    write_file(argv[3],vu,sizeof(vu));
    FILE *f=fopen(argv[3],"ab");assert(f);assert(fputc(0,f)!=EOF);assert(!fclose(f));
    denied(argv[3]);
    denied("/nonexistent/source.p3vu");
    p3dVerifiedGeometryPairClear(&g);
    write_file(argv[3],vu,sizeof(vu));denied(argv[3]);
    puts("C289: CRC-bound native per-vertex UV staging (synthetic): PASS");
    return 0;
}
