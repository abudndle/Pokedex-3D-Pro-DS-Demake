#ifndef P3D_FORM_MODEL_MAP_H
#define P3D_FORM_MODEL_MAP_H
#include <stdint.h>
#define P3D_MAX_FORM_ENTRIES 256
typedef struct { uint16_t species, form, resource; } P3DFormEntry;
typedef struct { P3DFormEntry entries[P3D_MAX_FORM_ENTRIES]; unsigned count; int ready; } P3DFormMap;
/* P3FM v1: header magic,u16 version,u16 count; sorted unique (species,form,resource) triples.
 * species: zero-based 0..648; form: one-based alternate ordinal; resource: 0..737. */
int p3dFormMapLoad(P3DFormMap *map,const char *path);
int p3dFormResolve(const P3DFormMap *map,int species,int form);
int p3dFormNext(const P3DFormMap *map,int species,int current_form);
#endif
