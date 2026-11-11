#ifndef P3D_VERIFIED_MATERIAL_UV_DRAW_H
#define P3D_VERIFIED_MATERIAL_UV_DRAW_H
#include "verified_primitive_uv_bridge.h"
#include "source_shader_caps.h"
#include "source_material_words.h"
typedef int (*P3DVerifiedMaterialTriangleSink)(void *context,
    uint16_t mesh_id,unsigned triangle_index,unsigned texture_id,
    const P3DPrimitiveUvVertex *a,const P3DPrimitiveUvVertex *b,
    const P3DPrimitiveUvVertex *c);
/* When words are supplied, verified color ranges use textures and unresolved
 * ranges report P3D_SOURCE_MATERIAL_NO_TEXTURE to the sink. Without words,
 * every range must pass the strict source shader check. */
int p3dVerifiedMaterialUvDraw(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,const P3DSourceMaterialWords *words,
    P3DVerifiedMaterialTriangleSink sink,void *context);
#endif
