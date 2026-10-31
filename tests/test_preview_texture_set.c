#include "preview_texture_set.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 static P3DTexturePixels scratch;
 P3DMaterialMap materials={0};
 P3DTextureManifest manifest={0};
 P3DPreviewTextureSet set={0};
 assert(argc==3);
 materials.ready=1;materials.count=3;
 materials.ranges[0]=(P3DMaterialRange){0,1,100,11};
 materials.ranges[1]=(P3DMaterialRange){1,1,101,12};
 materials.ranges[2]=(P3DMaterialRange){2,1,102,11};
 manifest.ready=1;manifest.count=2;
 manifest.entries[0]=(P3DTextureEntry){11,8,8,1};
 manifest.entries[1]=(P3DTextureEntry){12,8,8,1};
 assert(p3dPreviewTextureSetLoad(&set,&scratch,&materials,&manifest,argv[1]));
 assert(set.ready && set.count==2);
 assert(p3dPreviewTextureSetFind(&set,11));
 assert(p3dPreviewTextureSetFind(&set,12));
 assert(p3dPreviewTextureSetFind(&set,11)->gl_id!=
        p3dPreviewTextureSetFind(&set,12)->gl_id);
 assert(!p3dPreviewTextureSetFind(&set,13));
 assert(!scratch.ready);
 p3dPreviewTextureSetRelease(&set);
 assert(!set.ready && set.count==0);
 /* Second texture is missing. The loader must roll back the first. */
 assert(!p3dPreviewTextureSetLoad(&set,&scratch,&materials,&manifest,argv[2]));
 assert(!set.ready && set.count==0);
 /* Budget validation fails before any pixel reads or VRAM allocation. */
 manifest.entries[1].width=256;
 manifest.entries[1].height=256;
 assert(!p3dPreviewTextureSetLoad(&set,&scratch,&materials,&manifest,argv[1]));
 assert(!set.ready && set.count==0);
 manifest.entries[1].width=8;manifest.entries[1].height=8;
 manifest.entries[1].format=2;
 assert(!p3dPreviewTextureSetLoad(&set,&scratch,&materials,&manifest,argv[1]));
 assert(!set.ready && set.count==0);
 manifest.entries[1].format=1;
 manifest.ready=0;
 assert(!p3dPreviewTextureSetLoad(&set,&scratch,&materials,&manifest,argv[1]));
 assert(!set.ready && set.count==0);
 puts("Multi-material private texture VRAM set: PASS");
 return 0;
}
