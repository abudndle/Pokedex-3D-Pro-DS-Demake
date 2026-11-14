#ifndef P3D_VERIFIED_MATERIAL_UV_DRAW_H
#define P3D_VERIFIED_MATERIAL_UV_DRAW_H
#include "verified_primitive_uv_bridge.h"
#include "source_shader_caps.h"
#include "source_material_words.h"
typedef int (*P3DVerifiedMaterialTriangleSink)(void *context,
    uint16_t mesh_id,unsigned triangle_index,unsigned texture_id,
    const P3DPrimitiveUvVertex *a,const P3DPrimitiveUvVertex *b,
    const P3DPrimitiveUvVertex *c);
/* Source-backed color-map gate. Does not infer original sampler slot or
 * implement unsupported multi-sampler/bump/other shader behavior. */
int p3dVerifiedMaterialUvDraw(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,
    P3DVerifiedMaterialTriangleSink sink,void *context);
/* Original C5 operation words and shader flags independently determine
 * color-capable material faces. Unsupported effects retain their geometry
 * with P3D_SOURCE_MATERIAL_NO_TEXTURE instead of a guessed texture. */
int p3dVerifiedMaterialUvDrawWithWords(
    const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *caps,const P3DSourceMaterialWords *words,
    P3DVerifiedMaterialTriangleSink sink,void *context);
#endif
