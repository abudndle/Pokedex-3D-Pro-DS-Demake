#ifndef P3D_DEX_DESCRIPTION_H
#define P3D_DEX_DESCRIPTION_H
#include "species_details.h"
#define P3D_DESCRIPTION_TAB P3D_DETAIL_DESCRIPTION_TAB
#define P3D_DESCRIPTION_BYTES 192u
#define P3D_DESCRIPTION_LINE_WIDTH 28u
#define P3D_DESCRIPTION_LINES_PER_PAGE 4u
#define P3D_DESCRIPTION_MAX_PAGES 48u
#define P3D_DESCRIPTION_CONTROL_ROW 18
/* Offsets refer only to owned normalized text, never the caller's source. */
typedef struct {
 char text[P3D_DESCRIPTION_BYTES];
 uint8_t offsets[P3D_DESCRIPTION_BYTES],lengths[P3D_DESCRIPTION_BYTES];
 uint8_t count,page,ready;
 uint32_t checksum;
} P3DDescription;
void p3dDescriptionClear(P3DDescription *description);
int p3dDescriptionSet(P3DDescription *description,const char *source);
unsigned p3dDescriptionPages(const P3DDescription *description);
int p3dDescriptionLine(const P3DDescription *description,unsigned relative_line,char out[29]);
int p3dDescriptionStep(P3DDescription *description,int direction);
/* Valid visible hits consume input even when already at a page boundary. */
int p3dDescriptionTouch(P3DDescription *description,int controls_visible,int x,int y);
int p3dDescriptionRestore(P3DDescription *description,int valid,unsigned page,uint32_t checksum);
#endif
