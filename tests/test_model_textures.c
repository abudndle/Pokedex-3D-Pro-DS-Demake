#include "model_textures.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 P3DTextureManifest m={0};
 assert(argc==3);
 assert(p3dTextureFind(&m,3)==NULL);
 assert(p3dTextureManifestLoad(&m,argv[1]));
 assert(m.count==2);
 assert(p3dTextureFind(&m,3)->width==64);
 assert(p3dTextureFind(&m,8)->height==128);
 assert(p3dTextureFind(&m,7)==NULL);
 assert(!p3dTextureManifestLoad(&m,argv[2]));
 assert(p3dTextureFind(&m,3)==NULL);
 puts("Texture reference manifest: PASS");
 return 0;
}
