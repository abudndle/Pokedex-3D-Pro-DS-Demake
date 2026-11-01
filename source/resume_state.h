#ifndef P3D_RESUME_STATE_H
#define P3D_RESUME_STATE_H
#include "feature_menu.h"
#include <stdint.h>
/* Separate dual-slot P3RV, preserves legacy P3SV/P3RC formats unchanged. */
typedef struct {
    uint8_t home,page,highlight,records_tab;
    uint16_t dex,move,selected_dex,album_page;
    /* P3RV v2: restore the exact in-page context as well as the page.
     * V1 checkpoints decode with all these fields safely zeroed. */
    uint16_t selected_form,move_text_offset,menu_cursor;
    uint8_t album_selected,records_recent_cursor,move_show_effect;
    uint8_t search_region,search_scope,search_field,favorite_cursor;
    /* P3RV v3: exact typed Search text and additional subpage selection. */
    char search_query[13];
    uint8_t search_letter,challenge_mode;
    uint8_t type_attack,type_defend,type_defend2_plus_one;
    uint8_t favorites_selected;
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
