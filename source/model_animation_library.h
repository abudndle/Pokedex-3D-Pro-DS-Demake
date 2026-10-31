#ifndef P3D_MODEL_ANIMATION_LIBRARY_H
#define P3D_MODEL_ANIMATION_LIBRARY_H
#include "model_animation.h"

/* Only clips that pass P3AN validation are exposed. The legacy pNNN.p3an
 * slot is -1; extra private clips use pNNN_a00.p3an through _a06.p3an.
 * Slot numbers are filenames, NOT guessed original animation identities. */
#define P3D_ANIMATION_LIBRARY_MAX 8
typedef struct {
    int resource_index;
    int slots[P3D_ANIMATION_LIBRARY_MAX];
    unsigned count;
    unsigned selected;
    int ready;
} P3DAnimationLibrary;

/* Only one decoded clip is resident at a time to fit DS memory limits.
 * Returns 1 if at least one verified clip exists, 0 otherwise. */
int p3dAnimationLibraryLoad(P3DAnimationLibrary *library,
                             P3DAnimationClip *clip,
                             const char *directory,int resource_index);
/* Cycle among validated clips. Returns 1 only for an actual selection
 * change; failure invalidates playback rather than rendering stale poses. */
int p3dAnimationLibraryStep(P3DAnimationLibrary *library,
                             P3DAnimationClip *clip,
                             const char *directory,int direction);
#endif
