#include "album_touch.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
int main(void){
 size_t next=99;
 /* Row 13 draws at y104, and its 16px cell must not select row 14. */
 assert(p3dAlbumListTouch(7,0,1,80,116,&next)==P3D_ALBUM_TOUCH_SELECT&&next==0);
 for(size_t row=0;row<5;row++){
  assert(p3dAlbumListTouch(7,0,1,24,104+(int)row*16,&next)==P3D_ALBUM_TOUCH_SELECT&&next==row);
  assert(p3dAlbumListTouch(7,6,1,24,104+(int)row*16,&next)==P3D_ALBUM_TOUCH_SELECT&&next==row+2);
 }
 assert(p3dAlbumListTouch(7,4,1,80,172,&next)==P3D_ALBUM_TOUCH_SELECT&&next==4);
 assert(p3dAlbumListTouch(7,4,1,80,188,&next)==P3D_ALBUM_TOUCH_OPEN);
 assert(p3dAlbumListTouch(7,4,1,80,180,&next)==0);
 assert(p3dAlbumListTouch(7,4,1,24,180,&next)==P3D_ALBUM_TOUCH_PREV);
 assert(p3dAlbumListTouch(7,4,1,220,180,&next)==P3D_ALBUM_TOUCH_NEXT);
 next=99;
 assert(!p3dAlbumListTouch(1,0,1,24,120,&next)&&next==99);
 assert(!p3dAlbumListTouch(7,0,0,24,104,&next));
 assert(!p3dAlbumListTouch(0,0,1,80,188,&next));
 assert(!p3dAlbumListTouch(SIZE_MAX,0,1,80,188,&next));
 assert(!p3dAlbumListTouch(7,7,1,80,188,&next));
 assert(!p3dAlbumListTouch(7,0,1,80,188,NULL));
 assert(!p3dAlbumListTouch(7,0,1,-1,104,&next));
 assert(!p3dAlbumListTouch(7,0,1,256,104,&next));
 assert(!p3dAlbumListTouch(7,0,1,24,192,&next));
 assert(!p3dAlbumListTouch(7,0,1,24,103,&next));
 assert(p3dAlbumViewerTouch(1,24,156)==P3D_ALBUM_TOUCH_PLAY);
 assert(p3dAlbumViewerTouch(1,24,164)==P3D_ALBUM_TOUCH_LIST);
 assert(p3dAlbumViewerTouch(1,24,180)==P3D_ALBUM_TOUCH_PREV);
 assert(p3dAlbumViewerTouch(1,220,180)==P3D_ALBUM_TOUCH_NEXT);
 assert(p3dAlbumViewerTouch(1,128,180)==P3D_ALBUM_TOUCH_LIST);
 assert(!p3dAlbumViewerTouch(1,128,140));
 assert(!p3dAlbumViewerTouch(0,128,148));
 assert(!p3dAlbumViewerTouch(1,256,148));
 assert(!p3dAlbumViewerTouch(1,128,192));
 puts("C400 Album filename, open, playback and list touch controls: PASS");return 0;
}
