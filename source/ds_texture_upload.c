#include "ds_texture_upload.h"
static int p3dTextureDimensionsValid(const P3DTexturePixels *pixels){
 unsigned w,h;
 if(!pixels||!pixels->ready)return 0;
 w=pixels->width; h=pixels->height;
 return w>=8 && h>=8 && w<=256 && h<=256 &&
        !(w&(w-1)) && !(h&(h-1));
}
#ifdef C7_TEST_HOST
static int next_test_id=1;
int p3dDsTextureUpload(const P3DTexturePixels *pixels,int *texture_id){
 if(!texture_id||!p3dTextureDimensionsValid(pixels))return 0;
 *texture_id=next_test_id++;
 return 1;
}
#else
#include <nds.h>
int p3dDsTextureUpload(const P3DTexturePixels *pixels,int *texture_id){
 int id=0,sx=0,sy=0;
 if(!texture_id||!p3dTextureDimensionsValid(pixels))return 0;
 *texture_id=0;
 for(unsigned n=pixels->width;n>8;n>>=1)sx++;
 for(unsigned n=pixels->height;n>8;n>>=1)sy++;
 glGenTextures(1,&id);
 if(id<=0)return 0;
 glBindTexture(0,id);
 /* libnds GL_RGB converts opaque RGB555 input to DS 16-bit direct texels. */
 if(!glTexImage2D(0,0,GL_RGB,sx,sy,0,
                  TEXGEN_OFF,(const void *)pixels->pixels)){
    glDeleteTextures(1,&id);
    glBindTexture(0,0);
    return 0;
 }
 *texture_id=id;
 return 1;
}
#endif
