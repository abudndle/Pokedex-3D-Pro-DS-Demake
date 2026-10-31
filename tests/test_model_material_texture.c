#include "model_material_texture.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 P3DMaterialMap materials={0};
 P3DTextureManifest textures={0};
 assert(argc==4);
 assert(p3dMaterialMapLoad(&materials,argv[1],3));
 assert(p3dTextureManifestLoad(&textures,argv[2]));
 assert(p3dModelMaterialTexturesValid(&materials,&textures));
 assert(p3dModelTextureForTriangle(&materials,&textures,0)==12);
 assert(p3dModelTextureForTriangle(&materials,&textures,2)==13);
 assert(p3dModelTextureForTriangle(&materials,&textures,3)==-1);
 assert(p3dTextureManifestLoad(&textures,argv[3]));
 assert(!p3dModelMaterialTexturesValid(&materials,&textures));
 assert(p3dModelTextureForTriangle(&materials,&textures,0)==-1);
 puts("Model material texture references: PASS");
 return 0;
}
