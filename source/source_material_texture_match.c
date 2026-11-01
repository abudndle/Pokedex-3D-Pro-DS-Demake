#include "source_material_texture_match.h"
int p3dSourceMaterialTextureReferencesMatch(
    const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,
    const P3DTextureManifest *textures,
    unsigned model_id,unsigned mesh_triangles){
    unsigned src_cursor=0,mat_cursor=0,j=0;
    if(!source||!source->ready||model_id>=738||!mesh_triangles||
       mesh_triangles>600||source->model_id!=model_id||
       source->triangle_count!=mesh_triangles||
       !source->count||source->count>P3D_SOURCE_MATERIAL_MAX_RANGES||
       !p3dModelMaterialTexturesMatchMesh(materials,textures,mesh_triangles))
        return 0;
    for(unsigned i=0;i<source->count;i++){
        const P3DSourceMaterialRange *s=&source->ranges[i];
        unsigned end;
        if(s->first_triangle!=src_cursor||!s->triangle_count||
           s->triangle_count>mesh_triangles-src_cursor||
           s->material_index>255||s->source_pass!=0x0c02u)
            return 0;
        end=src_cursor+s->triangle_count;
        /* Never let a proposed P3MT face span cross a verified C5
         * material boundary, even if its texture ID happens to match. */
        while(mat_cursor<end){
            const P3DMaterialRange *m;
            if(j>=materials->count)return 0;
            m=&materials->ranges[j++];
            if(m->first_triangle!=mat_cursor||!m->triangle_count||
               m->triangle_count>end-mat_cursor||
               m->material_id!=s->material_index||
               (m->texture_id!=s->source_texture0 &&
                m->texture_id!=s->source_texture1))
                return 0;
            /* P3MR may name 65535 as "no source texture"; that is
             * never a valid original texture payload reference. */
            if(m->texture_id==P3D_SOURCE_MATERIAL_NO_TEXTURE)return 0;
            mat_cursor+=m->triangle_count;
        }
        src_cursor=end;
    }
    return src_cursor==mesh_triangles && mat_cursor==mesh_triangles &&
           j==materials->count;
}

/* Do not render a candidate range unless its complete mesh/source
 * provenance is coherent. The original shader's sampler role is still
 * unknown; this returns the chosen referenced texture, not an inferred
 * diffuse/normal-map role. */
int p3dSourceCandidateTextureForTriangle(
    const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,
    const P3DTextureManifest *textures,
    unsigned model_id,unsigned mesh_triangles,unsigned triangle){
    if(triangle>=mesh_triangles ||
       !p3dSourceMaterialTextureReferencesMatch(
           source,materials,textures,model_id,mesh_triangles))
        return -1;
    return p3dModelTextureForTriangle(materials,textures,triangle);
}

int p3dSourceCandidateTextureMap(
    const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,
    const P3DTextureManifest *textures,
    unsigned model_id,unsigned mesh_triangles,
    int *out,unsigned out_capacity){
    if(!out || !out_capacity || out_capacity>600)return 0;
    for(unsigned i=0;i<out_capacity;i++)out[i]=-1;
    if(mesh_triangles>out_capacity ||
       !p3dSourceMaterialTextureReferencesMatch(
           source,materials,textures,model_id,mesh_triangles))
        return 0;
    unsigned cursor=0;
    for(unsigned i=0;i<materials->count;i++){
        const P3DMaterialRange *r=&materials->ranges[i];
        for(unsigned j=0;j<r->triangle_count;j++)
            out[cursor++]=(int)r->texture_id;
    }
    return cursor==mesh_triangles;
}

/* Source C5 range eligibility is a draw-time check, not a promise inferred
 * from texture filename similarity. In particular NEVER bind a valid GL
 * texture to a face whose original material reference says otherwise. */
int p3dSourceCandidateTextureRangeReady(
    const int *face_texture_ids,unsigned map_capacity,
    unsigned mesh_triangles,unsigned first_triangle,
    unsigned triangle_count,unsigned texture_id,
    int source_colormap_approved,int normalized_paired_uv){
    if(!face_texture_ids || !source_colormap_approved || !normalized_paired_uv ||
       !mesh_triangles || mesh_triangles>600 ||
       !map_capacity || map_capacity>600 || mesh_triangles>map_capacity ||
       first_triangle>=mesh_triangles || !triangle_count ||
       triangle_count>mesh_triangles-first_triangle ||
       texture_id==P3D_SOURCE_MATERIAL_NO_TEXTURE ||
       texture_id>0x7fffffffu)
        return 0;
    for(unsigned i=first_triangle;i<first_triangle+triangle_count;i++)
        if(face_texture_ids[i]!=(int)texture_id)
            return 0;
    return 1;
}
