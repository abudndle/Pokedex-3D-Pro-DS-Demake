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
    return sink(context,0,1,8,&a,&b,&c);
}
int p3dTestMaterialBegin(int id){assert(id>0);begin_calls++;return 1;}
void p3dTestMaterialTexCoord(int16_t u,int16_t v){
    assert(u==0||u==4096);assert(v==0||v==4096);uv_calls++;
}
void p3dTestMaterialVertex(const int16_t *p){assert(p>=xyz&&p<xyz+9);vertices++;}
void p3dTestMaterialEnd(void){draw_calls++;}
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
    /* Missing second texture rolls back the first upload completely. */
    allow_source=1;
    assert(!p3dDsMaterialUvDraw(&g,&uv,&source,&materials,&textures,
           &caps,&cache,scratch,&drawn));
    assert(preflight_calls==2 && !drawn && !cache.count && !cache.ready);
    assert(!begin_calls && !draw_calls);
    make_texture("t008.p3px");
    assert(p3dDsMaterialTextureCacheInit(&cache,&textures,resolve,NULL));
    assert(p3dDsMaterialUvDraw(&g,&uv,&source,&materials,&textures,
           &caps,&cache,scratch,&drawn));
    assert(drawn==2 && preflight_calls==4 && begin_calls==2 &&
           draw_calls==2 && uv_calls==6 && vertices==6 && cache.count==2);
    p3dDsMaterialTextureCacheDestroy(&cache);
    assert(!cache.count&&!cache.ready);
    assert(!remove("t007.p3px")); assert(!remove("t008.p3px"));
    free(scratch);
    puts("C304: synthetic native material preflight/rollback/draw PASS");
    return 0;
}
