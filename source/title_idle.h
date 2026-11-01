#ifndef P3D_TITLE_IDLE_H
#define P3D_TITLE_IDLE_H
#include <stddef.h>
#include <time.h>
#define P3D_TITLE_IDLE_TICKS 720u
typedef struct {unsigned ticks; int active;} P3DTitleIdle;
void p3dTitleIdleReset(P3DTitleIdle *idle);
int p3dTitleIdleAdvance(P3DTitleIdle *idle);
int p3dTitleIdleClock(char *dest,size_t size,time_t now);
#endif
