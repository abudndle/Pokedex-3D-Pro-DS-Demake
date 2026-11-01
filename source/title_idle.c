#include "title_idle.h"
#include <stdio.h>
#include <string.h>
void p3dTitleIdleReset(P3DTitleIdle *idle){
    if(idle)memset(idle,0,sizeof(*idle));
}
int p3dTitleIdleAdvance(P3DTitleIdle *idle){
    if(!idle||idle->active)return 0;
    if(idle->ticks<P3D_TITLE_IDLE_TICKS)idle->ticks++;
    if(idle->ticks==P3D_TITLE_IDLE_TICKS){
        idle->active=1;
        return 1;
    }
    return 0;
}
/* Xorshift32 is a lightweight scene picker; this is NOT a recovered 3DS
 * RNG algorithm. The game has 649 Pokédex species (not the 738 model
 * resources, which also contain forms). Source art is loaded independently. */
void p3dTitleIdleSeed(P3DTitleIdle *idle,uint32_t entropy){
    if(!idle)return;
    idle->rng=entropy?entropy:0x6d2b79f5u;
    idle->has_species=0;
    idle->scene_ticks=0;
}
static uint32_t scene_random(P3DTitleIdle *idle){
    uint32_t v=idle->rng;
    if(!v)v=0x6d2b79f5u;
    v^=v<<13;
    v^=v>>17;
    v^=v<<5;
    idle->rng=v;
    return v;
}
unsigned p3dTitleIdleChooseSpecies(P3DTitleIdle *idle){
    uint32_t value;
    unsigned next;
    if(!idle)return 0;
    /* 649 choices, excluding the previous one once a scene is showing.
     * The saved Pokédex entry is never read or modified by this selector. */
    value=scene_random(idle);
    next=(unsigned)(value%(P3D_TITLE_POKEDEX_COUNT-
                           (idle->has_species?1u:0u)));
    if(idle->has_species && next>=idle->species)next++;
    idle->species=next;
    idle->has_species=1;
    idle->scene_ticks=0;
    return next;
}
int p3dTitleIdleSceneDue(P3DTitleIdle *idle){
    if(!idle||!idle->active||!idle->has_species)return 0;
    if(++idle->scene_ticks>=P3D_TITLE_SCENE_TICKS){
        idle->scene_ticks=0;
        return 1;
    }
    return 0;
}
int p3dTitleIdleClock(char *dest,size_t size,time_t now){
    struct tm *clock;
    if(!dest||!size)return 0;
    dest[0]=0;
    clock=localtime(&now);
    if(!clock)return 0;
    /* Clock and date are read from the running console/emulator RTC; no
     * hard-coded day, date, timezone or game-world invented time. */
    return strftime(dest,size,"%a %m/%d/%Y %I:%M %p",clock)>0;
}
