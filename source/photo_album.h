#ifndef P3D_PHOTO_ALBUM_H
#define P3D_PHOTO_ALBUM_H
#include <stddef.h>
#include <stdio.h>
#define P3D_SD_PHOTO_FOLDER "sd:/Pokedex 3D Pro/Photos"
#define P3D_PHOTO_PATH_MAX 320
#define P3D_ALBUM_PAGE_MAX 7
#define P3D_PHOTO_ID_COUNT 10000u
typedef struct {char folder[P3D_PHOTO_PATH_MAX];} P3DPhotoAlbum;
int p3dPhotoAlbumOpen(P3DPhotoAlbum *album,const char *photo_folder);
size_t p3dPhotoAlbumPage(const P3DPhotoAlbum *album,char names[][32],size_t page_size,size_t offset,size_t *total);
int p3dPhotoAlbumDelete(P3DPhotoAlbum *album,const char *photo_name);
/* Read-only regular-file handle; never accepts arbitrary paths or symlinks. */
FILE *p3dPhotoAlbumRead(const P3DPhotoAlbum *album,const char *photo_name);
/* One bounded directory scan. Failure leaves both selection fields intact. */
int p3dPhotoAlbumLocate(const P3DPhotoAlbum *album,unsigned photo_id,
                         size_t *offset,size_t *selected);
#endif
