#ifndef P3D_MODEL_MATERIAL_TEXTURE_H
#define P3D_MODEL_MATERIAL_TEXTURE_H
#include "model_materials.h"
#include "model_textures.h"
/* Fail closed unless every model material range refers to a known texture.
 * This is a binding validator; original material IDs remain private. */
int p3dModelMaterialTexturesValid(const P3DMaterialMap *materials,
                                  const P3DTextureManifest *textures);
int p3dModelTextureForTriangle(const P3DMaterialMap *materials,
                               const P3DTextureManifest *textures,
                               unsigned triangle);
#endif
