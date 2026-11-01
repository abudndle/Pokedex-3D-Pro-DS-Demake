#include "source_color_ranges.h"
#include "source_material_texture_match.h"
#include <string.h>
int p3dSourceColorRangesBuild(P3DSourceColorRanges *out,
    const P3DSourceMaterialWords *words,
    const P3DSourceShaderCaps *caps,
    const P3DSourceMaterialMap *source,
    const P3DMaterialMap *candidate,
    const P3DTextureManifest *textures,
    unsigned model_id,unsigned triangles){
    unsigned src_index=0;
    if(!out)return 0;
    memset(out,0,sizeof(*out));
    if(!candidate||!source||!caps||!words||!textures||
       !p3dSourceMaterialWordsMatch(words,caps,source,model_id,triangles)||
       !p3dSourceMaterialTextureReferencesMatch(source,candidate,textures,
                                                 model_id,triangles)||
       candidate->count>P3D_MATERIAL_MAX)
        return 0;
    out->count=candidate->count;
    for(unsigned i=0;i<candidate->count;i++){
        const P3DMaterialRange *m=&candidate->ranges[i];
        const P3DSourceMaterialRange *original;
        const P3DSourceShaderMaterial *shader;
        unsigned first=m->first_triangle;
        unsigned t0,t1,color_id;
        while(src_index<source->count &&
              first >= (unsigned)source->ranges[src_index].first_triangle+
                       source->ranges[src_index].triangle_count)
            src_index++;
        if(src_index>=source->count)return 0;
        original=&source->ranges[src_index];
        if(original->material_index>=caps->count)return 0;
        shader=&caps->materials[original->material_index];
        /* Reject any *uninterpreted* original 3DS shader capabilities
         * instead of assigning a guessed diffuse/normal/effect sampler.
         * Only a sole source texture reference is a preview candidate. */
        if(shader->flags!=P3D_SHADER_CAP_COLORMAP)continue;
        t0=shader->texture0;t1=shader->texture1;
        if(t0!=P3D_SOURCE_MATERIAL_NO_TEXTURE &&
           t1!=P3D_SOURCE_MATERIAL_NO_TEXTURE && t0!=t1)continue;
        color_id=t0==P3D_SOURCE_MATERIAL_NO_TEXTURE?t1:t0;
        if(color_id==P3D_SOURCE_MATERIAL_NO_TEXTURE ||
           color_id!=m->texture_id)continue;
        out->enabled[i]=1;
        out->approved++;
    }
    /* A valid all-blocked model still renders the full source geometry,
     * without allocating any Nintendo DS texture VRAM. */
    out->ready=1;
    return 1;
}
