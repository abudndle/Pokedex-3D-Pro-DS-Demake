#ifndef P3D_TITLE_IDLE_H
#define P3D_TITLE_IDLE_H
#include <stddef.h>
#include <time.h>
#include <stdint.h>
#define P3D_TITLE_IDLE_TICKS 720u
/* Scene rotation is separate from the first title inactivity delay.
 * The actual 3DS transition duration still needs original source evidence. */
#define P3D_TITLE_SCENE_TICKS 600u
#define P3D_TITLE_POKEDEX_COUNT 649u
typedef struct {
    unsigned ticks,scene_ticks;
    unsigned species;
    uint32_t rng;
    int active,has_species;
} P3DTitleIdle;
void p3dTitleIdleReset(P3DTitleIdle *idle);
int p3dTitleIdleAdvance(P3DTitleIdle *idle);
/* Source-independent title scene choice: never use saved Pokédex species.
 * Seed from console RTC/session entropy; avoid repeating the prior scene. */
void p3dTitleIdleSeed(P3DTitleIdle *idle,uint32_t session_entropy);
unsigned p3dTitleIdleChooseSpecies(P3DTitleIdle *idle);
int p3dTitleIdleSceneDue(P3DTitleIdle *idle);
int p3dTitleIdleClock(char *dest,size_t size,time_t now);
#endif
