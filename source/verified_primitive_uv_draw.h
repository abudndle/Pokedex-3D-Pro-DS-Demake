#ifndef P3D_VERIFIED_PRIMITIVE_UV_DRAW_H
#define P3D_VERIFIED_PRIMITIVE_UV_DRAW_H
#include "verified_primitive_uv_bridge.h"
/* Emits verified source-indexed UVs and vertices through native DS GL.
 * Caller owns texture enable/bind, matrices, and material approval. */
int p3dVerifiedPrimitiveUvDraw(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,uint32_t *drawn_triangles);
#endif
