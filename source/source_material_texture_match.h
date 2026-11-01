#ifndef P3D_SOURCE_MATERIAL_TEXTURE_MATCH_H
#define P3D_SOURCE_MATERIAL_TEXTURE_MATCH_H
#include "source_material_map.h"
#include "model_material_texture.h"
/* Require candidate P3MT material IDs and texture references to agree with
 * the original C5 draw-table material+texture references (private P3MR).
 * This validates provenance, NOT which C5 sampler is diffuse/color. */
int p3dSourceMaterialTextureReferencesMatch(
    const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,
    const P3DTextureManifest *textures,
    unsigned model_id,unsigned mesh_triangles);
/* Resolve the source-verified candidate texture for an individual triangle.
 * Returns -1 if any model/material/source reference is inconsistent.
 * This does not prove that either original 3DS sampler is the color sampler. */
int p3dSourceCandidateTextureForTriangle(
    const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,
    const P3DTextureManifest *textures,
    unsigned model_id,unsigned mesh_triangles,unsigned triangle);
/* Build an entire source-backed per-face texture map atomically.
 * On failure no partial mapping is exposed; output remains -1 throughout.
 * Does not infer original 3DS sampler/shader roles. */
int p3dSourceCandidateTextureMap(
    const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,
    const P3DTextureManifest *textures,
    unsigned model_id,unsigned mesh_triangles,
    int *out,unsigned out_capacity);
/* Final draw-time C5 provenance gate: reject an entire source material
 * span unless every face maps to the exact approved original texture.
 * Bounds are against the LOADED mesh, not merely the 600-face buffer.
 * Does not grant unknown sampler/shader roles or certify texture fidelity. */
int p3dSourceCandidateTextureRangeMatches(
    const int *face_textures,unsigned face_capacity,
    unsigned mesh_triangles,unsigned first_triangle,
    unsigned triangle_count,unsigned texture_id);

#endif
