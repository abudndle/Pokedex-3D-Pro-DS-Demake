#include "photo_album.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
 P3DPhotoAlbum a;char names[2][32];size_t total=0;char path[400];FILE *f;
 if(argc!=2)return 2;
 assert(p3dPhotoAlbumOpen(&a,argv[1]));
 for(int i=1;i<=3;i++){snprintf(path,sizeof(path),"%s/AR_%04d.png",argv[1],i);f=fopen(path,"wb");assert(f);fclose(f);}
 assert(p3dPhotoAlbumPage(&a,names,2,0,&total)==2&&total==3);
 assert(strcmp(names[0],"AR_0003.png")==0&&strcmp(names[1],"AR_0002.png")==0);
 assert(p3dPhotoAlbumPage(&a,names,2,2,&total)==1&&strcmp(names[0],"AR_0001.png")==0);
 assert(!p3dPhotoAlbumDelete(&a,"../bad.png"));
 assert(p3dPhotoAlbumDelete(&a,"AR_0002.png"));
 assert(p3dPhotoAlbumPage(&a,names,2,0,&total)==2&&total==2);
 puts("Photo album browse/delete: PASS");return 0;
}
