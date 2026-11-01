#ifndef P3D_MOVE_TEXT_VIEW_H
#define P3D_MOVE_TEXT_VIEW_H
#include "move_dex.h"
#define P3D_MOVE_FIELD_DESCRIPTION 0
#define P3D_MOVE_FIELD_EFFECT 1
/* Select only original P3DM content. Missing effect data remains missing. */
const char *p3dMoveTextField(const P3DMove *entry,int field);
/* Move in 28-character steps through an 84-character Nintendo DS viewport. */
int p3dMoveTextScroll(int current,const char *text,int direction);
#endif
