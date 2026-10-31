#include "custom_images.h"
#include <string.h>
void p3dImageSettingsReset(P3DImageSettings *s){
 if(!s)return;
 s->mode=P3D_IMAGE_ORIGINAL;
 s->filename[0]=0;
}
int p3dImageFilenameValid(const char *filename){
 size_t n;
 if(!filename)return 0;
 n=strlen(filename);
 if(n<5||n>=P3D_CUSTOM_IMAGE_NAME_MAX)return 0;
 /* Allow a single local file name only: no path traversal or separators. */
 for(size_t i=0;i<n;i++){
  unsigned char ch=(unsigned char)filename[i];
  if(!((ch>='A'&&ch<='Z')||(ch>='a'&&ch<='z')||
       (ch>='0'&&ch<='9')||ch=='_'||ch=='-'||ch=='.'))return 0;
 }
 if(filename[0]=='.'||strstr(filename,".."))return 0;
 /* BMP is a practical on-device target; PNG/JPG require an explicit decoder. */
 const char *ext=filename+n-4;
 return ext[0]=='.'&&(ext[1]=='b'||ext[1]=='B')&&
        (ext[2]=='m'||ext[2]=='M')&&(ext[3]=='p'||ext[3]=='P');
}
int p3dImageSelectCustom(P3DImageSettings *s,const char *filename,int storage_ready,int image_exists){
 if(!s||!storage_ready||!image_exists||!p3dImageFilenameValid(filename))return 0;
 strcpy(s->filename,filename);s->mode=P3D_IMAGE_CUSTOM;return 1;
}
void p3dImageSelectOriginal(P3DImageSettings *s){p3dImageSettingsReset(s);}
int p3dImageUseCustom(const P3DImageSettings *s,int storage_ready,int image_exists){
 return s&&s->mode==P3D_IMAGE_CUSTOM&&storage_ready&&image_exists&&
        p3dImageFilenameValid(s->filename);
}
