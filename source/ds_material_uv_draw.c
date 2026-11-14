#include "ds_material_uv_draw.h"
#include "model_material_texture.h"
#ifdef C7_TEST_HOST
extern int p3dTestMaterialBegin(int texture_id);
extern void p3dTestMaterialTexCoord(int16_t u,int16_t v);
extern void p3dTestMaterialVertex(const int16_t *xyz);
extern void p3dTestMaterialEnd(void);
extern void p3dTestMaterialColor(unsigned char r,unsigned char g,unsigned char b);
#define P3D_MATERIAL_BEGIN(id) p3dTestMaterialBegin(id)
#define P3D_MATERIAL_UV(u,v) p3dTestMaterialTexCoord((u),(v))
#define P3D_MATERIAL_VERTEX(p) p3dTestMaterialVertex(p)
#define P3D_MATERIAL_END() p3dTestMaterialEnd()
#define P3D_MATERIAL_COLOR(r,g,b) p3dTestMaterialColor((r),(g),(b))
#else
#include <nds.h>
#define P3D_MATERIAL_BEGIN(id) do { glBindTexture(0,(id)); glBegin(GL_TRIANGLES); } while(0)
#define P3D_MATERIAL_UV(u,v) glTexCoord2t16((u),(v))
#define P3D_MATERIAL_VERTEX(p) glVertex3v16((v16)(p)[0],(v16)(p)[1],(v16)(p)[2])
#define P3D_MATERIAL_END() glEnd()
#define P3D_MATERIAL_COLOR(r,g,b) glColor3b((r),(g),(b))
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
       (texture_id!=P3D_SOURCE_MATERIAL_NO_TEXTURE &&
        !p3dDsMaterialTextureCacheGet(ctx->cache,texture_id,ctx->scratch,
          &hardware_id))){
        if(ctx)ctx->failed=1;
        return 0;
    }
    /* Unapproved original shader/sampler roles are drawn as neutral
     * geometry, never sampled as a guessed color texture. Bind texture
     * zero so the previous material cannot bleed into this triangle. */
    if(texture_id==P3D_SOURCE_MATERIAL_NO_TEXTURE){
        P3D_MATERIAL_COLOR(192,224,232);
        P3D_MATERIAL_BEGIN(0);
        P3D_MATERIAL_VERTEX(a->xyz);
        P3D_MATERIAL_VERTEX(b->xyz);
        P3D_MATERIAL_VERTEX(c->xyz);
        P3D_MATERIAL_END();
        ctx->count++;
        return 1;
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
    /* A previous plain range must not tint a verified color texture. */
    P3D_MATERIAL_COLOR(255,255,255);
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
typedef struct {
    unsigned ids[P3D_DS_TEXTURE_CACHE_MAX];
    unsigned count;
} MaterialTextureNeeds;
static int preflight_triangle(void *opaque,uint16_t mesh,unsigned triangle,
    unsigned texture_id,const P3DPrimitiveUvVertex *a,
    const P3DPrimitiveUvVertex *b,const P3DPrimitiveUvVertex *c){
    MaterialTextureNeeds *needed=(MaterialTextureNeeds *)opaque;
    (void)mesh;(void)triangle;
    if(!needed||!a||!b||!c||!a->xyz||!b->xyz||!c->xyz)return 0;
    if(texture_id==P3D_SOURCE_MATERIAL_NO_TEXTURE)return 1;
    if(texture_id>65534u)return 0;
    for(unsigned i=0;i<needed->count;i++)
        if(needed->ids[i]==texture_id)return 1;
    if(needed->count>=P3D_DS_TEXTURE_CACHE_MAX)return 0;
    needed->ids[needed->count++]=texture_id;
    return 1;
}
static int material_prepare_internal(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,const P3DSourceMaterialWords *words,
    P3DDsMaterialTextureCache *cache,P3DTexturePixels *scratch){
    MaterialTextureNeeds needed={0};
    if(!geometry||!uv||!source||!materials||!textures||!shader_caps||
       !cache||!cache->ready||cache->manifest!=textures||!scratch)return 0;
    /* Historical strict callers require every candidate material to fit.
     * Source-word callers count only materials actually approved for color. */
    if(!words && !p3dDsMaterialTextureBudgetValid(materials,textures,
          (unsigned)geometry->triangles))return 0;
    /* Validate the entire original triangle/UV walk before any upload. */
    if(words){
        if(!p3dVerifiedMaterialUvDrawWithWords(geometry,uv,source,materials,
           textures,shader_caps,words,preflight_triangle,&needed))return 0;
    }else if(!p3dVerifiedMaterialUvDraw(geometry,uv,source,materials,
               textures,shader_caps,preflight_triangle,&needed))return 0;
    /* This also checks pre-existing GPU allocations for each unique ID;
     * an all-neutral original model needs no texture VRAM at all. */
    if(needed.count && !p3dDsMaterialTextureCacheFits(cache,
                                      needed.ids,needed.count))return 0;
    for(unsigned i=0;i<needed.count;i++){
        int hardware_id=0;
        if(!p3dDsMaterialTextureCacheGet(cache,
             needed.ids[i],scratch,&hardware_id)){
            /* Atomically release the entire partially uploaded set. */
            p3dDsMaterialTextureCacheDestroy(cache);
            return 0;
        }
    }
    return 1;
}
static int material_draw_internal(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,const P3DSourceMaterialWords *words,
    P3DDsMaterialTextureCache *cache,P3DTexturePixels *scratch,
    uint32_t *drawn_triangles){
    MaterialUvDraw ctx;
    if(drawn_triangles)*drawn_triangles=0;
    if(!geometry||!uv||!source||!materials||!textures||!shader_caps||
       !cache||!cache->ready||!scratch)return 0;
    /* Legacy callers still perform guarded preparation here. Native
     * reload_preview() calls Prepare in advance, so every cache hit in the
     * actual frame is read-only and never writes texture VRAM. */
    if(!material_prepare_internal(geometry,uv,source,materials,textures,
                                  shader_caps,words,cache,scratch))return 0;
    ctx.cache=cache;ctx.scratch=scratch;ctx.count=0;ctx.failed=0;
    int complete=words
        ? p3dVerifiedMaterialUvDrawWithWords(geometry,uv,source,materials,
            textures,shader_caps,words,draw_material_triangle,&ctx)
        : p3dVerifiedMaterialUvDraw(geometry,uv,source,materials,textures,
            shader_caps,draw_material_triangle,&ctx);
    if(!complete||ctx.failed)return 0;
    if(drawn_triangles)*drawn_triangles=ctx.count;
    return ctx.count==geometry->triangles;
}

/* Keep existing strict host and caller interfaces unchanged. */
int p3dDsMaterialUvPrepare(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,
    P3DDsMaterialTextureCache *cache,P3DTexturePixels *scratch){
    return material_prepare_internal(geometry,uv,source,materials,textures,
                                     shader_caps,NULL,cache,scratch);
}
int p3dDsMaterialUvDraw(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,
    P3DDsMaterialTextureCache *cache,P3DTexturePixels *scratch,
    uint32_t *drawn_triangles){
    return material_draw_internal(geometry,uv,source,materials,textures,
                                  shader_caps,NULL,cache,scratch,drawn_triangles);
}
int p3dDsMaterialUvPrepareWithWords(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,const P3DSourceMaterialWords *words,
    P3DDsMaterialTextureCache *cache,P3DTexturePixels *scratch){
    if(!words)return 0;
    return material_prepare_internal(geometry,uv,source,materials,textures,
                                     shader_caps,words,cache,scratch);
}
int p3dDsMaterialUvDrawWithWords(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,const P3DSourceMaterialWords *words,
    P3DDsMaterialTextureCache *cache,P3DTexturePixels *scratch,
    uint32_t *drawn_triangles){
    if(!words){if(drawn_triangles)*drawn_triangles=0;return 0;}
    return material_draw_internal(geometry,uv,source,materials,textures,
                                  shader_caps,words,cache,scratch,drawn_triangles);
}
