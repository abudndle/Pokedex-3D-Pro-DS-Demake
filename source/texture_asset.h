#ifndef P3D_TEXTURE_ASSET_H
#define P3D_TEXTURE_ASSET_H
#include "model_textures.h"
#include "texture_pixels.h"
/* Load a private RGB555 file only if its verified manifest entry agrees. */
int p3dTextureAssetLoad(P3DTexturePixels *pixels,const P3DTextureManifest *manifest,
                        unsigned texture_id,const char *path);
#endif
