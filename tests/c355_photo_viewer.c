#define _POSIX_C_SOURCE 200809L
#include "photo_viewer.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
int main(int argc,char **argv){
    assert(argc==2);P3DPhotoAlbum album={0};static P3DPhotoViewer view;
    assert(p3dPhotoAlbumOpen(&album,argv[1]));
    assert(p3dPhotoViewerOpen(&view,&album,"AR_0001.png"));
    assert(view.active&&view.ready&&view.width==2&&view.height==1);
    assert(view.pixels[96*256]==0x801f); /* left red */
    assert(view.pixels[96*256+255]==0xfc00); /* right blue */
    assert(view.pixels[0]==0x8000); /* aspect-preserving letterbox */
    assert(p3dPhotoViewerOpen(&view,&album,"AR_0003.png"));
    assert(view.pixels[96*256]==0x8010&&view.pixels[96*256+255]==0x8000);
    assert(p3dPhotoViewerOpen(&view,&album,"AR_0013.png"));
    assert(view.width==640&&view.height==480);
    assert(view.pixels[0]==0x83e0&&view.pixels[P3D_PHOTO_PIXELS-1]==0x83e0);
    assert(p3dPhotoViewerOpen(&view,&album,"AR_0014.png"));
    assert(view.pixels[96*256]==0x801f&&view.pixels[96*256+255]==0xfc00);
    assert(p3dPhotoViewerOpen(&view,&album,"AR_0015.png"));
    assert(view.pixels[96*256]==0x801f&&view.pixels[96*256+255]==0xc000);
    assert(p3dPhotoViewerOpen(&view,&album,"AR_0019.png"));
    assert(view.pixels[96*256]==0x8000&&view.pixels[96*256+255]==0xfc00);
    assert(p3dPhotoViewerOpen(&view,&album,"AR_0021.png"));
    assert(p3dPhotoViewerOpen(&view,&album,"AR_0022.png"));
    const int bad[]={2,4,5,6,7,8,9,10,11,12,16,17,18,20};
    for(unsigned j=0;j<sizeof(bad)/sizeof(bad[0]);j++){
        char name[32];snprintf(name,sizeof(name),"AR_%04d.png",bad[j]);
        int opened=p3dPhotoViewerOpen(&view,&album,name);
        if(opened)fprintf(stderr,"Invalid fixture accepted: %s\n",name);
        assert(!opened);
        assert(!view.ready&&!view.width&&!view.height);
        for(unsigned i=0;i<P3D_PHOTO_PIXELS;i++)assert(view.pixels[i]==0x8000);
    }
    assert(!p3dPhotoViewerOpen(&view,&album,"AR_0002.png"));
    assert(!view.ready&&!view.width&&!view.height);
    for(unsigned i=0;i<P3D_PHOTO_PIXELS;i++)assert(view.pixels[i]==0x8000);
    assert(!p3dPhotoViewerOpen(&view,&album,"../AR_0001.png"));
    char path[400];snprintf(path,sizeof(path),"%s/AR_9999.png",argv[1]);
    assert(mkdir(path,0700)==0);
    assert(!p3dPhotoViewerOpen(&view,&album,"AR_9999.png"));
    snprintf(path,sizeof(path),"%s/AR_9998.png",argv[1]);
    assert(symlink("AR_0001.png",path)==0);
    assert(!p3dPhotoViewerOpen(&view,&album,"AR_9998.png"));
#ifdef __linux__
    snprintf(path,sizeof(path),"%s/AR_9997.png",argv[1]);
    assert(mkfifo(path,0600)==0);
    alarm(2); /* A regular-photo reader must not block on a replaced FIFO. */
    assert(!p3dPhotoViewerOpen(&view,&album,"AR_9997.png"));
    alarm(0);
#endif
    FILE *source=p3dPhotoAlbumRead(&album,"AR_0001.png");assert(source);
    assert(fputc(0,source)==EOF);assert(fclose(source)==0);
    p3dPhotoViewerClose(&view);assert(!view.active&&!view.ready);
    size_t offset=0,selected=6;
    assert(p3dPhotoAlbumStep(&offset,&selected,9,1));
    assert(offset==7&&selected==0);
    assert(p3dPhotoAlbumStep(&offset,&selected,9,1));
    assert(offset==7&&selected==1);
    assert(!p3dPhotoAlbumStep(&offset,&selected,9,1));
    assert(p3dPhotoAlbumStep(&offset,&selected,9,-1));
    assert(offset==7&&selected==0);
    assert(p3dPhotoAlbumStep(&offset,&selected,9,-1));
    assert(offset==0&&selected==6);
    offset=SIZE_MAX;selected=SIZE_MAX;
    assert(p3dPhotoAlbumStep(&offset,&selected,9,0));
    assert(offset==0&&selected==0);
    puts("C355 actual PNG pixels, fail-closed images and cross-page browsing: PASS");
    return 0;
}
