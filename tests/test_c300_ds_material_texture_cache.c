#include "ds_material_texture_cache.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static const char *resolve(void *ctx,unsigned id){
    (void)ctx;return id==7?"texture.p3px":NULL;
}
int main(void){
    P3DTextureManifest manifest={0};
    P3DDsMaterialTextureCache cache;
    P3DTexturePixels *scratch;
    int first=0,second=0;
    FILE *f=fopen("texture.p3px","wb");
    assert(f);
    {const unsigned char h[10]={'P','3','P','X',1,0,8,0,8,0};
     assert(fwrite(h,1,sizeof(h),f)==sizeof(h));
     for(unsigned i=0;i<64;i++){const unsigned char px[2]={0x1f,0x00};assert(fwrite(px,1,2,f)==2);}}
    fclose(f);
    manifest.ready=1;manifest.count=1;
    manifest.entries[0].id=7;manifest.entries[0].width=8;
    manifest.entries[0].height=8;manifest.entries[0].format=1;
    scratch=(P3DTexturePixels *)malloc(sizeof(*scratch));assert(scratch);
    assert(p3dDsMaterialTextureCacheInit(&cache,&manifest,resolve,NULL));
    assert(p3dDsMaterialTextureCacheGet(&cache,7,scratch,&first));
    assert(first>0&&cache.count==1);
    assert(p3dDsMaterialTextureCacheGet(&cache,7,scratch,&second));
    assert(second==first&&cache.count==1);
    assert(!p3dDsMaterialTextureCacheGet(&cache,8,scratch,&second));
    assert(second==0);
    p3dDsMaterialTextureCacheDestroy(&cache);
    assert(cache.count==0&&!cache.ready);
    free(scratch);
    /* C303: distinct textures consume the VRAM bank once each; duplicate
     * ranges do not count as duplicate uploads. No proprietary fixtures. */
    {
        P3DMaterialMap materials={0};
        P3DTextureManifest textures={0};
        materials.ready=1;materials.count=2;
        materials.ranges[0].first_triangle=0;
        materials.ranges[0].triangle_count=1;
        materials.ranges[0].texture_id=7;
        materials.ranges[1].first_triangle=1;
        materials.ranges[1].triangle_count=1;
        materials.ranges[1].texture_id=7;
        textures.ready=1;textures.count=1;
        textures.entries[0].id=7;
        textures.entries[0].width=256;
        textures.entries[0].height=256;
        textures.entries[0].format=1;
        assert(p3dDsMaterialTextureBudgetValid(&materials,&textures,2));
        assert(!p3dDsMaterialTextureBudgetValid(&materials,&textures,3));
        /* One extra 8x8 ID exceeds the 128 KiB budget. */
        textures.count=2;textures.entries[1].id=8;
        textures.entries[1].width=8;
        textures.entries[1].height=8;
        textures.entries[1].format=1;
        materials.ranges[1].texture_id=8;
        assert(!p3dDsMaterialTextureBudgetValid(&materials,&textures,2));
        textures.entries[0].width=128;
        assert(p3dDsMaterialTextureBudgetValid(&materials,&textures,2));
        textures.entries[0].width=8;
        /* Nine distinct textures exceed the eight-allocation limit. */
        materials.count=9;textures.count=9;
        for(unsigned i=0;i<9;i++){
            materials.ranges[i].first_triangle=(uint16_t)i;
            materials.ranges[i].triangle_count=1;
            materials.ranges[i].texture_id=(uint16_t)(i+1);
            textures.entries[i].id=(uint16_t)(i+1);
            textures.entries[i].width=8;
            textures.entries[i].height=8;
            textures.entries[i].format=1;
        }
        assert(!p3dDsMaterialTextureBudgetValid(&materials,&textures,9));
        /* A nine-entry manifest is legal if only eight distinct IDs are
         * actually referenced and allocated. */
        {P3DDsMaterialTextureCache more={0};
         assert(p3dDsMaterialTextureCacheInit(&more,&textures,resolve,NULL));
         p3dDsMaterialTextureCacheDestroy(&more);}
        materials.count=8;textures.count=8;
        assert(p3dDsMaterialTextureBudgetValid(&materials,&textures,8));
        textures.entries[0].format=2;
        assert(!p3dDsMaterialTextureBudgetValid(&materials,&textures,8));
    }
    remove("texture.p3px");
    return 0;
}
