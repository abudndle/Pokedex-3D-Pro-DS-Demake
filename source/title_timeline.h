#ifndef P3D_TITLE_TIMELINE_H
#define P3D_TITLE_TIMELINE_H
#include <stdint.h>
#define P3D_TITLE_MAX_FRAMES 16u
/* P3TL v1 is a private, user-supplied source timing declaration.
 * Frame 0 is the existing original title pair, not synthesized art.
 * Timing is in DS VBlanks; no 3DS source timing is inferred by the port. */
typedef struct {
    uint16_t frames,ticks[P3D_TITLE_MAX_FRAMES];
    uint16_t current,elapsed;
    uint8_t loop,ready;
} P3DTitleTimeline;
int p3dTitleTimelineLoad(P3DTitleTimeline *out,const char *path);
int p3dTitleTimelineAdvance(P3DTitleTimeline *timeline);
#endif
