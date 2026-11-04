#ifndef P3D_PHOTO_VIEWER_H
#define P3D_PHOTO_VIEWER_H
#include "photo_album.h"
#include "photo_png.h"
#include <stdint.h>
#define P3D_PHOTO_WIDTH 256u
#define P3D_PHOTO_HEIGHT 192u
#define P3D_PHOTO_PIXELS (P3D_PHOTO_WIDTH*P3D_PHOTO_HEIGHT)
/* DS adaptation: five seconds at the native VBlank cadence (~60 Hz). */
#define P3D_PHOTO_DWELL_FRAMES 300u
typedef struct {
    _Alignas(4) uint16_t pixels[P3D_PHOTO_PIXELS];
    uint16_t width,height;
    unsigned char active,ready;
    char name[12];
    uint16_t photo_id;
    P3DPhotoIdentity identity;
    unsigned short dwell_frames;
    unsigned char playing;
} P3DPhotoViewer;
int p3dPhotoViewerOpen(P3DPhotoViewer *view,const P3DPhotoAlbum *album,const char *name);
void p3dPhotoViewerClose(P3DPhotoViewer *view);
int p3dPhotoViewerPlay(P3DPhotoViewer *view);
int p3dPhotoViewerTick(P3DPhotoViewer *view);
int p3dPhotoViewerAdvance(P3DPhotoViewer *view,const P3DPhotoAlbum *album,
                           size_t *offset,size_t *selected);
/* Reopen only the same complete file, relocating its list selection when
 * new photos have shifted the saved rank. Failure closes the viewer and
 * leaves the caller's list selection unchanged. CRC is not authentication. */
int p3dPhotoViewerRestore(P3DPhotoViewer *view,const P3DPhotoAlbum *album,
                           unsigned photo_id,P3DPhotoIdentity identity,
                           size_t *offset,size_t *selected);
int p3dPhotoAlbumStep(size_t *offset,size_t *selected,size_t total,int direction);
#endif
