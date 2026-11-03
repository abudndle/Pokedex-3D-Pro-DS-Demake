#ifndef P3D_DS_MATERIAL_TEXTURE_CACHE_H
#define P3D_DS_MATERIAL_TEXTURE_CACHE_H
#include "ds_texture_upload.h"
#include "model_textures.h"
#define P3D_DS_TEXTURE_CACHE_MAX P3D_TEXTURE_MAX
typedef const char *(*P3DDsTexturePathResolver)(void *context,unsigned texture_id);
typedef struct {
    const P3DTextureManifest *manifest;
    P3DDsTexturePathResolver resolve_path;
    void *resolver_context;
    uint16_t ids[P3D_DS_TEXTURE_CACHE_MAX];
    int texture_ids[P3D_DS_TEXTURE_CACHE_MAX];
    unsigned count;
    int ready;
} P3DDsMaterialTextureCache;
/* Initialize a lazy cache. Paths are supplied by the private-asset resolver;
 * no proprietary filenames or texture assignments are embedded in this code. */
int p3dDsMaterialTextureCacheInit(P3DDsMaterialTextureCache *cache,
    const P3DTextureManifest *manifest,P3DDsTexturePathResolver resolver,
    void *resolver_context);
/* Resolve, validate dimensions/format, load pixels and upload once per ID.
 * Caller supplies reusable pixel scratch to avoid a large DS stack object. */
int p3dDsMaterialTextureCacheGet(P3DDsMaterialTextureCache *cache,
    unsigned texture_id,P3DTexturePixels *scratch,int *hardware_texture_id);
void p3dDsMaterialTextureCacheDestroy(P3DDsMaterialTextureCache *cache);
#endif
