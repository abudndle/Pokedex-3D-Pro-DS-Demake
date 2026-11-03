#ifndef P3D_DS_MATERIAL_UV_DRAW_H
#define P3D_DS_MATERIAL_UV_DRAW_H
#include "ds_material_texture_cache.h"
#include "verified_material_uv_draw.h"
/* Emits only triangles accepted by the complete source/material/UV gate.
 * Projection, model transforms, lighting and GL frame setup remain caller-owned. */
int p3dDsMaterialUvDraw(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,
    P3DDsMaterialTextureCache *cache,P3DTexturePixels *scratch,
    uint32_t *drawn_triangles);
#endif
