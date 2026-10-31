#include "settings_images.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void){
 P3DSettingsImages s;
 p3dSettingsImagesInit(&s,0);
 assert(!p3dSettingsImagesTouch(&s,20,116,"photo.bmp",1));
 assert(s.image.mode==P3D_IMAGE_ORIGINAL);
 p3dSettingsImagesInit(&s,1);
 assert(!p3dSettingsImagesTouch(&s,20,116,"photo.bmp",0));
 assert(p3dSettingsImagesTouch(&s,20,116,"photo.bmp",1));
 assert(s.image.mode==P3D_IMAGE_CUSTOM);
 assert(strcmp(s.image.filename,"photo.bmp")==0);
 assert(p3dSettingsImagesTouch(&s,20,104,"photo.bmp",1));
 assert(s.image.mode==P3D_IMAGE_ORIGINAL);
 assert(!p3dSettingsImagesTouch(&s,250,104,"photo.bmp",1));
 puts("DS settings custom image touch controls: PASS");
 return 0;
}
