#ifndef P3D_SOURCE_COLOR_RANGES_H
#define P3D_SOURCE_COLOR_RANGES_H
#include <stdint.h>
#include "source_material_words.h"
#include "model_material_texture.h"
/* Only original C5 source-backed simple-colormap material ranges can
 * use the DS preview color texture. Other original shader roles are UNKNOWN. */
typedef struct {
    uint8_t enabled[P3D_MATERIAL_MAX];
    unsigned count,approved;
    int ready;
} P3DSourceColorRanges;
int p3dSourceColorRangesBuild(P3DSourceColorRanges *out,
    const P3DSourceMaterialWords *words,
    const P3DSourceShaderCaps *caps,
    const P3DSourceMaterialMap *source,
    const P3DMaterialMap *candidate,
    const P3DTextureManifest *textures,
    unsigned model_id,unsigned triangles);
#endif
