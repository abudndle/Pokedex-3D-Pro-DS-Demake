#ifndef P3D_SOURCE_SHADER_CAPS_H
#define P3D_SOURCE_SHADER_CAPS_H
#include <stdint.h>
#include "source_material_map.h"
#include "model_material_texture.h"
#define P3D_SHADER_MAX_MATERIALS 256u
#define P3D_SHADER_CAP_COLORMAP 1u
#define P3D_SHADER_CAP_BUMPMAP 2u
typedef struct {
    uint16_t material_id,shader_index,texture0,texture1,flags;
} P3DSourceShaderMaterial;
typedef struct {
    uint16_t model_id,count;
    int ready;
    P3DSourceShaderMaterial materials[P3D_SHADER_MAX_MATERIALS];
} P3DSourceShaderCaps;
/* P3SC: CRC-checked original C5 shader capability declarations, not decoded
 * source GPU sampler assignments or proof of specific diffuse texture roles. */
int p3dSourceShaderCapsLoad(P3DSourceShaderCaps *out,const char *path,
                            unsigned model_id);
/* Conservative gate: original material needs CF_COLORMAP AND exactly one
 * non-sentinel original C5 texture reference. More complex materials stay
 * untextured until real source shader/sampler role decoding exists. */
int p3dSourceShaderColorReferencesMatch(
    const P3DSourceShaderCaps *caps,
    const P3DSourceMaterialMap *source,
    const P3DMaterialMap *candidate,
    const P3DTextureManifest *textures,
    unsigned model_id,unsigned mesh_triangles);
#endif
