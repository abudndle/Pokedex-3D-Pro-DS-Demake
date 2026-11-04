#define _POSIX_C_SOURCE 200809L
#include "photo_viewer.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
static uint32_t crc_byte(uint32_t c,unsigned char byte){
 c^=byte;for(int k=0;k<8;k++)c=(c>>1)^((c&1u)?0xedb88320u:0);return c;
}
int main(int argc,char **argv){
 assert(argc==2);P3DPhotoAlbum album={0};static P3DPhotoViewer view;
 assert(p3dPhotoAlbumOpen(&album,argv[1]));
 assert(p3dPhotoViewerOpen(&view,&album,"AR_0001.png"));
 assert(view.photo_id==1);
 P3DPhotoIdentity original=view.identity;
 FILE *f=p3dPhotoAlbumRead(&album,"AR_0001.png");assert(f);
 uint32_t crc=~0u;unsigned count=0;int byte;
 while((byte=fgetc(f))!=EOF){crc=crc_byte(crc,(unsigned char)byte);count++;}
 assert(!ferror(f)&&!fclose(f));
 assert(original.checksum==~crc&&original.bytes==count);
 size_t offset=0,selected=0;
 assert(p3dPhotoViewerRestore(&view,&album,1,original,&offset,&selected));
 assert(view.active&&view.ready&&view.photo_id==1&&offset==21&&selected==0);
 /* Adding a newer filename must change rank, not restored photo identity. */
 char path[400];snprintf(path,sizeof(path),"%s/AR_9999.png",argv[1]);
 f=fopen(path,"wb");assert(f);assert(fputs("not decoded when locating",f)>=0);assert(!fclose(f));
 assert(p3dPhotoViewerRestore(&view,&album,1,original,&offset,&selected));
 assert(view.photo_id==1&&offset==21&&selected==1);
 P3DPhotoIdentity wrong=original;wrong.checksum^=1;
 assert(!p3dPhotoViewerRestore(&view,&album,1,wrong,&offset,&selected));
 assert(!view.active&&!view.ready&&offset==21&&selected==1);
 wrong=original;wrong.bytes++;
 assert(!p3dPhotoViewerRestore(&view,&album,1,wrong,&offset,&selected));
 /* Replacing a valid file with another valid photo cannot revive it. */
 assert(p3dPhotoViewerOpen(&view,&album,"AR_0003.png"));
 P3DPhotoIdentity other=view.identity;
 assert(!p3dPhotoViewerRestore(&view,&album,1,other,&offset,&selected));
 snprintf(path,sizeof(path),"%s/AR_0001.png",argv[1]);
 FILE *replacement=p3dPhotoAlbumRead(&album,"AR_0003.png");assert(replacement);
 f=fopen(path,"wb");assert(f);
 while((byte=fgetc(replacement))!=EOF)assert(fputc(byte,f)!=EOF);
 assert(!ferror(replacement)&&!fclose(replacement)&&!fclose(f));
 assert(!p3dPhotoViewerRestore(&view,&album,1,original,&offset,&selected));
 assert(!view.active&&!view.ready);
 snprintf(path,sizeof(path),"%s/AR_0001.png",argv[1]);assert(unlink(path)==0);
 assert(!p3dPhotoViewerRestore(&view,&album,1,original,&offset,&selected));
 assert(!view.active&&!view.ready);
 assert(!p3dPhotoAlbumLocate(&album,10000,&offset,&selected));
 assert(!p3dPhotoViewerRestore(&view,&album,10000,original,&offset,&selected));
 puts("C356 whole-file identity, stable-ID relocation and changed/missing-photo rejection: PASS");
 return 0;
}
