#ifndef P3D_SPECIES_MODEL_MAP_H
#define P3D_SPECIES_MODEL_MAP_H
#include <stdint.h>
#define P3D_SPECIES_COUNT 649
#define P3D_RESOURCE_COUNT 738
#define P3D_MODEL_UNAVAILABLE 0xffffu
typedef struct { uint16_t resource[P3D_SPECIES_COUNT]; int ready; } P3DModelMap;
/* Requires an explicit, privately generated mapping; no guessed identity mapping. */
int p3dModelMapLoad(P3DModelMap *map, const char *path);
int p3dModelMapResolve(const P3DModelMap *map, int species_index);
#endif
