#include "custom_images.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void){
 P3DImageSettings s;
 p3dImageSettingsReset(&s);
 assert(!p3dImageUseCustom(&s,1,1));
 assert(!p3dImageSelectCustom(&s,"../../private.bmp",1,1));
 assert(!p3dImageSelectCustom(&s,"my_image.png",1,1));
 assert(!p3dImageSelectCustom(&s,"my_image.bmp",0,1));
 assert(!p3dImageSelectCustom(&s,"my_image.bmp",1,0));
 assert(p3dImageSelectCustom(&s,"my_image.BMP",1,1));
 assert(p3dImageUseCustom(&s,1,1));
 assert(!p3dImageUseCustom(&s,0,1));
 assert(!p3dImageUseCustom(&s,1,0));
 assert(strcmp(s.filename,"my_image.BMP")==0);
 p3dImageSelectOriginal(&s);
 assert(s.mode==P3D_IMAGE_ORIGINAL);
 puts("DS-mode custom image selection: PASS");
 return 0;
}
