#include "image_background.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 P3DImageSettings s;
 uint16_t pixels[4];
 P3DImageBackground output={pixels,4,0,0,0};
 if(argc!=2)return 2;
 p3dImageSettingsReset(&s);
 assert(!p3dBackgroundLoad(&output,&s,argv[1],1));
 assert(!output.custom_active);
 assert(p3dImageSelectCustom(&s,"image.bmp",1,1));
 assert(!p3dBackgroundLoad(&output,&s,argv[1],0));
 assert(p3dBackgroundLoad(&output,&s,argv[1],1));
 assert(output.width==2&&output.height==2&&output.custom_active);
 assert(pixels[0]==0xfc00u);
 p3dImageSelectOriginal(&s);
 assert(!p3dBackgroundLoad(&output,&s,argv[1],1));
 assert(!output.custom_active);
 puts("Custom background runtime loading: PASS");
 return 0;
}
