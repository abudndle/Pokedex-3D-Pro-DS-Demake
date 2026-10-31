#ifndef P3D_DS_TEXTURE_UPLOAD_H
#define P3D_DS_TEXTURE_UPLOAD_H
#include "texture_pixels.h"
/* 0 on failure, 1 on upload; caller owns DS 3D texture VRAM setup. */
int p3dDsTextureUpload(const P3DTexturePixels *pixels,int *texture_id);
#endif
