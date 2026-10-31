#ifndef P3D_MODEL_ANIMATION_H
#define P3D_MODEL_ANIMATION_H
#include <stdint.h>
#define P3D_ANIMATION_MAX_FRAMES 120
typedef struct { int16_t yaw; int16_t pitch; int16_t roll; uint16_t duration; } P3DAnimationFrame;
typedef struct { P3DAnimationFrame frames[P3D_ANIMATION_MAX_FRAMES]; unsigned count; unsigned total_ticks; int ready; } P3DAnimationClip;
/* Synthetic-friendly transform clip transport; NOT original skeletal animation decoding.
 * P3AN v1: magic, LE16 version, LE16 frame count; frames are 8-byte LE
 * yaw/pitch/roll (signed) and duration (unsigned, nonzero). */
int p3dAnimationLoad(P3DAnimationClip *clip,const char *path);
int p3dAnimationFrameAt(const P3DAnimationClip *clip,unsigned tick);
#endif
