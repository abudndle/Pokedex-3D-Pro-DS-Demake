#ifndef P3D_IMAGE_BACKGROUND_H
#define P3D_IMAGE_BACKGROUND_H
#include "custom_images.h"
#include <stddef.h>
#include <stdint.h>
/* This output is a background pixel buffer, not a Pokemon model texture. */
typedef struct {uint16_t *pixels;size_t capacity;int width,height;int custom_active;} P3DImageBackground;
int p3dBackgroundLoad(P3DImageBackground *out,const P3DImageSettings *settings,const char *folder,int storage_ready);
void p3dBackgroundClear(P3DImageBackground *out);
#endif
