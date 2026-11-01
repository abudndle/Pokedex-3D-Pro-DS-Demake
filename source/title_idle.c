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
