#ifndef P3D_VERIFIED_VERTEX_UV_H
#define P3D_VERIFIED_VERTEX_UV_H
#include <stddef.h>
#include <stdint.h>
#include "verified_geometry_pair.h"
/* P3VU v1 is an optional, PRIVATE, source-indexed UV transport.
 * 20-byte header: magic, version, model, mesh count, reserved,
 * CRC32 of the exact paired P3VX file, CRC32 of the P3VU mesh table+UV data.
 * 8-byte mesh table: mesh ID, vertex count, packed first-vertex index.
 * Payload: little-endian signed 4.12 (u,v) per original P3VX vertex.
 * Only unit coordinates [0,4096] are accepted until original C5 wrap and
 * sampler operations are independently decoded. CRC is a pairing check,
 * NOT proof that the UVs are original or safe to bind to a color texture. */
#define P3D_VERTEX_UV_MAX_BYTES (20u+P3D_VERTEX_MAX_MESHES*8u+P3D_VERTEX_MAX_VERTICES*4u)
typedef struct {
    uint8_t bytes[P3D_VERTEX_UV_MAX_BYTES];
    size_t size;
    unsigned mesh_count,vertex_count;
    uint16_t model;
    int ready;
} P3DVerifiedVertexUv;
void p3dVerifiedVertexUvClear(P3DVerifiedVertexUv *uv);
/* Fails closed, clearing all previous model state on any mismatch/corruption. */
int p3dVerifiedVertexUvLoad(P3DVerifiedVertexUv *uv,const char *path,
                            const P3DVerifiedGeometryPair *geometry);
/* Returns false on unbound mesh or vertex. Output coordinates unchanged on failure. */
int p3dVerifiedVertexUvGet(const P3DVerifiedVertexUv *uv,
                           unsigned mesh_index,unsigned vertex_index,
                           int16_t *u,int16_t *v);
#endif
