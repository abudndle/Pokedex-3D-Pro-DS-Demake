#include "texture_asset.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 static P3DTexturePixels pixels;
 P3DTextureManifest manifest={0};
 assert(argc==4);
 assert(p3dTextureManifestLoad(&manifest,argv[1]));
 assert(p3dTextureAssetLoad(&pixels,&manifest,3,argv[2]));
 assert(pixels.ready&&pixels.width==8&&pixels.height==8);
 assert(!p3dTextureAssetLoad(&pixels,&manifest,4,argv[2]));
 assert(!pixels.ready);
 assert(!p3dTextureAssetLoad(&pixels,&manifest,3,argv[3]));
 assert(!pixels.ready);
 puts("Texture metadata/payload integration: PASS");
 return 0;
}
