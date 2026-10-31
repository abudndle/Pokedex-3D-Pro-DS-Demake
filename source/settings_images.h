#ifndef P3D_SETTINGS_IMAGES_H
#define P3D_SETTINGS_IMAGES_H
#include "custom_images.h"
#include <stddef.h>
#define P3D_SETTINGS_IMAGE_ROWS 2
typedef struct {P3DImageSettings image;int selected_row;int storage_ready;int custom_file_exists;} P3DSettingsImages;
void p3dSettingsImagesInit(P3DSettingsImages *state,int storage_ready);
int p3dSettingsImagesTouch(P3DSettingsImages *state,int x,int y,const char *custom_file,int file_exists);
int p3dSettingsImagesApply(P3DSettingsImages *state,const char *custom_file,int file_exists);
const char *p3dSettingsImagesStatus(const P3DSettingsImages *state);
#endif
