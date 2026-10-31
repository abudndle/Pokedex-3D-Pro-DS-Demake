#ifndef P3D_MODEL_UV_H
#define P3D_MODEL_UV_H
#include <stdint.h>
#define P3D_UV_MAX_TRIANGLES 600
typedef struct {int16_t uv[P3D_UV_MAX_TRIANGLES*6]; unsigned triangles; int ready;} P3DUvMap;
/* P3UV v1: magic, u16 version, u16 triangle_count, then six signed
 * 4.12 texture coordinates per triangle, arranged u0,v0,u1,v1,u2,v2.
 * Source UVs must be verified before writing the private NitroFS file. */
int p3dUvLoad(P3DUvMap *map,const char *path,unsigned model_triangles);
#endif
