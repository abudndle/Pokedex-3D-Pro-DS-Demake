#include "source_shader_caps.h"
#include "source_material_texture_match.h"
#include <stdio.h>
#include <string.h>
#define P3SC_HEADER_BYTES 16u
#define P3SC_RECORD_BYTES 10u
static unsigned get16(const unsigned char *p){
    return (unsigned)p[0] | ((unsigned)p[1]<<8);
}
static uint32_t get32(const unsigned char *p){
    return (uint32_t)get16(p) | ((uint32_t)get16(p+2)<<16);
}
static uint32_t crc32_data(const unsigned char *p,unsigned size){
    uint32_t crc=0xffffffffu;
    for(unsigned i=0;i<size;i++){
        crc^=p[i];
        for(unsigned k=0;k<8;k++)
            crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
    }
    return crc^0xffffffffu;
}
int p3dSourceShaderCapsLoad(P3DSourceShaderCaps *out,const char *path,
                            unsigned model_id){
    unsigned char file[P3SC_HEADER_BYTES +
                       P3SC_RECORD_BYTES*P3D_SHADER_MAX_MATERIALS];
    FILE *f;
    unsigned count,got;
    if(!out)return 0;
    memset(out,0,sizeof(*out));
    if(!path||model_id>=738)return 0;
    f=fopen(path,"rb");
    if(!f)return 0;
    got=(unsigned)fread(file,1,sizeof(file),f);
    if(ferror(f)||fgetc(f)!=EOF){fclose(f);return 0;}
    fclose(f);
    if(got<P3SC_HEADER_BYTES||memcmp(file,"P3SC",4)!=0||
       get16(file+4)!=2||get16(file+6)!=model_id||
       get16(file+10)!=0)return 0;
    count=get16(file+8);
    if(!count||count>P3D_SHADER_MAX_MATERIALS||
       got!=P3SC_HEADER_BYTES+count*P3SC_RECORD_BYTES||
       crc32_data(file+P3SC_HEADER_BYTES,count*P3SC_RECORD_BYTES)!=get32(file+12))
        return 0;
    for(unsigned i=0;i<count;i++){
        const unsigned char *p=file+P3SC_HEADER_BYTES+i*P3SC_RECORD_BYTES;
        P3DSourceShaderMaterial *m=&out->materials[i];
        m->material_id=(uint16_t)get16(p);
        m->shader_index=(uint16_t)get16(p+2);
        m->texture0=(uint16_t)get16(p+4);
        m->texture1=(uint16_t)get16(p+6);
        m->flags=(uint16_t)get16(p+8);
        if(m->material_id!=i||
           (m->flags&~(P3D_SHADER_CAP_COLORMAP|P3D_SHADER_CAP_BUMPMAP|P3D_SHADER_CAP_OTHER)))
            return 0;
    }
    out->model_id=(uint16_t)model_id;
    out->count=(uint16_t)count;
    out->ready=1;
    return 1;
}
int p3dSourceShaderColorReferencesMatch(
    const P3DSourceShaderCaps *caps,
    const P3DSourceMaterialMap *source,
    const P3DMaterialMap *candidate,
    const P3DTextureManifest *textures,
    unsigned model_id,unsigned mesh_triangles){
    unsigned j=0;
    if(!caps||!caps->ready||caps->model_id!=model_id||
       !caps->count||caps->count>P3D_SHADER_MAX_MATERIALS||
       !p3dSourceMaterialTextureReferencesMatch(source,candidate,textures,
                                                 model_id,mesh_triangles))
        return 0;
    for(unsigned i=0;i<source->count;i++){
        const P3DSourceMaterialRange *s=&source->ranges[i];
        const P3DSourceShaderMaterial *cap;
        unsigned candidate_id,other_id,end=s->first_triangle+s->triangle_count;
        if(s->material_index>=caps->count)return 0;
        cap=&caps->materials[s->material_index];
        if(cap->material_id!=s->material_index ||
           cap->texture0!=s->source_texture0 ||
           cap->texture1!=s->source_texture1 ||
           !(cap->flags&P3D_SHADER_CAP_COLORMAP) ||
           /* CF_BUMPMAP indicates an additional source shader mapping.
            * With no decoded C5 sampler equations, even a single texture
            * reference is NOT evidence that it drives color-only output. */
           (cap->flags&(P3D_SHADER_CAP_BUMPMAP|P3D_SHADER_CAP_OTHER)))return 0;
        candidate_id=cap->texture0;
        other_id=cap->texture1;
        /* A source material with two DIFFERENT textures needs actual C5
         * shader sampler-slot decoding, even when CF_COLORMAP is present.
         * We cannot safely pick whichever texture has a color-ish name. */
        if(candidate_id!=P3D_SOURCE_MATERIAL_NO_TEXTURE &&
           other_id!=P3D_SOURCE_MATERIAL_NO_TEXTURE &&
           candidate_id!=other_id)return 0;
        if(candidate_id==P3D_SOURCE_MATERIAL_NO_TEXTURE)
            candidate_id=other_id;
        if(candidate_id==P3D_SOURCE_MATERIAL_NO_TEXTURE)return 0;
        while(j<candidate->count &&
              candidate->ranges[j].first_triangle<end){
            const P3DMaterialRange *m=&candidate->ranges[j++];
            if(m->material_id!=s->material_index||
               m->texture_id!=candidate_id)return 0;
        }
    }
    return j==candidate->count;
}
