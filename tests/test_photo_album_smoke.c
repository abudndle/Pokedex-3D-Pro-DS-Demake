#include "photo_album.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
 P3DPhotoAlbum a={0};char names[8][32];size_t total=0;char path[400];FILE *f;
 if(argc!=2)return 2;
 assert(p3dPhotoAlbumOpen(&a,argv[1]));
 for(int i=1;i<=9;i++){snprintf(path,sizeof(path),"%s/AR_%04d.png",argv[1],i);f=fopen(path,"wb");assert(f);fclose(f);}
 assert(p3dPhotoAlbumPage(&a,names,2,0,&total)==2&&total==9);
 assert(strcmp(names[0],"AR_0009.png")==0&&strcmp(names[1],"AR_0008.png")==0);
 assert(p3dPhotoAlbumPage(&a,names,2,8,&total)==1&&strcmp(names[0],"AR_0001.png")==0);
 assert(p3dPhotoAlbumPage(&a,names,8,0,&total)==7&&total==9);
 assert(strcmp(names[6],"AR_0003.png")==0);
 assert(p3dPhotoAlbumPage(&a,names,2,SIZE_MAX,&total)==0&&total==9);
 assert(p3dPhotoAlbumPage(&a,names,2,SIZE_MAX-1,&total)==0&&total==9);
 assert(p3dPhotoAlbumPage(&a,names,0,0,&total)==0&&total==9);
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
 puts("C267 fail-closed SD Album path and bounded pagination: PASS");return 0;
}
