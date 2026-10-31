#ifndef P3D_MODEL_MATERIALS_H
#define P3D_MODEL_MATERIALS_H
#include <stdint.h>
#define P3D_MATERIAL_MAX 64
typedef struct {uint16_t first_triangle, triangle_count, material_id, texture_id;} P3DMaterialRange;
typedef struct {P3DMaterialRange ranges[P3D_MATERIAL_MAX];unsigned count;int ready;} P3DMaterialMap;
/* P3MT v1, little endian: 4-byte magic, u16 version, u16 range count,
 * followed by 8-byte (start,count,material,texture) entries.
 * No texture decoding or invented material assignments are implied. */
int p3dMaterialMapLoad(P3DMaterialMap *map,const char *path,unsigned model_triangles);
int p3dMaterialForTriangle(const P3DMaterialMap *map,unsigned triangle);
#endif
