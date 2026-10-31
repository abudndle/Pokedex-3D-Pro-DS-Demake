#include "ds_texture_upload.h"
#ifdef C7_TEST_HOST
static int next_test_id=1;
int p3dDsTextureUpload(const P3DTexturePixels *pixels,int *texture_id){
 if(!pixels||!pixels->ready||!texture_id)return 0;
 *texture_id=next_test_id++;
 return 1;
}
#else
#include <nds.h>
int p3dDsTextureUpload(const P3DTexturePixels *pixels,int *texture_id){
 int id=0;
 if(!pixels||!pixels->ready||!texture_id)return 0;
 if(pixels->width<8||pixels->height<8)return 0;
 int sx=0,sy=0;
 for(unsigned n=pixels->width;n>8;n>>=1)sx++;
 for(unsigned n=pixels->height;n>8;n>>=1)sy++;
 glGenTextures(1,&id);
 if(id<=0)return 0;
 glBindTexture(0,id);
 glTexImage2D(0,0,GL_RGB,sx,sy,0,
              TEXGEN_OFF,(const void *)pixels->pixels);
 *texture_id=id;
 return 1;
}
#endif
