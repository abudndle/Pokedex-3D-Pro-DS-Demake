#ifndef P3D_DS_MATERIAL_TEXTURE_CACHE_H
#define P3D_DS_MATERIAL_TEXTURE_CACHE_H
#include "ds_texture_upload.h"
#include "model_textures.h"
#include "model_materials.h"
/* Match the native preview's bounded texture bank and allocation count. */
#define P3D_DS_TEXTURE_CACHE_MAX 8u
#define P3D_DS_TEXTURE_VRAM_BYTES (128u*1024u)
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
/* Preflight distinct texture allocations with no GL calls or pixel reads.
 * Reused texture IDs consume VRAM only once. Reject incomplete material
 * coverage, unknown formats, or resource usage beyond bank B. */
int p3dDsMaterialTextureBudgetValid(const P3DMaterialMap *materials,
    const P3DTextureManifest *manifest,unsigned triangle_count);
/* Budget the union of resident textures and IDs approved for this draw. */
int p3dDsMaterialTextureCacheFits(const P3DDsMaterialTextureCache *cache,
    const unsigned *needed,unsigned count);
void p3dDsMaterialTextureCacheDestroy(P3DDsMaterialTextureCache *cache);
#endif
