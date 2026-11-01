#ifndef P3D_VERIFIED_PRIMITIVE_BRIDGE_H
#define P3D_VERIFIED_PRIMITIVE_BRIDGE_H
#include <stddef.h>
#include <stdint.h>
/* Vertex data is supplied by a separately validated original-source decoder.
 * Each mesh has its own vertex buffer. No implicit cross-mesh index remap. */
typedef struct {
    uint16_t mesh_id;
    const int16_t *xyz;
    uint32_t vertex_count;
} P3DPrimitiveVertices;
typedef int (*P3DPrimitiveTriangleSink)(void *context,uint16_t mesh_id,
    const int16_t *a,const int16_t *b,const int16_t *c);
/* Transactional preflight: no sink is called if any mesh/index is invalid. */
int p3dVerifiedPrimitiveBridge(const uint8_t *indices,size_t size,
    uint16_t expected_model,const P3DPrimitiveVertices *meshes,size_t mesh_count,
    P3DPrimitiveTriangleSink sink,void *context,uint32_t *emitted);
#endif
