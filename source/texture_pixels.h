#ifndef P3D_TEXTURE_PIXELS_H
#define P3D_TEXTURE_PIXELS_H
#include <stdint.h>
#define P3D_TEXTURE_PIXEL_MAX (256u*256u)
typedef struct {uint16_t width,height,version;uint16_t pixels[P3D_TEXTURE_PIXEL_MAX];int ready;} P3DTexturePixels;
/* P3PX v1: legacy RGB555; v2: DS 16-bit direct-color A1 RGB555.
 * Both versions: magic, LE16 version, width, height, then exactly
 * width*height LE16 pixels. In v2 bit 15 is opacity, 0 transparent,
 * 1 opaque. The source alpha8 is quantized by a private converter.
 * Preserve the source format version so native upload can keep P3PX v2\n * bit-15 alpha; v1 is legacy opaque RGB555. No material bindings implied. */
int p3dTexturePixelsLoad(P3DTexturePixels *image,const char *path);
#endif
