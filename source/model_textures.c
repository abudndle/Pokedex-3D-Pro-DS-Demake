#include "model_textures.h"
#include <stdio.h>
#include <string.h>
static unsigned rd16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
int p3dTextureManifestLoad(P3DTextureManifest *map,const char *path){
 unsigned char h[8],b[8];P3DTextureManifest tmp={0};FILE *f;
 if(!map)return 0;map->ready=0;
 if(!path)return 0;
 f=fopen(path,"rb");if(!f)return 0;
 if(fread(h,1,8,f)!=8||memcmp(h,"P3TX",4)!=0||rd16(h+4)!=1||
    rd16(h+6)>P3D_TEXTURE_MAX){fclose(f);return 0;}
 tmp.count=rd16(h+6);
 for(unsigned i=0;i<tmp.count;i++){
   if(fread(b,1,8,f)!=8){fclose(f);return 0;}
   P3DTextureEntry *e=&tmp.entries[i];
   e->id=(uint16_t)rd16(b);
   e->width=(uint16_t)rd16(b+2);e->height=(uint16_t)rd16(b+4);
   e->format=(uint16_t)rd16(b+6);
   if(!e->width||!e->height||e->width>256||e->height>256||
      (e->width&(e->width-1))||(e->height&(e->height-1))||
      e->format!=1||(i&&tmp.entries[i-1].id>=e->id)){fclose(f);return 0;}
 }
 if(fgetc(f)!=EOF){fclose(f);return 0;}
 fclose(f);tmp.ready=1;*map=tmp;return 1;
}
const P3DTextureEntry *p3dTextureFind(const P3DTextureManifest *map,unsigned id){
 if(!map||!map->ready)return NULL;
 for(unsigned i=0;i<map->count;i++){
   if(map->entries[i].id==id)return &map->entries[i];
   if(map->entries[i].id>id)break;
 }
 return NULL;
}
