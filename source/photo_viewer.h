#ifndef P3D_PHOTO_VIEWER_H
#define P3D_PHOTO_VIEWER_H
#include "photo_album.h"
#include <stdint.h>
#define P3D_PHOTO_WIDTH 256u
#define P3D_PHOTO_HEIGHT 192u
#define P3D_PHOTO_PIXELS (P3D_PHOTO_WIDTH*P3D_PHOTO_HEIGHT)
typedef struct {
    _Alignas(4) uint16_t pixels[P3D_PHOTO_PIXELS];
    uint16_t width,height;
    unsigned char active,ready;
    char name[12];
} P3DPhotoViewer;
int p3dPhotoViewerOpen(P3DPhotoViewer *view,const P3DPhotoAlbum *album,const char *name);
void p3dPhotoViewerClose(P3DPhotoViewer *view);
int p3dPhotoAlbumStep(size_t *offset,size_t *selected,size_t total,int direction);
#endif
