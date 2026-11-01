#ifndef P3D_SOURCE_TRACK_BINDINGS_H
#define P3D_SOURCE_TRACK_BINDINGS_H
#include "original_skeleton.h"
/* P3TB v1 is a private, source-derived owner-to-skeleton association, NOT
 * animation keyframes, clips, matrices, interpolation or skinning. */
#define P3D_TRACK_BINDING_RECORD_BYTES 112u
#define P3D_TRACK_BINDING_NAME_BYTES 104u
typedef struct {
    uint16_t model_id;
    uint16_t count;
    int ready;
    uint16_t node[P3D_SKELETON_MAX_NODES];
    uint32_t source_first_track[P3D_SKELETON_MAX_NODES];
} P3DSourceTrackBindings;
void p3dSourceTrackBindingsClear(P3DSourceTrackBindings *out);
/* Fails closed on absent/mismatched source rig, model, node, exact name,
 * original string offset, duplicate node, CRC, record ordering or EOF. */
int p3dSourceTrackBindingsLoad(P3DSourceTrackBindings *out,
    const P3DOriginalSkeleton *rig,const char *path,unsigned expected_model_id);
#endif
