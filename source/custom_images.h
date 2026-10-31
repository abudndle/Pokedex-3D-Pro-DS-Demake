#ifndef P3D_CUSTOM_IMAGES_H
#define P3D_CUSTOM_IMAGES_H
#include <stddef.h>
#define P3D_CUSTOM_IMAGE_NAME_MAX 64
typedef enum { P3D_IMAGE_ORIGINAL=0, P3D_IMAGE_CUSTOM=1 } P3DImageMode;
typedef struct {
 P3DImageMode mode;
 char filename[P3D_CUSTOM_IMAGE_NAME_MAX];
} P3DImageSettings;
/* Original visuals are always the safe default. A custom selection is enabled
 * only when the user picks an available image and a storage driver can read it. */
void p3dImageSettingsReset(P3DImageSettings *s);
int p3dImageFilenameValid(const char *filename);
int p3dImageSelectCustom(P3DImageSettings *s,const char *filename,int storage_ready,int image_exists);
void p3dImageSelectOriginal(P3DImageSettings *s);
int p3dImageUseCustom(const P3DImageSettings *s,int storage_ready,int image_exists);
#endif
