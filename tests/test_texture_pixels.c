#include "texture_pixels.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 static P3DTexturePixels img;
 assert(argc==3);
 assert(p3dTexturePixelsLoad(&img,argv[1]));
 assert(img.ready&&img.width==8&&img.height==8);
 assert(img.pixels[0]==0x7fff&&img.pixels[63]==0x001f);
 assert(!p3dTexturePixelsLoad(&img,argv[2]));
 assert(!img.ready);
 puts("Texture pixel payload validation: PASS");
 return 0;
}
