/* C304 synthetic-only orchestration fixture: no Nintendo material or models.
 * Mock the source provenance bridge so this test specifically probes
 * preflight/upload/rollback ordering and verified triangle emission. */
#include "ds_material_uv_draw.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int allow_source;
static unsigned preflight_calls,draw_calls,begin_calls,uv_calls,vertices;
static int kinds[32],vals_a[32],vals_b[32];
static unsigned trace_count;
static void trace(int kind,int a,int b){
    assert(trace_count<32);
    kinds[trace_count]=kind;
    vals_a[trace_count]=a;
    vals_b[trace_count]=b;
    trace_count++;
}
static int16_t xyz[9]={0,0,0,4096,0,0,0,4096,0};
int p3dVerifiedMaterialUvDraw(const P3DVerifiedGeometryPair *g,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *caps,const P3DSourceMaterialWords *words,
    P3DVerifiedMaterialTriangleSink sink,
    void *context){
    (void)uv;(void)source;(void)materials;(void)textures;(void)caps;(void)words;
    assert(g && g->triangles==2 && sink);
    preflight_calls++;
    if(!allow_source)return 0;
    P3DPrimitiveUvVertex a={0},b={0},c={0};
    a.xyz=xyz; b.xyz=xyz+3; c.xyz=xyz+6;
    a.u=0; b.u=4096; c.v=4096;
    if(!sink(context,0,0,7,&a,&b,&c))return 0;
    return sink(context,0,1,8,&a,&b,&c);
}
int p3dTestMaterialBegin(int id){assert(id>0);begin_calls++;trace(1,id,0);return 1;}
void p3dTestMaterialTexCoord(int16_t u,int16_t v){
    assert(u==0||u==128);assert(v==0||v==128);uv_calls++;trace(2,u,v);
}
void p3dTestMaterialVertex(const int16_t *p){
    assert(p>=xyz&&p<xyz+9);vertices++;trace(3,p[0],p[1]);
}
void p3dTestMaterialEnd(void){draw_calls++;trace(4,0,0);}
static const char *resolve(void *opaque,unsigned id){
    (void)opaque;return id==7?"t007.p3px":id==8?"t008.p3px":NULL;
}
static void make_texture(const char *path){
    FILE *f=fopen(path,"wb");assert(f);
    const unsigned char hdr[10]={'P','3','P','X',1,0,8,0,8,0};
    assert(fwrite(hdr,1,sizeof(hdr),f)==sizeof(hdr));
    for(unsigned i=0;i<64;i++){
        const unsigned char px[2]={0x1f,0x00};
        assert(fwrite(px,1,2,f)==2);
    }
    assert(!fclose(f));
}
int main(void){
    static P3DVerifiedGeometryPair g;
    static P3DVerifiedVertexUv uv;
    static P3DSourceMaterialMap source;
    static P3DSourceShaderCaps caps;
    static P3DMaterialMap materials;
    static P3DTextureManifest textures;
    static P3DDsMaterialTextureCache cache;
    P3DTexturePixels *scratch=malloc(sizeof(*scratch));assert(scratch);
    g.triangles=2;
    materials.ready=1; materials.count=2;
    textures.ready=1; textures.count=2;
    for(unsigned i=0;i<2;i++){
        materials.ranges[i].first_triangle=(uint16_t)i;
        materials.ranges[i].triangle_count=1;
        materials.ranges[i].texture_id=(uint16_t)(7+i);
        textures.entries[i].id=(uint16_t)(7+i);
        textures.entries[i].width=8;
        textures.entries[i].height=8;
        textures.entries[i].format=1;
    }
    uint32_t drawn=99;
    make_texture("t007.p3px");
    assert(p3dDsMaterialTextureCacheInit(&cache,&textures,resolve,NULL));
    /* A corrupt/denied source stream must not upload any private texture. */
    allow_source=0;
    assert(!p3dDsMaterialUvDraw(&g,&uv,&source,&materials,&textures,
           &caps,NULL,&cache,scratch,&drawn));
    assert(preflight_calls==1 && !drawn && !cache.count && cache.ready);
    assert(!begin_calls && !draw_calls);
    /* Missing second texture rolls back the first upload completely. */
    allow_source=1;
    assert(!p3dDsMaterialUvDraw(&g,&uv,&source,&materials,&textures,
           &caps,NULL,&cache,scratch,&drawn));
    assert(preflight_calls==2 && !drawn && !cache.count && !cache.ready);
    assert(!begin_calls && !draw_calls);
    make_texture("t008.p3px");
    assert(p3dDsMaterialTextureCacheInit(&cache,&textures,resolve,NULL));
    /* C312: load all texture VRAM with zero polygon writes, before any
     * model frame. Renaming the source texture files then proves that two
     * successive frames never reopen their backing payloads. */
    assert(p3dDsMaterialUvPrepare(&g,&uv,&source,&materials,&textures,
                                 &caps,NULL,&cache,scratch));
    assert(cache.ready && cache.count==2);
    assert(!begin_calls && !draw_calls && !vertices && !uv_calls);
    assert(!rename("t007.p3px","t007.prepared"));
    assert(!rename("t008.p3px","t008.prepared"));
    assert(p3dDsMaterialUvDraw(&g,&uv,&source,&materials,&textures,
           &caps,NULL,&cache,scratch,&drawn));
    assert(drawn==2 && preflight_calls==5 && begin_calls==2 &&
           draw_calls==2 && uv_calls==6 && vertices==6 && cache.count==2);
    /* C305 independent synthetic draw trace: two distinct binds, and
     * exact ordered UV and XYZ events for both source-backed triangles. */
    {
        const int expected_kinds[16]={
            1,2,3,2,3,2,3,4,1,2,3,2,3,2,3,4
        };
        const int expected_u[3]={0,128,0};
        const int expected_v[3]={0,0,128};
        const int expected_x[3]={0,4096,0};
        const int expected_y[3]={0,0,4096};
        assert(trace_count==16);
        for(unsigned i=0;i<16;i++)assert(kinds[i]==expected_kinds[i]);
        assert(vals_a[0]>0&&vals_a[8]>0&&vals_a[0]!=vals_a[8]);
        for(unsigned tri=0;tri<2;tri++){
            for(unsigned vertex=0;vertex<3;vertex++){
                unsigned u=tri*8+1+vertex*2;
                assert(vals_a[u]==expected_u[vertex] &&
                       vals_b[u]==expected_v[vertex]);
                assert(vals_a[u+1]==expected_x[vertex] &&
                       vals_b[u+1]==expected_y[vertex]);
            }
        }
        /* A second frame must reuse the same GPU IDs and exact trace;
         * switching models separately calls the cache destructor. */
        int first=vals_a[0],second=vals_a[8];
        trace_count=0;
        assert(p3dDsMaterialUvDraw(&g,&uv,&source,&materials,&textures,
              &caps,NULL,&cache,scratch,&drawn));
        assert(drawn==2&&cache.count==2&&trace_count==16);
        assert(vals_a[0]==first&&vals_a[8]==second);
        for(unsigned i=0;i<16;i++)assert(kinds[i]==expected_kinds[i]);
    }
    p3dDsMaterialTextureCacheDestroy(&cache);
    assert(!cache.count&&!cache.ready);
    assert(!remove("t007.prepared")); assert(!remove("t008.prepared"));
    free(scratch);
    puts("C304/C305: synthetic native texture transaction and exact draw trace PASS");
    return 0;
}
