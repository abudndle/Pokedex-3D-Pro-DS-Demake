#include "ds_material_uv_draw.h"
#include "model_material_texture.h"
#ifdef C7_TEST_HOST
extern int p3dTestMaterialBegin(int texture_id);
extern void p3dTestMaterialTexCoord(int16_t u,int16_t v);
extern void p3dTestMaterialVertex(const int16_t *xyz);
extern void p3dTestMaterialEnd(void);
#define P3D_MATERIAL_BEGIN(id) p3dTestMaterialBegin(id)
#define P3D_MATERIAL_UV(u,v) p3dTestMaterialTexCoord((u),(v))
#define P3D_MATERIAL_VERTEX(p) p3dTestMaterialVertex(p)
#define P3D_MATERIAL_END() p3dTestMaterialEnd()
#else
#include <nds.h>
#define P3D_MATERIAL_BEGIN(id) do { glBindTexture(0,(id)); glBegin(GL_TRIANGLES); } while(0)
#define P3D_MATERIAL_UV(u,v) glTexCoord2t16((u),(v))
#define P3D_MATERIAL_VERTEX(p) glVertex3v16((v16)(p)[0],(v16)(p)[1],(v16)(p)[2])
#define P3D_MATERIAL_END() glEnd()
#endif
typedef struct {
    P3DDsMaterialTextureCache *cache;
    P3DTexturePixels *scratch;
    unsigned count;
    int failed;
} MaterialUvDraw;
static int draw_material_triangle(void *opaque,uint16_t mesh,unsigned triangle,
    unsigned texture_id,const P3DPrimitiveUvVertex *a,
    const P3DPrimitiveUvVertex *b,const P3DPrimitiveUvVertex *c){
    MaterialUvDraw *ctx=(MaterialUvDraw *)opaque;
    int hardware_id=0;
    (void)mesh;(void)triangle;
    if(!ctx||ctx->failed||!a||!b||!c||!a->xyz||!b->xyz||!c->xyz||
       !p3dDsMaterialTextureCacheGet(ctx->cache,texture_id,ctx->scratch,
          &hardware_id)){
        if(ctx)ctx->failed=1;
        return 0;
    }
    /* P3VU stores normalized 4.12 UVs (0..4096), but libnds
     * glTexCoord2t16 accepts 12.4 TEXEL coordinates, not normalized
     * coordinates. Multiply by the actual verified texture dimensions
     * before submitting any polygon. A whole-image U=1 becomes width*16. */
    const P3DTextureEntry *entry=p3dTextureFind(ctx->cache->manifest,texture_id);
    if(!entry||!entry->width||!entry->height){
        ctx->failed=1;
        return 0;
    }
    P3D_MATERIAL_BEGIN(hardware_id);
    P3D_MATERIAL_UV((int16_t)((int32_t)a->u*entry->width/256),
                    (int16_t)((int32_t)a->v*entry->height/256));P3D_MATERIAL_VERTEX(a->xyz);
    P3D_MATERIAL_UV((int16_t)((int32_t)b->u*entry->width/256),
                    (int16_t)((int32_t)b->v*entry->height/256));P3D_MATERIAL_VERTEX(b->xyz);
    P3D_MATERIAL_UV((int16_t)((int32_t)c->u*entry->width/256),
                    (int16_t)((int32_t)c->v*entry->height/256));P3D_MATERIAL_VERTEX(c->xyz);
    P3D_MATERIAL_END();
    ctx->count++;
    return 1;
}
/* A separate dry run must accept the complete source/UV stream before
 * any libnds GL state is changed or a triangle is emitted. */
static int preflight_triangle(void *unused,uint16_t mesh,unsigned triangle,
    unsigned texture_id,const P3DPrimitiveUvVertex *a,
    const P3DPrimitiveUvVertex *b,const P3DPrimitiveUvVertex *c){
    (void)unused;(void)mesh;(void)triangle;(void)texture_id;
    return a&&b&&c&&a->xyz&&b->xyz&&c->xyz;
}
int p3dDsMaterialUvPrepare(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,
    P3DDsMaterialTextureCache *cache,P3DTexturePixels *scratch){
    if(!geometry||!uv||!source||!materials||!textures||!shader_caps||
       !cache||!cache->ready||!scratch)return 0;
    if(!p3dDsMaterialTextureBudgetValid(materials,textures,
          (unsigned)geometry->triangles))return 0;
    /* Reuse the same strict no-side-effects source walk as the native drawer.
     * No hardware drawing is permitted in this model-loading phase. */
    if(!p3dVerifiedMaterialUvDraw(geometry,uv,source,materials,textures,
        shader_caps,preflight_triangle,NULL))return 0;
    for(unsigned i=0;i<materials->count;i++){
        int hardware_id=0;
        if(!p3dDsMaterialTextureCacheGet(cache,
             materials->ranges[i].texture_id,scratch,&hardware_id)){
            /* Atomically release the entire partially uploaded set. */
            p3dDsMaterialTextureCacheDestroy(cache);
            return 0;
        }
    }
    return 1;
}
int p3dDsMaterialUvDraw(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,
    P3DDsMaterialTextureCache *cache,P3DTexturePixels *scratch,
    uint32_t *drawn_triangles){
    MaterialUvDraw ctx;
    if(drawn_triangles)*drawn_triangles=0;
    if(!geometry||!uv||!source||!materials||!textures||!shader_caps||
       !cache||!cache->ready||!scratch)return 0;
    /* Legacy callers still perform guarded preparation here. Native
     * reload_preview() calls Prepare in advance, so every cache hit in the
     * actual frame is read-only and never writes texture VRAM. */
    if(!p3dDsMaterialUvPrepare(geometry,uv,source,materials,textures,
                               shader_caps,cache,scratch))return 0;
    ctx.cache=cache;ctx.scratch=scratch;ctx.count=0;ctx.failed=0;
    if(!p3dVerifiedMaterialUvDraw(geometry,uv,source,materials,textures,
       shader_caps,draw_material_triangle,&ctx)||ctx.failed)return 0;
    if(drawn_triangles)*drawn_triangles=ctx.count;
    return ctx.count==geometry->triangles;
}
