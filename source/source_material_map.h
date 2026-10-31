#ifndef P3D_SOURCE_MATERIAL_MAP_H
#define P3D_SOURCE_MATERIAL_MAP_H
#include <stdint.h>
#define P3D_SOURCE_MATERIAL_MAX_RANGES 64u
#define P3D_SOURCE_MATERIAL_NO_TEXTURE 65535u
typedef struct {
    uint16_t first_triangle,triangle_count,material_index;
    uint16_t source_texture0,source_texture1,source_pass;
} P3DSourceMaterialRange;
typedef struct {
    uint16_t model_id,triangle_count,count;
    int ready;
    P3DSourceMaterialRange ranges[P3D_SOURCE_MATERIAL_MAX_RANGES];
} P3DSourceMaterialMap;
/* P3MR describes verified source C5 material indices in source-matched
 * DS3M/P3UV samples. NOT a P3MT diffuse texture map. Does not upload textures. */
int p3dSourceMaterialLoad(P3DSourceMaterialMap *out,const char *path,
                          unsigned expected_model_id,unsigned expected_triangles);
#endif
