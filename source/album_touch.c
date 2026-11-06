#include "album_touch.h"
#include "photo_album.h"
int p3dAlbumListTouch(size_t shown,size_t selected,int visible,int x,int y,size_t *next){
 if(!visible||!next||!shown||shown>P3D_ALBUM_PAGE_MAX||selected>=shown||x<0||x>=256||y<0||y>=192)return 0;
 if(y>=P3D_ALBUM_NAV_ROW*8&&y<(P3D_ALBUM_NAV_ROW+1)*8){
  if(x<64)return P3D_ALBUM_TOUCH_PREV;
  if(x>=192)return P3D_ALBUM_TOUCH_NEXT;
  return 0;
 }
 if(x>=8&&x<248&&y>=P3D_ALBUM_LIST_ROW*8&&y<P3D_ALBUM_NAV_ROW*8){
  size_t target=(selected>=5?selected-4:0)+(size_t)(y-P3D_ALBUM_LIST_ROW*8)/16;
  if(target<shown){*next=target;return P3D_ALBUM_TOUCH_SELECT;}
 }
 if(x>=8&&x<128&&y>=P3D_ALBUM_ACTION_ROW*8)return P3D_ALBUM_TOUCH_OPEN;
 return 0;
}
int p3dAlbumViewerTouch(int visible,int x,int y){
 if(!visible||x<0||x>=256||y<0||y>=192)return 0;
 if(x>=8&&x<248&&y>=P3D_ALBUM_PLAY_ROW*8&&y<(P3D_ALBUM_PLAY_ROW+2)*8)return P3D_ALBUM_TOUCH_PLAY;
 if(x>=8&&x<248&&y>=P3D_ALBUM_RETURN_ROW*8&&y<(P3D_ALBUM_RETURN_ROW+1)*8)return P3D_ALBUM_TOUCH_LIST;
 if(y>=P3D_ALBUM_NAV_ROW*8&&y<(P3D_ALBUM_NAV_ROW+1)*8)return x<64?P3D_ALBUM_TOUCH_PREV:x>=192?P3D_ALBUM_TOUCH_NEXT:P3D_ALBUM_TOUCH_LIST;
 return 0;
}
