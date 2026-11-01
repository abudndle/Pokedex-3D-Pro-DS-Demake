#ifndef P3D_ORIGINAL_TRACK_BINDING_H
#define P3D_ORIGINAL_TRACK_BINDING_H
#include <stdint.h>
#include "original_skeleton.h"
/* C151: exact source-verified C5 animation owner identity only.
 * No action clips, interpolation, matrix convention or skinning inferred. */
typedef struct {
    uint16_t source_node_index; /* C148 verified original C5 owner low16 */
    const char *source_node_name; /* C147 verified original C5 string name */
} P3DOriginalTrackOwner;
/* Fail closed on any missing/mismatched/duplicate source node.
 * On failure, every output slot remains 0xffff (unbound).
 * Returns 1 for a fully validated original-node association only. */
int p3dOriginalTrackBind(const P3DOriginalSkeleton *rig,
                         const P3DOriginalTrackOwner *owners,
                         unsigned count,uint16_t *resolved);
#endif
