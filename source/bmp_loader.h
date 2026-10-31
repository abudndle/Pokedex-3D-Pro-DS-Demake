#ifndef P3D_BMP_LOADER_H
#define P3D_BMP_LOADER_H
#include <stdint.h>
#include <stddef.h>
/* Output contains RGB555 pixels; caller provides width*height elements. */
int p3dBmpDecode24(const char *path,uint16_t *pixels,size_t capacity,int *out_width,int *out_height);
#endif
