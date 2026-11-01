#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include "verified_vertex_stream.h"
#include "verified_primitive_bridge.h"
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
static int accept(void *ctx,uint16_t mesh,const int16_t *a,
                  const int16_t *b,const int16_t *c){
    unsigned *seen=(unsigned *)ctx;
    assert(mesh==7||mesh==9);
    assert(a[0]!=b[0]&&b[0]!=c[0]);
    (*seen)++;
    return 1;
}
static void checksum(uint8_t *file,size_t len){
    wr32(file+12,crc32_bytes(file+16,len-16));
}
int main(void){
    /* Two distinct original-style meshes, three vertices each, one triangle
     * per mesh. These are synthetic transport fixtures, not game assets. */
    uint8_t file[16+16+6*6]={0};
    int16_t xyz[18];
    P3DPrimitiveVertices meshes[2];
    size_t count=99;
    uint32_t emitted=0;
    unsigned seen=0;
    memcpy(file,"P3VX",4);wr16(file+4,1);wr16(file+6,0);
    wr16(file+8,2);wr16(file+10,0);
    wr16(file+16,7);wr16(file+18,3);wr32(file+20,0);
    wr16(file+24,9);wr16(file+26,3);wr32(file+28,3);
    for(unsigned i=0;i<18;i++)wr16(file+32+i*2,(uint16_t)(100+i*10));
    checksum(file,sizeof(file));
    assert(p3dVerifiedVerticesDecode(file,sizeof(file),0,meshes,2,xyz,18,&count));
    assert(count==2&&meshes[0].mesh_id==7&&meshes[1].mesh_id==9);
    assert(meshes[0].xyz==xyz&&meshes[1].xyz==xyz+9);
    assert(xyz[0]==100&&xyz[9]==190&&xyz[17]==270);
    const uint8_t index[]={
        'P','3','I','X',1,0,0,0,2,0,
        7,0,1,0,0,0,0,0,1,0,2,0,
        9,0,1,0,0,0,0,0,1,0,2,0};
    assert(p3dVerifiedPrimitiveBridge(index,sizeof(index),0,meshes,2,
                                       accept,&seen,&emitted));
    assert(seen==2&&emitted==2);
    /* Fail-closed: no output data changes even for valid-CRC malformed rows. */
    int16_t snapshot[18];memcpy(snapshot,xyz,sizeof(xyz));
    uint16_t prior=meshes[0].mesh_id;
    file[sizeof(file)-1]^=0x80;
    assert(!p3dVerifiedVerticesDecode(file,sizeof(file),0,meshes,2,xyz,18,&count));
    assert(count==0&&memcmp(snapshot,xyz,sizeof(xyz))==0&&meshes[0].mesh_id==prior);
    file[sizeof(file)-1]^=0x80;
    wr32(file+28,2);checksum(file,sizeof(file));
    assert(!p3dVerifiedVerticesDecode(file,sizeof(file),0,meshes,2,xyz,18,&count));
    wr32(file+28,3);checksum(file,sizeof(file));
    assert(!p3dVerifiedVerticesDecode(file,sizeof(file)-1,0,meshes,2,xyz,18,&count));
    assert(!p3dVerifiedVerticesDecode(file,sizeof(file),1,meshes,2,xyz,18,&count));
    assert(!p3dVerifiedVerticesDecode(file,sizeof(file),0,meshes,1,xyz,18,&count));
    assert(!p3dVerifiedVerticesDecode(file,sizeof(file),0,meshes,2,xyz,17,&count));
    wr16(file+24,7);checksum(file,sizeof(file));
    assert(!p3dVerifiedVerticesDecode(file,sizeof(file),0,meshes,2,xyz,18,&count));
    return 0;
}
