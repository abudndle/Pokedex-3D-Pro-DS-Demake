#include "photo_viewer.h"
#include "photo_png.h"
#include <string.h>
int p3dPhotoViewerOpen(P3DPhotoViewer *view,const P3DPhotoAlbum *album,const char *name){
    if(!view)return 0;
    memset(view,0,sizeof(*view));view->active=1;
    if(name&&strlen(name)==11)memcpy(view->name,name,12);
    for(unsigned i=0;i<P3D_PHOTO_PIXELS;i++)view->pixels[i]=0x8000;
    FILE *file=p3dPhotoAlbumRead(album,name);
    if(!file)return 0;
    unsigned w=0,h=0;
    P3DPhotoIdentity identity;
    int ok=p3dPhotoPngDecode(file,view->pixels,&w,&h,&identity);
    if(fclose(file)!=0)ok=0;
    if(!ok){
        for(unsigned i=0;i<P3D_PHOTO_PIXELS;i++)view->pixels[i]=0x8000;
        return 0;
    }
    view->width=(uint16_t)w;view->height=(uint16_t)h;view->ready=1;
    view->identity=identity;
    view->photo_id=(uint16_t)((name[3]-'0')*1000+(name[4]-'0')*100+
                              (name[5]-'0')*10+(name[6]-'0'));
    return 1;
}
void p3dPhotoViewerClose(P3DPhotoViewer *view){if(view)memset(view,0,sizeof(*view));}
int p3dPhotoViewerPlay(P3DPhotoViewer *view){
    if(!view)return 0;
    view->dwell_frames=0;
    view->playing=(unsigned char)(view->active&&view->ready&&!view->playing);
    return view->playing;
}
int p3dPhotoViewerTick(P3DPhotoViewer *view){
    if(!view||!view->active||!view->ready||!view->playing)return 0;
    if(++view->dwell_frames<P3D_PHOTO_DWELL_FRAMES)return 0;
    view->dwell_frames=0;return 1;
}
int p3dPhotoViewerAdvance(P3DPhotoViewer *view,const P3DPhotoAlbum *album,
                           size_t *offset,size_t *selected){
    size_t next_offset=0,next_selected=0,total=0;
    char names[P3D_ALBUM_PAGE_MAX][32];
    if(!view||!view->active||!view->ready||!view->playing)return 0;
    view->playing=0;view->dwell_frames=0;
    if(!offset||!selected||
       !p3dPhotoAlbumLocate(album,view->photo_id,&next_offset,&next_selected))return 0;
    size_t shown=p3dPhotoAlbumPage(album,names,P3D_ALBUM_PAGE_MAX,next_offset,&total);
    if(!shown||!total)return 0;
    size_t rank=next_offset+next_selected;
    rank=rank+1<total?rank+1:0;
    next_offset=(rank/P3D_ALBUM_PAGE_MAX)*P3D_ALBUM_PAGE_MAX;
    next_selected=rank%P3D_ALBUM_PAGE_MAX;
    shown=p3dPhotoAlbumPage(album,names,P3D_ALBUM_PAGE_MAX,next_offset,&total);
    if(next_selected>=shown)return 0;
    *offset=next_offset;*selected=next_selected;
    if(!p3dPhotoViewerOpen(view,album,names[next_selected]))return 0;
    view->playing=1;return 1;
}
int p3dPhotoViewerRestore(P3DPhotoViewer *view,const P3DPhotoAlbum *album,
                           unsigned photo_id,P3DPhotoIdentity identity,
                           size_t *offset,size_t *selected){
    char name[12];size_t next_offset=0,next_selected=0;
    if(!view)return 0;
    p3dPhotoViewerClose(view);
    if(!offset||!selected||photo_id>=P3D_PHOTO_ID_COUNT||
       !identity.bytes||identity.bytes>P3D_PHOTO_FILE_MAX||
       !p3dPhotoAlbumLocate(album,photo_id,&next_offset,&next_selected))return 0;
    (void)snprintf(name,sizeof(name),"AR_%04u.png",photo_id);
    if(!p3dPhotoViewerOpen(view,album,name)||view->identity.bytes!=identity.bytes||
       view->identity.checksum!=identity.checksum){
        p3dPhotoViewerClose(view);return 0;
    }
    *offset=next_offset;*selected=next_selected;
    return 1;
}
int p3dPhotoAlbumStep(size_t *offset,size_t *selected,size_t total,int direction){
    if(!offset||!selected)return 0;
    size_t previous_offset=*offset,previous_selected=*selected,index=0;
    if(total && *offset<total && *selected<P3D_ALBUM_PAGE_MAX &&
       *selected<total-*offset)index=*offset+*selected;
    if(total){
        if(direction<0&&index)index--;
        else if(direction>0&&index<total-1)index++;
    }
    *offset=(index/P3D_ALBUM_PAGE_MAX)*P3D_ALBUM_PAGE_MAX;
    *selected=index%P3D_ALBUM_PAGE_MAX;
    return *offset!=previous_offset||*selected!=previous_selected;
}
