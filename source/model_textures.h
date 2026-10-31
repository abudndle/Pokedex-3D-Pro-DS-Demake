#ifndef P3D_MODEL_TEXTURES_H
#define P3D_MODEL_TEXTURES_H
#include <stdint.h>
#define P3D_TEXTURE_MAX 64
typedef struct {uint16_t id,width,height,format;} P3DTextureEntry;
typedef struct {P3DTextureEntry entries[P3D_TEXTURE_MAX];unsigned count;int ready;} P3DTextureManifest;
/* P3TX v1, LE: magic, u16 version, u16 count; 8-byte records
   (id,width,height,format). Format 1 = opaque RGB555 metadata.
   No texture pixels are embedded; this only validates references. */
int p3dTextureManifestLoad(P3DTextureManifest *map,const char *path);
const P3DTextureEntry *p3dTextureFind(const P3DTextureManifest *map,unsigned id);
#endif
