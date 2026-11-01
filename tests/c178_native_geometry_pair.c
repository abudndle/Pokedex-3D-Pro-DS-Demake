#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "verified_geometry_pair.h"
static P3DVerifiedGeometryPair pair;
static void wr16(uint8_t *p,uint16_t n){p[0]=(uint8_t)n;p[1]=(uint8_t)(n>>8);}
static void wr32(uint8_t *p,uint32_t n){wr16(p,(uint16_t)n);wr16(p+2,(uint16_t)(n>>16));}
static uint32_t crc32_bytes(const uint8_t *p,size_t n){
    uint32_t crc=0xffffffffu;
    for(size_t i=0;i<n;i++){
        crc^=p[i];
        for(unsigned j=0;j<8;j++)crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
    }
    return crc^0xffffffffu;
}
static void write_file(const char *path,const uint8_t *data,size_t size){
    FILE *f=fopen(path,"wb");assert(f);
    assert(fwrite(data,1,size,f)==size);assert(fclose(f)==0);
}
int main(int argc,char **argv){
    assert(argc==3);
    uint8_t vx[16+8+18]={0};
    uint8_t ix[]={ 'P','3','I','X',1,0,14,0,1,0,
                   7,0,1,0,0,0,0,0,1,0,2,0 };
    memcpy(vx,"P3VX",4);wr16(vx+4,1);wr16(vx+6,14);
    wr16(vx+8,1);wr16(vx+16,7);wr16(vx+18,3);
    for(unsigned i=0;i<9;i++)wr16(vx+24+i*2,(uint16_t)(i*11));
    wr32(vx+12,crc32_bytes(vx+16,sizeof(vx)-16));
    write_file(argv[1],vx,sizeof(vx));write_file(argv[2],ix,sizeof(ix));
    assert(p3dVerifiedGeometryPairLoad(&pair,argv[1],argv[2],14));
    assert(pair.ready&&pair.mesh_count==1&&pair.triangles==1);
    assert(pair.meshes[0].mesh_id==7&&pair.meshes[0].xyz==pair.xyz);
    assert(pair.xyz[8]==88);
    /* Bad index must invalidate previously loaded geometry, not reuse it. */
    ix[20]=3;write_file(argv[2],ix,sizeof(ix));
    assert(!p3dVerifiedGeometryPairLoad(&pair,argv[1],argv[2],14));
    assert(!pair.ready&&!pair.mesh_count&&!pair.triangles);
    ix[20]=2;write_file(argv[2],ix,sizeof(ix));
    assert(!p3dVerifiedGeometryPairLoad(&pair,argv[1],argv[2],15));
    assert(!pair.ready);
    vx[sizeof(vx)-1]^=1;write_file(argv[1],vx,sizeof(vx));
    assert(!p3dVerifiedGeometryPairLoad(&pair,argv[1],argv[2],14));
    assert(!pair.ready);
    vx[sizeof(vx)-1]^=1;write_file(argv[1],vx,sizeof(vx));
    assert(p3dVerifiedGeometryPairLoad(&pair,argv[1],argv[2],14));
    assert(!p3dVerifiedGeometryPairLoad(&pair,"/missing/p3vx",argv[2],14));
    assert(!pair.ready);
    return 0;
}
