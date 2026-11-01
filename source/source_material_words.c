#include "source_material_words.h"
#include <stdio.h>
#include <string.h>
#define HEADER_BYTES 16u
#define RECORD_BYTES 52u
static uint16_t rd16(const unsigned char *p){
    return (uint16_t)((unsigned)p[0]|((unsigned)p[1]<<8));
}
static uint32_t rd32(const unsigned char *p){
    return (uint32_t)rd16(p)|((uint32_t)rd16(p+2)<<16);
}
static uint32_t crc_step(uint32_t crc,const unsigned char *p,unsigned n){
    for(unsigned i=0;i<n;i++){
        crc^=p[i];
        for(unsigned j=0;j<8;j++)
            crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
    }
    return crc;
}
int p3dSourceMaterialWordsLoad(P3DSourceMaterialWords *out,
                               const char *path,unsigned expected_model_id){
    FILE *file;
    unsigned char head[HEADER_BYTES],row[RECORD_BYTES];
    unsigned count;
    uint32_t crc;
    if(!out)return 0;
    memset(out,0,sizeof(*out));
    if(!path||expected_model_id>=738)return 0;
    file=fopen(path,"rb");
    if(!file)return 0;
    if(fread(head,1,HEADER_BYTES,file)!=HEADER_BYTES||
       memcmp(head,"P3SW",4)!=0||rd16(head+4)!=1||
       rd16(head+6)!=expected_model_id||rd16(head+10)!=0)
        goto fail;
    count=rd16(head+8);
    if(!count||count>P3D_SHADER_MAX_MATERIALS)goto fail;
    crc=0xffffffffu;
    for(unsigned i=0;i<count;i++){
        if(fread(row,1,RECORD_BYTES,file)!=RECORD_BYTES)goto fail;
        crc=crc_step(crc,row,RECORD_BYTES);
        for(unsigned j=0;j<P3D_SOURCE_WORDS_PER_MATERIAL;j++)
            out->words[i][j]=rd32(row+j*4u);
    }
    if(fgetc(file)!=EOF||ferror(file)||
       (crc^0xffffffffu)!=rd32(head+12))goto fail;
    fclose(file);
    out->model_id=(uint16_t)expected_model_id;
    out->count=(uint16_t)count;
    out->ready=1;
    return 1;
fail:
    fclose(file);
    /* Clear every incomplete record, not merely ready: callers might reuse
     * this object across original Pokémon species/form changes. */
    memset(out,0,sizeof(*out));
    return 0;
}
int p3dSourceMaterialWordsMatch(
    const P3DSourceMaterialWords *words,
    const P3DSourceShaderCaps *caps,
    const P3DSourceMaterialMap *source,
    unsigned expected_model_id,unsigned expected_triangles){
    if(!words||!caps||!source||!words->ready||!caps->ready||
       !source->ready||expected_model_id>=738||!expected_triangles||
       expected_triangles>600||words->model_id!=expected_model_id||
       caps->model_id!=expected_model_id||source->model_id!=expected_model_id||
       source->triangle_count!=expected_triangles||
       !words->count||words->count>P3D_SHADER_MAX_MATERIALS||
       words->count!=caps->count||
       !source->count||source->count>P3D_SOURCE_MATERIAL_MAX_RANGES)
        return 0;
    for(unsigned i=0;i<words->count;i++){
        const uint32_t *w=words->words[i];
        const P3DSourceShaderMaterial *m=&caps->materials[i];
        if(m->material_id!=i||
           (w[0]&65535u)!=m->shader_index||
           (w[1]&65535u)!=m->texture0||
           (w[1]>>16)!=m->texture1)
            return 0;
    }
    for(unsigned i=0;i<source->count;i++){
        const P3DSourceMaterialRange *r=&source->ranges[i];
        const uint32_t *w;
        if(r->material_index>=words->count)return 0;
        w=words->words[r->material_index];
        if((w[1]&65535u)!=r->source_texture0||
           (w[1]>>16)!=r->source_texture1)return 0;
    }
    return 1;
}
