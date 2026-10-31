#include "settings_images.h"
#include "menu_layout.h"
#include <string.h>
void p3dSettingsImagesInit(P3DSettingsImages *s,int storage_ready){
 if(!s)return;
 memset(s,0,sizeof(*s));s->storage_ready=storage_ready?1:0;
 p3dImageSettingsReset(&s->image);
}
int p3dSettingsImagesApply(P3DSettingsImages *s,const char *file,int exists){
 if(!s)return 0;
 if(s->selected_row==0){p3dImageSelectOriginal(&s->image);return 1;}
 if(s->selected_row!=1)return 0;
 s->custom_file_exists=exists?1:0;
 return p3dImageSelectCustom(&s->image,file,s->storage_ready,exists);
}
int p3dSettingsImagesTouch(P3DSettingsImages *s,int x,int y,const char *file,int exists){
 int selected;
 if(!s)return 0;
 selected=p3dFeatureHitTest(x,y,P3D_SETTINGS_IMAGE_ROWS);
 if(selected<0)return 0;
 s->selected_row=selected;
 return p3dSettingsImagesApply(s,file,exists);
}
const char *p3dSettingsImagesStatus(const P3DSettingsImages *s){
 if(!s)return "Unavailable";
 if(s->image.mode==P3D_IMAGE_ORIGINAL)return "Original background";
 if(!s->storage_ready)return "Storage not available";
 if(!s->custom_file_exists)return "Custom image missing";
 return "Custom BMP selected";
}
