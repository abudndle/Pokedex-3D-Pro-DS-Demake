#ifndef P3D_TEXTURE_PIXELS_H
#define P3D_TEXTURE_PIXELS_H
#include <stdint.h>
#define P3D_TEXTURE_PIXEL_MAX (256u*256u)
typedef struct {uint16_t width,height;uint16_t pixels[P3D_TEXTURE_PIXEL_MAX];int ready;} P3DTexturePixels;
/* P3PX v1: 4-byte magic, LE16 version=1, width, height; then
   exactly width*height little-endian RGB555 pixels.
   Pixel conversion/upload requires separate verified DS VRAM integration. */
int p3dTexturePixelsLoad(P3DTexturePixels *image,const char *path);
#endif
