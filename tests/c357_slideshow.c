#include "photo_viewer.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 assert(argc==2);P3DPhotoAlbum album={0};static P3DPhotoViewer v;
 assert(p3dPhotoAlbumOpen(&album,argv[1]));
 assert(p3dPhotoViewerOpen(&v,&album,"AR_0009.png"));
 assert(p3dPhotoViewerPlay(&v));
 for(unsigned i=0;i<299;i++)assert(!p3dPhotoViewerTick(&v));
 assert(p3dPhotoViewerTick(&v));
 size_t offset=0,selected=0;
 assert(p3dPhotoViewerAdvance(&v,&album,&offset,&selected));
 assert(v.photo_id==8&&v.playing&&offset==0&&selected==1);
 assert(!p3dPhotoViewerPlay(&v));
 for(unsigned i=0;i<600;i++)assert(!p3dPhotoViewerTick(&v));
 assert(v.photo_id==8);
 assert(p3dPhotoViewerPlay(&v));
 for(unsigned i=0;i<299;i++)assert(!p3dPhotoViewerTick(&v));
 assert(p3dPhotoViewerTick(&v));
 assert(p3dPhotoViewerOpen(&v,&album,"AR_0001.png"));
 assert(!v.playing);
 assert(p3dPhotoViewerPlay(&v));
 assert(p3dPhotoViewerAdvance(&v,&album,&offset,&selected));
 assert(v.photo_id==9&&offset==0&&selected==0&&v.playing);
 assert(p3dPhotoViewerOpen(&v,&album,"AR_0003.png"));
 assert(p3dPhotoViewerPlay(&v));
 assert(p3dPhotoViewerAdvance(&v,&album,&offset,&selected));
 assert(v.photo_id==2&&offset==7&&selected==0&&v.playing);
 assert(p3dPhotoViewerRestore(&v,&album,2,v.identity,&offset,&selected));
 assert(!v.playing&&!p3dPhotoViewerTick(&v));
 assert(p3dPhotoViewerOpen(&v,&album,"AR_0009.png"));
 assert(p3dPhotoViewerPlay(&v));
 /* A corrupt next file stops playback without repeated retries or file writes. */
 char path[400];snprintf(path,sizeof(path),"%s/AR_0008.png",argv[1]);
 FILE *f=fopen(path,"wb");assert(f);assert(fputs("invalid",f)>=0);assert(!fclose(f));
 assert(!p3dPhotoViewerAdvance(&v,&album,&offset,&selected));
 assert(!v.playing&&!v.ready&&v.active&&v.photo_id==0);
 assert(!p3dPhotoViewerPlay(&v));
 for(unsigned i=0;i<600;i++)assert(!p3dPhotoViewerTick(&v));
 p3dPhotoViewerClose(&v);assert(!p3dPhotoViewerPlay(&v));
 puts("C357 timed advance, pause, wrap and corrupt-photo stop: PASS");return 0;
}
