#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "verified_geometry_pair.h"
#include "verified_vertex_uv.h"
#include "verified_primitive_uv_bridge.h"
static P3DVerifiedGeometryPair g;
static P3DVerifiedVertexUv uv;
static uint8_t vx[16+8+18];
static uint8_t ix[]={ 'P','3','I','X',1,0,14,0,1,0,
                      7,0,1,0,0,0,0,0,1,0,2,0 };
static uint8_t vu[20+8+12];

static unsigned uv_triangles;
static int uv_sink(void *ctx,uint16_t mesh,
    const P3DPrimitiveUvVertex *a,const P3DPrimitiveUvVertex *b,
    const P3DPrimitiveUvVertex *c){
    (void)ctx;
    assert(mesh==7);
    assert(a->u==0&&a->v==0);
    assert(b->u==4096&&b->v==0);
    assert(c->u==0&&c->v==4096);
    assert(a->xyz==g.xyz&&b->xyz==g.xyz+3&&c->xyz==g.xyz+6);
    uv_triangles++;
    return 1;
}

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
    /* Getter must reject damaged in-memory metadata without touching outputs. */
    {size_t original=uv.size;uv.size=20;
     assert(!p3dVerifiedVertexUvGet(&uv,0,1,&u,&v));
     assert(u==4096&&v==0);uv.size=original;}
    {unsigned original=uv.mesh_count;uv.mesh_count=P3D_VERTEX_MAX_MESHES+1u;
     assert(!p3dVerifiedVertexUvGet(&uv,0,1,&u,&v));
     assert(u==4096&&v==0);uv.mesh_count=original;}
    assert(u==4096&&v==0);
    {uint32_t first=0;memcpy(&first,uv.bytes+24,4);
     uv.bytes[24]=0xff;uv.bytes[25]=0xff;uv.bytes[26]=0xff;uv.bytes[27]=0xff;
     assert(!p3dVerifiedVertexUvGet(&uv,0,1,&u,&v));
     assert(u==4096&&v==0);
     uv.bytes[24]=(uint8_t)first;uv.bytes[25]=(uint8_t)(first>>8);
     uv.bytes[26]=(uint8_t)(first>>16);uv.bytes[27]=(uint8_t)(first>>24);}
    /* C295: in-range edits still invalidate the signed payload CRC. */
    {uint8_t original=uv.bytes[28];uv.bytes[28]=1;
     assert(!p3dVerifiedVertexUvGet(&uv,0,0,&u,&v));
     assert(u==4096&&v==0);uv.bytes[28]=original;}
    {uint8_t original=uv.bytes[20];uv.bytes[20]=8;
     assert(!p3dVerifiedVertexUvGet(&uv,0,1,&u,&v));
     assert(u==4096&&v==0);uv.bytes[20]=original;}
    assert(p3dVerifiedVertexUvGet(&uv,0,1,&u,&v));
    /* C294: a UV read is valid only for the exact live geometry. */
    assert(p3dVerifiedVertexUvGetPaired(&uv,&g,0,1,&u,&v));
    /* C298: renderer receives verified XYZ and paired UV per triangle. */
    uv_triangles=0;
    assert(p3dVerifiedPrimitiveUvBridge(&g,&uv,uv_sink,NULL));
    assert(uv_triangles==1);

    {uint8_t original=g.vx[24];g.vx[24]^=1;
     assert(!p3dVerifiedVertexUvGetPaired(&uv,&g,0,1,&u,&v));
     assert(u==4096&&v==0);g.vx[24]=original;}
    {uint16_t original=g.model;g.model=15;
     assert(!p3dVerifiedVertexUvGetPaired(&uv,&g,0,1,&u,&v));
     assert(u==4096&&v==0);g.model=original;}
    {uint16_t original=g.meshes[0].mesh_id;g.meshes[0].mesh_id=8;
     assert(!p3dVerifiedVertexUvGetPaired(&uv,&g,0,1,&u,&v));
     assert(u==4096&&v==0);g.meshes[0].mesh_id=original;}
    /* C296: reject a redirected live mesh pointer even if IDs and CRC match. */
    {const int16_t *original=g.meshes[0].xyz;
     g.meshes[0].xyz=g.xyz+3;
     assert(!p3dVerifiedVertexUvGetPaired(&uv,&g,0,1,&u,&v));
     assert(u==4096&&v==0);
     g.meshes[0].xyz=original;}
    {const int16_t *original=g.meshes[0].xyz;
     g.meshes[0].xyz=NULL;
     assert(!p3dVerifiedVertexUvGetPaired(&uv,&g,0,1,&u,&v));
     assert(u==4096&&v==0);
     g.meshes[0].xyz=original;}
    /* C297: paired reads reject incomplete whole-model metadata. */
    {unsigned original=uv.vertex_count;uv.vertex_count--;
     assert(!p3dVerifiedVertexUvGetPaired(&uv,&g,0,1,&u,&v));
     assert(u==4096&&v==0);uv.vertex_count=original;}
    {size_t original=g.mesh_count;g.mesh_count++;
     assert(!p3dVerifiedVertexUvGetPaired(&uv,&g,0,1,&u,&v));
     assert(u==4096&&v==0);g.mesh_count=original;}
    {size_t original=uv.size;uv.size--;
     assert(!p3dVerifiedVertexUvGetPaired(&uv,&g,0,1,&u,&v));
     assert(u==4096&&v==0);uv.size=original;}
    assert(!p3dVerifiedVertexUvGetPaired(&uv,&g,1,0,&u,&v));
    assert(p3dVerifiedVertexUvGetPaired(&uv,&g,0,1,&u,&v));
    /* Corrupted staged UV coordinates must fail without modifying outputs. */
    {uint8_t original=uv.bytes[32];
     uv.bytes[32]=1; /* U=4097 */
     assert(!p3dVerifiedVertexUvGet(&uv,0,1,&u,&v));
     assert(u==4096&&v==0);
     uv.bytes[32]=original;}
    {uint8_t original=uv.bytes[35];
     uv.bytes[35]=0x80; /* negative V */
     assert(!p3dVerifiedVertexUvGet(&uv,0,1,&u,&v));
     assert(u==4096&&v==0);
     uv.bytes[35]=original;}
    assert(p3dVerifiedVertexUvGet(&uv,0,1,&u,&v));
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
    /* Oversized file must fail without retaining any partial UV state. */
    write_file(argv[3],vu,sizeof(vu));
    {FILE *extra=fopen(argv[3],"ab");assert(extra);
     for(unsigned i=0;i<P3D_VERTEX_UV_MAX_BYTES;i++)assert(fputc(0,extra)!=EOF);
     assert(!fclose(extra));}
    denied(argv[3]);
    p3dVerifiedGeometryPairClear(&g);
    write_file(argv[3],vu,sizeof(vu));denied(argv[3]);
    puts("C289: CRC-bound native per-vertex UV staging (synthetic): PASS");
    return 0;
}
