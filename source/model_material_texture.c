#include "model_material_texture.h"
int p3dModelMaterialTexturesValid(const P3DMaterialMap *materials,
                                  const P3DTextureManifest *textures){
 if(!materials||!materials->ready||!textures||!textures->ready)return 0;
 for(unsigned i=0;i<materials->count;i++){
   if(!p3dTextureFind(textures,materials->ranges[i].texture_id))return 0;
 }
 return materials->count>0;
}
int p3dModelTextureForTriangle(const P3DMaterialMap *materials,
                               const P3DTextureManifest *textures,
                               unsigned triangle){
 if(!p3dModelMaterialTexturesValid(materials,textures))return -1;
 for(unsigned i=0;i<materials->count;i++){
   const P3DMaterialRange *r=&materials->ranges[i];
   if(triangle>=r->first_triangle &&
      triangle-r->first_triangle<r->triangle_count)return r->texture_id;
 }
 return -1;
}
