#ifndef __NDS__
#define _POSIX_C_SOURCE 200809L
#endif
#include "photo_album.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#ifndef __NDS__
#include <sys/stat.h>
#include <unistd.h>
#endif
int main(int argc,char **argv){
 P3DPhotoAlbum a={0};char names[8][32];size_t total=0;char path[400];FILE *f;
 if(argc!=2)return 2;
 assert(p3dPhotoAlbumOpen(&a,argv[1]));
 for(int i=1;i<=9;i++){snprintf(path,sizeof(path),"%s/AR_%04d.png",argv[1],i);f=fopen(path,"wb");assert(f);fclose(f);}
 assert(p3dPhotoAlbumPage(&a,names,2,0,&total)==2&&total==9);
 assert(strcmp(names[0],"AR_0009.png")==0&&strcmp(names[1],"AR_0008.png")==0);
 /* The photo above the requested row disappears before confirmation. */
 char requested[12];memcpy(requested,names[1],sizeof(requested));
 assert(p3dPhotoAlbumDelete(&a,names[0]));
 assert(p3dPhotoAlbumPage(&a,names,2,0,&total)==2&&total==8);
 assert(!strcmp(names[1],"AR_0007.png"));
 assert(!p3dPhotoAlbumConfirmDelete(&a,requested,names[1]));
 assert(p3dPhotoAlbumPage(&a,names,2,0,&total)==2&&total==8);
 assert(!strcmp(names[0],requested)&&!strcmp(names[1],"AR_0007.png"));
 assert(!p3dPhotoAlbumConfirmDelete(&a,requested,NULL));
 assert(p3dPhotoAlbumConfirmDelete(&a,requested,names[0]));
 assert(p3dPhotoAlbumPage(&a,names,2,0,&total)==2&&total==7);
 for(int i=8;i<=9;i++){
  snprintf(path,sizeof(path),"%s/AR_%04d.png",argv[1],i);
  f=fopen(path,"wb");assert(f);assert(!fclose(f));
 }
 assert(p3dPhotoAlbumPage(&a,names,2,8,&total)==1&&strcmp(names[0],"AR_0001.png")==0);
 assert(p3dPhotoAlbumPage(&a,names,8,0,&total)==7&&total==9);
 assert(strcmp(names[6],"AR_0003.png")==0);
 assert(p3dPhotoAlbumPage(&a,names,2,SIZE_MAX,&total)==0&&total==9);
 assert(p3dPhotoAlbumPage(&a,names,2,SIZE_MAX-1,&total)==0&&total==9);
 assert(p3dPhotoAlbumPage(&a,names,0,0,&total)==0&&total==9);
#ifndef __NDS__
 /* Host symlink/dir entries must not be counted or removed as saved photos.
  * Real FAT does not expose POSIX symlinks, but can contain directories. */
 snprintf(path,sizeof(path),"%s/AR_0010.png",argv[1]);assert(mkdir(path,0700)==0);
 assert(!p3dPhotoAlbumDelete(&a,"AR_0010.png"));
 snprintf(path,sizeof(path),"%s/AR_0011.png",argv[1]);assert(symlink("AR_0001.png",path)==0);
 assert(!p3dPhotoAlbumDelete(&a,"AR_0011.png"));
 assert(p3dPhotoAlbumPage(&a,names,2,0,&total)==2&&total==9);
#endif
 /* Delete the only photo on page two and keep the nearest surviving row. */
 assert(p3dPhotoAlbumDelete(&a,"AR_0002.png"));
 size_t offset=P3D_ALBUM_PAGE_MAX,selected=0;
 assert(p3dPhotoAlbumPage(&a,names,P3D_ALBUM_PAGE_MAX,offset,&total)==1&&total==8);
 assert(!strcmp(names[0],"AR_0001.png"));
 assert(p3dPhotoAlbumConfirmDelete(&a,"AR_0001.png",names[0]));
 p3dPhotoAlbumClampSelection(total-1,&offset,&selected);
 assert(offset==0&&selected==6);
 assert(p3dPhotoAlbumPage(&a,names,P3D_ALBUM_PAGE_MAX,offset,&total)==7&&total==7);
 assert(!strcmp(names[selected],"AR_0003.png"));
 p3dPhotoAlbumClampSelection(5,&offset,&selected);
 assert(offset==0&&selected==4);
 p3dPhotoAlbumClampSelection(0,&offset,&selected);
 assert(offset==0&&selected==0);
 for(int i=1;i<=2;i++){
  snprintf(path,sizeof(path),"%s/AR_%04d.png",argv[1],i);
  f=fopen(path,"wb");assert(f);assert(!fclose(f));
 }
 assert(!p3dPhotoAlbumDelete(&a,"../bad.png"));
 assert(p3dPhotoAlbumDelete(&a,"AR_0002.png"));
 assert(p3dPhotoAlbumPage(&a,names,2,0,&total)==2&&total==8);
 /* Failed reopen must revoke stale SD album access, including delete. */
 assert(!p3dPhotoAlbumOpen(&a,"invalid"));
 assert(!a.folder[0]);
 assert(!p3dPhotoAlbumDelete(&a,"AR_0001.png"));
 assert(p3dPhotoAlbumPage(&a,names,2,0,&total)==0&&total==0);
 assert(p3dPhotoAlbumOpen(&a,argv[1]));
 assert(p3dPhotoAlbumOpen(&a,a.folder));
 assert(!p3dPhotoAlbumOpen(&a,NULL));
 assert(!a.folder[0]);
 assert(p3dPhotoAlbumOpen(&a,argv[1]));
 assert(p3dPhotoAlbumPage(&a,names,2,0,&total)==2&&total==8);
 /* C270: deep FAT Album pages must not require repeated directory scans.
  * Test >1000 sparse IDs, descending order, page boundaries and overflow. */
 for(int i=1000;i<2024;i++){
  snprintf(path,sizeof(path),"%s/AR_%04d.png",argv[1],i);
  f=fopen(path,"wb");assert(f);fclose(f);
 }
 assert(p3dPhotoAlbumPage(&a,names,7,0,&total)==7&&total==1032);
 assert(strcmp(names[0],"AR_2023.png")==0&&strcmp(names[6],"AR_2017.png")==0);
 assert(p3dPhotoAlbumPage(&a,names,7,1023,&total)==7&&total==1032);
 assert(strcmp(names[0],"AR_1000.png")==0&&strcmp(names[1],"AR_0009.png")==0);
 assert(strcmp(names[6],"AR_0004.png")==0);
 assert(p3dPhotoAlbumPage(&a,names,7,1031,&total)==1&&total==1032);
 assert(strcmp(names[0],"AR_0001.png")==0);
 assert(p3dPhotoAlbumPage(&a,names,7,1032,&total)==0&&total==1032);
 assert(p3dPhotoAlbumPage(&a,names,7,SIZE_MAX,&total)==0&&total==1032);
 puts("C270 bounded single-pass SD Album pagination: PASS");return 0;
}
