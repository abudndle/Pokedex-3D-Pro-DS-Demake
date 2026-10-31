#ifndef P3D_MODEL_TEXTURE_CATALOG_H
#define P3D_MODEL_TEXTURE_CATALOG_H
#include <stdint.h>
#define P3D_TX_MAX_ENTRIES 32
#define P3D_TX_MAX_NAME 40
/* P3TM v1: verified texture-source metadata; NOT mesh/material bindings. */
typedef struct {
    uint16_t width, height;
    uint32_t original_format, original_offset;
    uint8_t original_sha256[32];
    char original_name[P3D_TX_MAX_NAME];
} P3DTextureDescriptor;
typedef struct {
    uint16_t model_id, texture_count;
    int ready;
    P3DTextureDescriptor entries[P3D_TX_MAX_ENTRIES];
} P3DModelTextureCatalog;
/* Fails closed on missing, empty, corrupted, or mismatched original catalogs.
   Does not interpret or assign any original GPU materials or upload textures. */
int p3dTextureCatalogLoad(P3DModelTextureCatalog *out,
                          const char *path, unsigned expected_model_id);
#endif
