#ifndef P3D_DS_MATERIAL_UV_DRAW_H
#define P3D_DS_MATERIAL_UV_DRAW_H
#include "ds_material_texture_cache.h"
#include "verified_material_uv_draw.h"
/* C312: validate all source triangles, then upload their entire native texture
 * set before the first 3D drawing frame. Never emit a polygon here.
 * On any partial upload failure the cache is destroyed for safe fallback. */
int p3dDsMaterialUvPrepare(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,
    P3DDsMaterialTextureCache *cache,P3DTexturePixels *scratch);
/* Emits only triangles accepted by the complete source/material/UV gate.
 * Projection, model transforms, lighting and GL frame setup remain caller-owned. */
int p3dDsMaterialUvDraw(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,
    P3DDsMaterialTextureCache *cache,P3DTexturePixels *scratch,
    uint32_t *drawn_triangles);
/* Source-word-backed mixed material path. Unsupported shaders are drawn
 * untextured and only eligible color textures are loaded into DS VRAM. */
int p3dDsMaterialUvPrepareWithWords(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,const P3DSourceMaterialWords *words,
    P3DDsMaterialTextureCache *cache,P3DTexturePixels *scratch);
int p3dDsMaterialUvDrawWithWords(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,const P3DSourceMaterialWords *words,
    P3DDsMaterialTextureCache *cache,P3DTexturePixels *scratch,
    uint32_t *drawn_triangles);
#endif
