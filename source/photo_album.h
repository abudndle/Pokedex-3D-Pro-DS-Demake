#ifndef P3D_PHOTO_ALBUM_H
#define P3D_PHOTO_ALBUM_H
#include <stddef.h>
#define P3D_SD_PHOTO_FOLDER "sd:/Pokedex 3D Pro/Photos"
#define P3D_PHOTO_PATH_MAX 320
#define P3D_ALBUM_PAGE_MAX 7
typedef struct {char folder[P3D_PHOTO_PATH_MAX];} P3DPhotoAlbum;
int p3dPhotoAlbumOpen(P3DPhotoAlbum *album,const char *photo_folder);
size_t p3dPhotoAlbumPage(const P3DPhotoAlbum *album,char names[][32],size_t page_size,size_t offset,size_t *total);
int p3dPhotoAlbumDelete(P3DPhotoAlbum *album,const char *photo_name);
#endif
