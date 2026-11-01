#include "model_material_texture.h"

/* Validate source-derived material coverage, not only whether each texture ID
 * appears somewhere in a manifest. A stray/overlapping range can otherwise
 * bind the wrong Pokémon texture to valid geometry without any loader error.
 * The exact-match path additionally checks the preview's triangle count. */
static int valid_bindings(const P3DMaterialMap *materials,
                          const P3DTextureManifest *textures,
                          unsigned mesh_triangles){
 unsigned cursor=0;
 if(!materials||!materials->ready||!textures||!textures->ready||
    materials->count==0||materials->count>P3D_MATERIAL_MAX||
    textures->count==0||textures->count>P3D_TEXTURE_MAX)return 0;
 for(unsigned i=0;i<textures->count;i++){
   const P3DTextureEntry *entry=&textures->entries[i];
   unsigned w=entry->width,h=entry->height;
   if(w<8||h<8||w>256||h>256||(w&(w-1))||(h&(h-1))||
      entry->format!=1||(i&&textures->entries[i-1].id>=entry->id))
     return 0;
 }
 for(unsigned i=0;i<materials->count;i++){
   const P3DMaterialRange *range=&materials->ranges[i];
   if(range->first_triangle!=cursor||!range->triangle_count||
      !p3dTextureFind(textures,range->texture_id))return 0;
   cursor+=range->triangle_count;
   if(mesh_triangles && cursor>mesh_triangles)return 0;
 }
 return cursor>0 && (!mesh_triangles || cursor==mesh_triangles);
}
int p3dModelMaterialTexturesValid(const P3DMaterialMap *materials,
                                  const P3DTextureManifest *textures){
 return valid_bindings(materials,textures,0);
}
int p3dModelMaterialTexturesMatchMesh(const P3DMaterialMap *materials,
                                      const P3DTextureManifest *textures,
                                      unsigned mesh_triangles){
 if(!mesh_triangles)return 0;
 return valid_bindings(materials,textures,mesh_triangles);
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
