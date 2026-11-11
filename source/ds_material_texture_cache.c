#include "ds_material_texture_cache.h"
#include "texture_asset.h"
#include "model_material_texture.h"
#include <string.h>
#ifdef C7_TEST_HOST
static void release_texture(int id){(void)id;}
#else
#include <nds.h>
static void release_texture(int id){if(id>0)glDeleteTextures(1,&id);}
#endif
typedef struct {
    uint16_t ids[P3D_DS_TEXTURE_CACHE_MAX];
    unsigned count,bytes;
} TextureBudget;
static int budget_add(TextureBudget *budget,const P3DTextureManifest *manifest,
                      unsigned id){
    for(unsigned i=0;i<budget->count;i++)
        if(budget->ids[i]==id)return 1;
    const P3DTextureEntry *entry=p3dTextureFind(manifest,id);
    if(!entry || entry->format!=1 || entry->width<8 || entry->height<8 ||
       entry->width>256 || entry->height>256 ||
       (entry->width&(entry->width-1)) || (entry->height&(entry->height-1)) ||
       budget->count>=P3D_DS_TEXTURE_CACHE_MAX)return 0;
    unsigned size=(unsigned)entry->width*(unsigned)entry->height*2u;
    if(size>P3D_DS_TEXTURE_VRAM_BYTES-budget->bytes)return 0;
    budget->ids[budget->count++]=(uint16_t)id;
    budget->bytes+=size;
    return 1;
}
int p3dDsMaterialTextureBudgetValid(const P3DMaterialMap *materials,
    const P3DTextureManifest *manifest,unsigned triangle_count){
    TextureBudget budget={0};
    if(!p3dModelMaterialTexturesMatchMesh(materials,manifest,triangle_count))
        return 0;
    for(unsigned i=0;i<materials->count;i++)
        if(!budget_add(&budget,manifest,materials->ranges[i].texture_id))return 0;
    return budget.count>0;
}
int p3dDsMaterialTextureCacheFits(const P3DDsMaterialTextureCache *cache,
    const unsigned *needed,unsigned count){
    TextureBudget budget={0};
    if(!cache || !cache->ready || !cache->manifest ||
       cache->manifest->count>P3D_TEXTURE_MAX || !needed || !count ||
       count>P3D_DS_TEXTURE_CACHE_MAX || cache->count>P3D_DS_TEXTURE_CACHE_MAX)
        return 0;
    for(unsigned i=0;i<cache->count;i++)
        if(!budget_add(&budget,cache->manifest,cache->ids[i]))return 0;
    for(unsigned i=0;i<count;i++)
        if(!budget_add(&budget,cache->manifest,needed[i]))return 0;
    return 1;
}
int p3dDsMaterialTextureCacheInit(P3DDsMaterialTextureCache *cache,
    const P3DTextureManifest *manifest,P3DDsTexturePathResolver resolver,
    void *resolver_context){
    if(!cache)return 0;
    memset(cache,0,sizeof(*cache));
    if(!manifest||!manifest->ready||!manifest->count||
       manifest->count>P3D_TEXTURE_MAX||!resolver)return 0;
    cache->manifest=manifest;
    cache->resolve_path=resolver;
    cache->resolver_context=resolver_context;
    cache->ready=1;
    return 1;
}
int p3dDsMaterialTextureCacheGet(P3DDsMaterialTextureCache *cache,
    unsigned texture_id,P3DTexturePixels *scratch,int *hardware_texture_id){
    const P3DTextureEntry *entry;
    const char *path;
    int uploaded=0;
    if(!hardware_texture_id)return 0;
    *hardware_texture_id=0;
    if(!cache||!cache->ready||!scratch)return 0;
    for(unsigned i=0;i<cache->count;i++){
        if(cache->ids[i]==texture_id){
            *hardware_texture_id=cache->texture_ids[i];
            return 1;
        }
    }
    entry=p3dTextureFind(cache->manifest,texture_id);
    if(!entry||entry->format!=1||
       cache->count>=P3D_DS_TEXTURE_CACHE_MAX)return 0;
    path=cache->resolve_path(cache->resolver_context,texture_id);
    if(!path||!p3dTextureAssetLoad(scratch,cache->manifest,texture_id,path)||
       !p3dDsTextureUpload(scratch,&uploaded)||uploaded<=0)return 0;
    cache->ids[cache->count]=(uint16_t)texture_id;
    cache->texture_ids[cache->count]=uploaded;
    cache->count++;
    *hardware_texture_id=uploaded;
    return 1;
}
void p3dDsMaterialTextureCacheDestroy(P3DDsMaterialTextureCache *cache){
    if(!cache)return;
    for(unsigned i=0;i<cache->count;i++)release_texture(cache->texture_ids[i]);
    memset(cache,0,sizeof(*cache));
}
