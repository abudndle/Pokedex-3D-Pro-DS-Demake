#ifndef P3D_PREVIEW_TEXTURE_SET_H
#define P3D_PREVIEW_TEXTURE_SET_H
#include "model_materials.h"
#include "model_textures.h"
#include "texture_pixels.h"
#define P3D_PREVIEW_TEXTURE_LIMIT 8
#define P3D_PREVIEW_TEXTURE_VRAM_BYTES (128u*1024u)
typedef struct {
 unsigned id,width,height;
 int gl_id;
} P3DPreviewTexture;
typedef struct {
 P3DPreviewTexture entries[P3D_PREVIEW_TEXTURE_LIMIT];
 unsigned count;
 int ready;
} P3DPreviewTextureSet;
/* Upload only distinct, referenced, verified private textures. Strictly bound
 * to VRAM bank B (128 KiB) and at most 8 allocations; no partial success. */
int p3dPreviewTextureSetLoad(P3DPreviewTextureSet *set,
                            P3DTexturePixels *scratch,
                            const P3DMaterialMap *materials,
                            const P3DTextureManifest *manifest,
                            const char *texture_directory);
void p3dPreviewTextureSetRelease(P3DPreviewTextureSet *set);
const P3DPreviewTexture *p3dPreviewTextureSetFind(const P3DPreviewTextureSet *set,
                                                 unsigned texture_id);
#endif
