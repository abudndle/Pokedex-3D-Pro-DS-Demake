#ifndef P3D_PHOTO_PNG_H
#define P3D_PHOTO_PNG_H
#include <stdint.h>
#include <stdio.h>
/* Bounded 640x480 noninterlaced PNG -> letterboxed DS RGB555.
 * Output is not ready until the caller receives success. */
int p3dPhotoPngDecode(FILE *file,uint16_t pixels[256u*192u],
                      unsigned *width,unsigned *height);
#endif
