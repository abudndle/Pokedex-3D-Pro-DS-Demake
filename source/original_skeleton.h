#ifndef P3D_ORIGINAL_SKELETON_H
#define P3D_ORIGINAL_SKELETON_H
#include <stdint.h>
/* C149: source-preserving native loader for private original P3SK v1 rigs.
 * These records carry original 3x4 float matrix bytes and parent/name refs.
 * NO skin weights or original action clips are inferred by this loader. */
#define P3D_SKELETON_MAX_NODES 160u
#define P3D_SKELETON_NODE_BYTES 56u
#define P3D_SKELETON_MAX_STRING_BYTES 4096u
typedef struct {
    uint16_t model_id;
    uint16_t node_count;
    uint16_t root_count;
    int ready;
    unsigned char records[P3D_SKELETON_MAX_NODES*P3D_SKELETON_NODE_BYTES];
    char strings[P3D_SKELETON_MAX_STRING_BYTES];
    unsigned string_bytes;
} P3DOriginalSkeleton;
/* Clear rig when switching models or when the optional private file is absent. */
void p3dOriginalSkeletonClear(P3DOriginalSkeleton *out);
/* Fail-closed: output must be zero/invalid after every rejected input. */
int p3dOriginalSkeletonLoad(P3DOriginalSkeleton *out,const char *path,unsigned expected_model_id);
const char *p3dOriginalSkeletonName(const P3DOriginalSkeleton *out,unsigned node_index);
int p3dOriginalSkeletonParent(const P3DOriginalSkeleton *out,unsigned node_index);
/* Returns a pointer to the exact 48 little-endian bytes of the original
 * node matrix; the consumer must explicitly handle float/matrix convention. */
const unsigned char *p3dOriginalSkeletonMatrixBytes(const P3DOriginalSkeleton *out,unsigned node_index);
#endif