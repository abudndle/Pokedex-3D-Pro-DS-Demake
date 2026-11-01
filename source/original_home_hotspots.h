#ifndef P3D_ORIGINAL_HOME_HOTSPOTS_H
#define P3D_ORIGINAL_HOME_HOTSPOTS_H
#include "feature_menu.h"
#include <stdint.h>
#define P3D_ORIGINAL_HOME_ICONS 7u
/* Private C123 source-measured original 3DS menu icon rectangles in
 * DS 256x192 touch coordinates, NOT inferred from text debug labels. */
typedef struct {
    uint16_t page,x0,y0,x1,y1;
} P3DHomeHotspot;
typedef struct {
    P3DHomeHotspot icons[P3D_ORIGINAL_HOME_ICONS];
    uint8_t ready;
} P3DHomeHotspots;
int p3dHomeHotspotsLoad(P3DHomeHotspots *out,const char *path);
int p3dHomeHotspotsHit(const P3DHomeHotspots *map,int x,int y);
int p3dHomeHotspotsValidate(const P3DHomeHotspots *map);
#endif
