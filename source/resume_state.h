#ifndef P3D_RESUME_STATE_H
#define P3D_RESUME_STATE_H
#include "feature_menu.h"
#include <stdint.h>
/* Separate dual-slot P3RV, preserves legacy P3SV/P3RC formats unchanged. */
typedef struct {
    uint8_t home,page,highlight,records_tab;
    uint16_t dex,move,selected_dex,album_page;
} P3DResumeState;
int p3dResumeStateValid(const P3DResumeState *state);
int p3dResumeLoad(const char *base,P3DResumeState *out);
int p3dResumeStore(const char *base,const P3DResumeState *state);
int p3dResumeApply(const P3DResumeState *state,P3DCapabilities caps,
                   int *home,P3DMenu *menu,int *highlight);
/* A valid checkpoint means reset must open the saved screen directly.
 * No checkpoint means the original title can be shown on a fresh start. */
int p3dResumeRestoreBoot(const char *base,P3DResumeState *restored,
                         P3DCapabilities caps,int *home,
                         P3DMenu *menu,int *highlight);
#endif
