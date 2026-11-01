#ifndef P3D_VERIFIED_PRIMITIVE_DRAW_H
#define P3D_VERIFIED_PRIMITIVE_DRAW_H
#include "verified_primitive_bridge.h"
/* Native DS draw adapter: source-verified 4.12 coordinates only.
 * Caller owns GL initialization, projection and texture state. */
int p3dVerifiedPrimitiveDraw(const uint8_t *indices,size_t size,
    uint16_t model,const P3DPrimitiveVertices *meshes,size_t mesh_count,
    uint32_t *drawn_triangles);
#endif
