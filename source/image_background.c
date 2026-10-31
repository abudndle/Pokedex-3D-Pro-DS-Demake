#include "image_background.h"
#include "bmp_loader.h"
#include <stdio.h>
#include <string.h>
void p3dBackgroundClear(P3DImageBackground *out){
 if(!out)return;
 out->width=0;out->height=0;out->custom_active=0;
}
int p3dBackgroundLoad(P3DImageBackground *out,const P3DImageSettings *settings,const char *folder,int storage_ready){
 char path[384];int n,w=0,h=0;
 if(!out)return 0;
 p3dBackgroundClear(out);
 if(!settings||!folder||!out->pixels||!out->capacity||!storage_ready||
 settings->mode!=P3D_IMAGE_CUSTOM||
 !p3dImageFilenameValid(settings->filename))return 0;
 n=snprintf(path,sizeof(path),"%s/%s",folder,settings->filename);
 if(n<=0||(size_t)n>=sizeof(path))return 0;
 if(!p3dBmpDecode24(path,out->pixels,out->capacity,&w,&h))return 0;
 out->width=w;out->height=h;out->custom_active=1;
 return 1;
}
