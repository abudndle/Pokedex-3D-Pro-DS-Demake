#include "preview_texture_set.h"
#include "model_material_texture.h"
#include "texture_asset.h"
#include "ds_texture_upload.h"
#include <stdio.h>
#include <string.h>
#ifndef C7_TEST_HOST
#include <nds.h>
#endif
void p3dPreviewTextureSetRelease(P3DPreviewTextureSet *set){
 if(!set)return;
#ifndef C7_TEST_HOST
 glBindTexture(0,0);
 for(unsigned i=0;i<set->count;i++){
   int id=set->entries[i].gl_id;
   if(id>0)glDeleteTextures(1,&id);
 }
#endif
 memset(set,0,sizeof(*set));
}
const P3DPreviewTexture *p3dPreviewTextureSetFind(const P3DPreviewTextureSet *set,
                                                 unsigned texture_id){
 if(!set||!set->ready)return NULL;
 for(unsigned i=0;i<set->count;i++)
   if(set->entries[i].id==texture_id)return &set->entries[i];
 return NULL;
}
int p3dPreviewTextureSetLoad(P3DPreviewTextureSet *set,
                            P3DTexturePixels *scratch,
                            const P3DMaterialMap *materials,
                            const P3DTextureManifest *manifest,
                            const char *texture_directory){
 unsigned bytes=0;
 char path[128];
 if(!set)return 0;
 p3dPreviewTextureSetRelease(set);
 if(!scratch||!texture_directory||!p3dModelMaterialTexturesValid(materials,manifest))
   return 0;
 /* Validate all distinct material references and VRAM budget before uploading
  * anything. Repeated material ranges share their one texture allocation. */
 for(unsigned i=0;i<materials->count;i++){
   unsigned id=materials->ranges[i].texture_id;
   const P3DTextureEntry *entry=p3dTextureFind(manifest,id);
   int found=0;
   if(!entry||entry->width<8||entry->height<8)return 0;
   for(unsigned j=0;j<set->count;j++)
     if(set->entries[j].id==id){found=1;break;}
   if(found)continue;
   if(set->count>=P3D_PREVIEW_TEXTURE_LIMIT){p3dPreviewTextureSetRelease(set);return 0;}
   unsigned size=(unsigned)entry->width*entry->height*2u;
   if(size>P3D_PREVIEW_TEXTURE_VRAM_BYTES-bytes){
     p3dPreviewTextureSetRelease(set);return 0;
   }
   P3DPreviewTexture *out=&set->entries[set->count++];
   out->id=id;out->width=entry->width;out->height=entry->height;
   bytes+=size;
 }
 for(unsigned i=0;i<set->count;i++){
   P3DPreviewTexture *out=&set->entries[i];
   int n=snprintf(path,sizeof(path),"%s/t%03u.p3px",texture_directory,out->id);
   if(n<0||(unsigned)n>=sizeof(path)||
      !p3dTextureAssetLoad(scratch,manifest,out->id,path)||
      !p3dDsTextureUpload(scratch,&out->gl_id)){
     scratch->ready=0;
     p3dPreviewTextureSetRelease(set);
     return 0;
   }
 }
 scratch->ready=0;
 set->ready=1;
 return 1;
}
