/* C304 synthetic-only orchestration fixture: no Nintendo material or models.
 * Mock the source provenance bridge so this test specifically probes
 * preflight/upload/rollback ordering and verified triangle emission. */
#include "ds_material_uv_draw.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int allow_source,plain_second;
static unsigned preflight_calls,draw_calls,begin_calls,uv_calls,vertices,plain_binds,color_calls;
static unsigned char last_colors[2][3];
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
    const P3DSourceShaderCaps *caps,P3DVerifiedMaterialTriangleSink sink,
    void *context){
    (void)uv;(void)source;(void)materials;(void)textures;(void)caps;
    assert(g && g->triangles==2 && sink);
    preflight_calls++;
    if(!allow_source)return 0;
    P3DPrimitiveUvVertex a={0},b={0},c={0};
    a.xyz=xyz; b.xyz=xyz+3; c.xyz=xyz+6;
    a.u=0; b.u=4096; c.v=4096;
    if(!sink(context,0,0,7,&a,&b,&c))return 0;
    return sink(context,0,1,plain_second?P3D_SOURCE_MATERIAL_NO_TEXTURE:8,&a,&b,&c);
}
int p3dVerifiedMaterialUvDrawWithWords(
    const P3DVerifiedGeometryPair *g,const P3DVerifiedVertexUv *uv,
    const P3DSourceMaterialMap *source,const P3DMaterialMap *materials,
    const P3DTextureManifest *textures,const P3DSourceShaderCaps *caps,
    const P3DSourceMaterialWords *words,
    P3DVerifiedMaterialTriangleSink sink,void *context){
    /* The verified source-word/classifier walker is tested independently.
     * This fixture only checks the native upload and draw transaction. */
    if(!words||!words->ready)return 0;
    return p3dVerifiedMaterialUvDraw(g,uv,source,materials,textures,
                                      caps,sink,context);
}
int p3dTestMaterialBegin(int id){assert(id>=0);if(!id)plain_binds++;begin_calls++;trace(1,id,0);return 1;}
void p3dTestMaterialColor(unsigned char r,unsigned char g,unsigned char b){
    unsigned idx=color_calls%2;
    last_colors[idx][0]=r;last_colors[idx][1]=g;last_colors[idx][2]=b;
    color_calls++;
}
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
           &caps,&cache,scratch,&drawn));
    assert(preflight_calls==1 && !drawn && !cache.count && cache.ready);
    assert(!begin_calls && !draw_calls);
    /* C448: source evidence marks the second face untextured. Its P3PX
     * file is deliberately absent; preparation must upload ONLY texture 7,
     * with no polygons, then render both source triangles safely. */
    P3DSourceMaterialWords words={0};
    words.ready=1;
    allow_source=1;
    plain_second=1;
    assert(p3dDsMaterialUvPrepareWithWords(&g,&uv,&source,&materials,
        &textures,&caps,&words,&cache,scratch));
    assert(cache.count==1 && cache.ids[0]==7 && cache.ready);
    assert(!begin_calls && !draw_calls && !vertices && !uv_calls);
    trace_count=0;
    assert(p3dDsMaterialUvDrawWithWords(&g,&uv,&source,&materials,
        &textures,&caps,&words,&cache,scratch,&drawn));
    assert(drawn==2 && cache.count==1 && plain_binds==1);
    assert(begin_calls==2 && draw_calls==2 && vertices==6 && uv_calls==3);
    assert(trace_count==13 && vals_a[0]>0 && vals_a[8]==0);
    assert(color_calls==2 && last_colors[0][0]==255 &&
           last_colors[1][0]==192);
    p3dDsMaterialTextureCacheDestroy(&cache);
    assert(p3dDsMaterialTextureCacheInit(&cache,&textures,resolve,NULL));
    plain_second=0;
    /* Preserve the old strict-mode transaction assertions below. */
    preflight_calls=1;
    begin_calls=draw_calls=vertices=uv_calls=plain_binds=color_calls=trace_count=0;
    /* C445: the current material map fits in isolation, but a full-bank
     * resident texture leaves no space. Reject BEFORE uploading or GL draw.
     * The resident slot here is a synthetic cache state, not real GPU data. */
    allow_source=1;
    textures.count=3;
    textures.entries[2].id=9;
    textures.entries[2].width=256;
    textures.entries[2].height=256;
    textures.entries[2].format=1;
    cache.ids[0]=9;
    cache.count=1;
    assert(!p3dDsMaterialUvPrepare(&g,&uv,&source,&materials,&textures,
                                   &caps,&cache,scratch));
    assert(preflight_calls==2 && cache.ready && cache.count==1);
    assert(!begin_calls && !draw_calls && !vertices && !uv_calls);
    cache.count=0;
    textures.count=2;
    /* Missing second texture rolls back the first upload completely. */
    assert(!p3dDsMaterialUvDraw(&g,&uv,&source,&materials,&textures,
           &caps,&cache,scratch,&drawn));
    assert(preflight_calls==3 && !drawn && !cache.count && !cache.ready);
    assert(!begin_calls && !draw_calls);
    make_texture("t008.p3px");
    assert(p3dDsMaterialTextureCacheInit(&cache,&textures,resolve,NULL));
    /* C312: load all texture VRAM with zero polygon writes, before any
     * model frame. Renaming the source texture files then proves that two
     * successive frames never reopen their backing payloads. */
    assert(p3dDsMaterialUvPrepare(&g,&uv,&source,&materials,&textures,
                                 &caps,&cache,scratch));
    assert(cache.ready && cache.count==2);
    assert(!begin_calls && !draw_calls && !vertices && !uv_calls);
    assert(!rename("t007.p3px","t007.prepared"));
    assert(!rename("t008.p3px","t008.prepared"));
    assert(p3dDsMaterialUvDraw(&g,&uv,&source,&materials,&textures,
           &caps,&cache,scratch,&drawn));
    assert(drawn==2 && preflight_calls==6 && begin_calls==2 &&
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
              &caps,&cache,scratch,&drawn));
        assert(drawn==2&&cache.count==2&&trace_count==16);
        assert(vals_a[0]==first&&vals_a[8]==second);
        for(unsigned i=0;i<16;i++)assert(kinds[i]==expected_kinds[i]);
    }
    /* C446: an explicitly unresolved source-material range must emit
     * its triangle with texture 0, no UV sampling, and a neutral tint.
     * The first verified triangle stays white textured. No new uploads. */
    plain_second=1;
    trace_count=0;
    unsigned old_vertices=vertices,old_uv=uv_calls,old_colors=color_calls;
    assert(p3dDsMaterialUvDraw(&g,&uv,&source,&materials,&textures,
          &caps,&cache,scratch,&drawn));
    assert(drawn==2 && trace_count==13 && cache.count==2);
    assert(kinds[0]==1 && vals_a[0]>0 && kinds[8]==1 && vals_a[8]==0);
    assert(kinds[9]==3 && kinds[10]==3 && kinds[11]==3 && kinds[12]==4);
    assert(plain_binds==1 && vertices==old_vertices+6 && uv_calls==old_uv+3);
    assert(color_calls==old_colors+2);
    assert(last_colors[old_colors%2][0]==255 && last_colors[old_colors%2][1]==255 && last_colors[old_colors%2][2]==255);
    assert(last_colors[(old_colors+1)%2][0]==192 && last_colors[(old_colors+1)%2][1]==224 && last_colors[(old_colors+1)%2][2]==232);
    plain_second=0;
    p3dDsMaterialTextureCacheDestroy(&cache);
    assert(!cache.count&&!cache.ready);
    assert(!remove("t007.prepared")); assert(!remove("t008.prepared"));
    free(scratch);
    puts("C304/C305: synthetic native texture transaction and exact draw trace PASS");
    return 0;
}
