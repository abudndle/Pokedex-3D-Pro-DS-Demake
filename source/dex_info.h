#ifndef P3D_DEX_INFO_H
#define P3D_DEX_INFO_H
#include "dex_text.h"
typedef struct { P3DDexText text; int index,page,pages,ready; } P3DDexInfo;
/* Loading always resets pagination; failure clears the previous record. */
int p3dDexInfoLoad(P3DDexInfo *info,int index);
int p3dDexInfoStep(P3DDexInfo *info,int direction);
void p3dDexInfoLines(const P3DDexInfo *info,char first[29],char second[29]);
/* Center of text-console row 21; excludes species-browsing corners. */
int p3dDexInfoTouchToggle(int x,int y);
#endif
