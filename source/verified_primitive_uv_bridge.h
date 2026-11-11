#ifndef P3D_VERIFIED_PRIMITIVE_UV_BRIDGE_H
#define P3D_VERIFIED_PRIMITIVE_UV_BRIDGE_H
#include <stdint.h>
#include "verified_geometry_pair.h"
#include "verified_vertex_uv.h"
typedef struct {
    const int16_t *xyz;
    int16_t u,v;
} P3DPrimitiveUvVertex;
typedef int (*P3DPrimitiveUvTriangleSink)(void *context,uint16_t mesh_id,
    const P3DPrimitiveUvVertex *a,const P3DPrimitiveUvVertex *b,
    const P3DPrimitiveUvVertex *c);
/* Transactionally preflight the complete index/geometry/UV pair before
 * invoking any sink. The sink must leave the input buffers unchanged. */
int p3dVerifiedPrimitiveUvBridge(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,P3DPrimitiveUvTriangleSink sink,
    void *context);
#endif
