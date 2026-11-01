#ifndef P3D_VERIFIED_VERTEX_STREAM_H
#define P3D_VERIFIED_VERTEX_STREAM_H
#include <stddef.h>
#include <stdint.h>
#include "verified_primitive_bridge.h"
/* P3VX v1: private, source-verified mesh XYZ transport (NOT a C5 decoder).
 * Header: 'P3VX', version u16, model u16, meshes u16, reserved u16,
 * CRC32 u32 over the following 8-byte mesh table and XYZ payload.
 * Table: mesh_id u16, vertex_count u16, first_vertex u32 (strictly packed).
 * Payload: signed little-endian 4.12 XYZ triples, six bytes per vertex.
 * No texture, skinning, provenance or animation is inferred by this format.
 */
#define P3D_VERTEX_MAX_MESHES 64u
#define P3D_VERTEX_MAX_VERTICES 8192u
/* All-or-nothing: on failure no output meshes/coordinates are modified.
 * xyz_capacity counts int16_t components, not vertices. Input must be
 * preloaded from a trusted private location; no file access occurs here. */
int p3dVerifiedVerticesDecode(const uint8_t *data,size_t size,
    uint16_t expected_model,P3DPrimitiveVertices *meshes,size_t mesh_capacity,
    int16_t *xyz,size_t xyz_capacity,size_t *decoded_mesh_count);
#endif
