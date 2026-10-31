#include "ds_texture_upload.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 static P3DTexturePixels pixels;
 int id=0;
 assert(!p3dDsTextureUpload(&pixels,&id));
 pixels.ready=1;pixels.width=8;pixels.height=8;
 assert(p3dDsTextureUpload(&pixels,&id));
 assert(id>0);
 assert(!p3dDsTextureUpload(NULL,&id));
 assert(!p3dDsTextureUpload(&pixels,NULL));
 puts("DS texture upload interface: PASS");
 return 0;
}
