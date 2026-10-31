#ifndef P3D_MODEL_ANIMATION_H
#define P3D_MODEL_ANIMATION_H
#include <stdint.h>
#define P3D_ANIMATION_MAX_FRAMES 120
typedef struct { int16_t yaw; int16_t pitch; int16_t roll; uint16_t duration; } P3DAnimationFrame;
typedef struct { P3DAnimationFrame frames[P3D_ANIMATION_MAX_FRAMES]; unsigned count; unsigned total_ticks; unsigned version; int ready; } P3DAnimationClip;
/* Synthetic-friendly transform clip transport; NOT original skeletal animation decoding.
 * P3AN v1: magic, LE16 version, LE16 frame count; frames are 8-byte LE
 * yaw/pitch/roll (signed) and duration (unsigned, nonzero).
 * P3AN v2 uses the same frame layout but interpolates the next keyframe
 * across the current frame's duration with shortest-arc DS angle wrapping.
 * v1 retains discrete/held poses. Neither format is skeletal animation. */
int p3dAnimationLoad(P3DAnimationClip *clip,const char *path);
int p3dAnimationFrameAt(const P3DAnimationClip *clip,unsigned tick);
/* Resolve a complete transform pose at a playback tick. Returns 0 if the
 * clip is invalid or no pose is available; original v1 timings are held. */
int p3dAnimationPoseAt(const P3DAnimationClip *clip,unsigned tick,
                       P3DAnimationFrame *pose);
#endif
