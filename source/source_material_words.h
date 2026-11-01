#ifndef P3D_SOURCE_MATERIAL_WORDS_H
#define P3D_SOURCE_MATERIAL_WORDS_H
#include <stdint.h>
#include "source_material_map.h"
#include "source_shader_caps.h"
#define P3D_SOURCE_WORDS_PER_MATERIAL 13u
/* Original C5 material source words. Their GPU operation semantics are NOT
 * decoded. Native geometry uses them only for independent provenance checks. */
typedef struct {
    uint16_t model_id,count;
    int ready;
    uint32_t words[P3D_SHADER_MAX_MATERIALS][P3D_SOURCE_WORDS_PER_MATERIAL];
} P3DSourceMaterialWords;
/* CRC-checked P3SW v1, independent of other private P3SC/P3MR sidecars. */
int p3dSourceMaterialWordsLoad(P3DSourceMaterialWords *out,
                               const char *path,unsigned expected_model_id);
int p3dSourceMaterialWordsMatch(
    const P3DSourceMaterialWords *words,
    const P3DSourceShaderCaps *caps,
    const P3DSourceMaterialMap *source,
    unsigned expected_model_id,unsigned expected_triangles);
#endif
