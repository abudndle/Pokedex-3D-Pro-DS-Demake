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
    int ok=p3dPhotoPngDecode(file,view->pixels,&w,&h);
    if(fclose(file)!=0)ok=0;
    if(!ok){
        for(unsigned i=0;i<P3D_PHOTO_PIXELS;i++)view->pixels[i]=0x8000;
        return 0;
    }
    view->width=(uint16_t)w;view->height=(uint16_t)h;view->ready=1;
    return 1;
}
void p3dPhotoViewerClose(P3DPhotoViewer *view){if(view)memset(view,0,sizeof(*view));}
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
