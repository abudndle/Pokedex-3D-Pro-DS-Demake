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
    P3D_MATERIAL_BEGIN(hardware_id);
    P3D_MATERIAL_UV(a->u,a->v);P3D_MATERIAL_VERTEX(a->xyz);
    P3D_MATERIAL_UV(b->u,b->v);P3D_MATERIAL_VERTEX(b->xyz);
    P3D_MATERIAL_UV(c->u,c->v);P3D_MATERIAL_VERTEX(c->xyz);
    P3D_MATERIAL_END();
    ctx->count++;
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
    /* Preload every material texture before emitting the first triangle.
     * A missing private asset therefore fails before any partial model draw. */
    if(!p3dModelMaterialTexturesMatchMesh(materials,textures,
          (unsigned)geometry->triangles))return 0;
    for(unsigned i=0;i<materials->count;i++){
        int hardware_id=0;
        if(!p3dDsMaterialTextureCacheGet(cache,
             materials->ranges[i].texture_id,scratch,&hardware_id))return 0;
    }
    ctx.cache=cache;ctx.scratch=scratch;ctx.count=0;ctx.failed=0;
    if(!p3dVerifiedMaterialUvDraw(geometry,uv,source,materials,textures,
       shader_caps,draw_material_triangle,&ctx)||ctx.failed)return 0;
    if(drawn_triangles)*drawn_triangles=ctx.count;
    return ctx.count==geometry->triangles;
}
