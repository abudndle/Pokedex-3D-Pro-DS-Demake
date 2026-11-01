#ifndef P3D_VERIFIED_PRIMITIVE_STREAM_H
#define P3D_VERIFIED_PRIMITIVE_STREAM_H
#include <stddef.h>
#include <stdint.h>
/* P3IX is a verified triangle index companion, not a vertex source. */
typedef struct {
    uint16_t model;
    uint16_t mesh_count;
    uint32_t triangles;
} P3DVerifiedIndexInfo;
/* Strictly validates a complete P3IX buffer; no partial stream acceptance. */
int p3dVerifiedIndexInspect(const uint8_t *data,size_t size,
                            uint16_t expected_model,P3DVerifiedIndexInfo *out);
#endif
