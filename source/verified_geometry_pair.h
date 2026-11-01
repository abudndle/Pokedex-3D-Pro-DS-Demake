#ifndef P3D_VERIFIED_GEOMETRY_PAIR_H
#define P3D_VERIFIED_GEOMETRY_PAIR_H
#include <stddef.h>
#include <stdint.h>
#include "verified_vertex_stream.h"
/* Bounded, optional private NitroFS source-geometry transport. A P3VX is NOT
 * evidence of source C5 vertex decoding; only independently verified private
 * sidecars may be supplied. The pair is deliberately not a release asset. */
#define P3D_GEOMETRY_MAX_TRIANGLES 1800u
#define P3D_GEOMETRY_P3VX_MAX_BYTES (16u+P3D_VERTEX_MAX_MESHES*8u+P3D_VERTEX_MAX_VERTICES*6u)
#define P3D_GEOMETRY_P3IX_MAX_BYTES (10u+P3D_VERTEX_MAX_MESHES*6u+P3D_GEOMETRY_MAX_TRIANGLES*6u)
typedef struct {
    uint8_t vx[P3D_GEOMETRY_P3VX_MAX_BYTES];
    uint8_t ix[P3D_GEOMETRY_P3IX_MAX_BYTES];
    int16_t xyz[P3D_VERTEX_MAX_VERTICES*3u];
    P3DPrimitiveVertices meshes[P3D_VERTEX_MAX_MESHES];
    size_t mesh_count,ix_size;
    uint32_t triangles;
    uint16_t model;
    int ready;
} P3DVerifiedGeometryPair;
/* Preflight both files, all indices and every vertex reference before ready.
 * On ANY failure all state is cleared, including previous species geometry.
 * Keep this large structure in static storage and never memcpy/move it after
 * loading: mesh pointers refer to its internal xyz array. */
int p3dVerifiedGeometryPairLoad(P3DVerifiedGeometryPair *pair,
    const char *vertex_path,const char *index_path,uint16_t model);
void p3dVerifiedGeometryPairClear(P3DVerifiedGeometryPair *pair);
#endif
