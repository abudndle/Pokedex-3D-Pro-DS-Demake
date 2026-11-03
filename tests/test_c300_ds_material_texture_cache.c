#include "ds_material_texture_cache.h"
#include <assert.h>
#include <stdio.h>
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
    remove("texture.p3px");
    return 0;
}
