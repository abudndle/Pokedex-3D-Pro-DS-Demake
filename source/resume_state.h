#ifndef P3D_RESUME_STATE_H
#define P3D_RESUME_STATE_H
#include "feature_menu.h"
#include "challenge.h"
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
    /* P3RV v4: optional exact active Challenge checkpoint. Inactive saves
     * retain the compact v3 file on disk for legacy interoperability. */
    uint8_t quiz_active;
    P3DChallenge quiz;
    uint32_t challenge_correct_total, challenge_answer_total;
    uint32_t challenge_recorded_rounds; /* P3RC rounds at checkpoint time */
    /* C333: optional P3RV v5 detail-tab state (only live Pokédex page). */
    uint8_t dex_detail_tab;
    /* Optional v6: exact complete learnset page, bound to P3SL content. */
    uint8_t dex_learnset_valid,dex_learnset_page;
    uint32_t dex_learnset_checksum;
    /* Optional v7: stable photo identity for the active Album viewer. */
    uint8_t album_view_active;
    uint16_t album_photo_id;
    uint32_t album_photo_checksum,album_photo_bytes;
    /* Optional v8: exact Description page, bound to the P3DX text bytes. */
    uint8_t dex_description_valid,dex_description_page;
    uint32_t dex_description_checksum;
} P3DResumeState;
int p3dResumeStateValid(const P3DResumeState *state);
/* A previously completed round must never be resurrected by a stale
 * review snapshot after P3RC has advanced, even if that snapshot has CRC. */
int p3dResumeCanRestoreQuiz(const P3DResumeState *state,
                            uint32_t progress_correct,uint32_t progress_answers,
                            uint32_t recorded_rounds);
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
