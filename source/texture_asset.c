#include "texture_asset.h"
int p3dTextureAssetLoad(P3DTexturePixels *pixels,const P3DTextureManifest *manifest,
                        unsigned texture_id,const char *path){
 const P3DTextureEntry *entry;
 if(!pixels)return 0;
 pixels->ready=0;
 entry=p3dTextureFind(manifest,texture_id);
 if(!entry||entry->format!=1||!p3dTexturePixelsLoad(pixels,path))return 0;
 if(pixels->width!=entry->width||pixels->height!=entry->height){
    pixels->ready=0;
    return 0;
 }
 return 1;
}
