#include "menu_layout.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 for(int n=0;n<10;n++)for(int cursor=-2;cursor<n+2;cursor++){
   size_t start=p3dMenuVisibleStart((size_t)n,cursor);
   if(n==0){assert(p3dMenuHitTest(20,105,0,cursor)==-1);continue;}
   for(int row=0;row<6;row++){
     int hit=p3dMenuHitTest(20,100+11*row+5,(size_t)n,cursor);
     assert(hit==(start+(size_t)row<(size_t)n?(int)(start+(size_t)row):-1) || (start+(size_t)row>P3D_MENU_VISIBLE_ROWS-1));
   }
 }
 /* Lists longer than six rows must keep their actual saved cursor.
  * Previously cursor 6/7 in a ten-entry list jumped to index 9,
  * shifting the visible touchscreen hitboxes to the final page. */
 assert(p3dMenuClampCursor(6,10)==6);
 assert(p3dMenuClampCursor(7,10)==7);
 assert(p3dMenuClampCursor(10,10)==9);
 assert(p3dMenuVisibleStart(10,6)==2);
 assert(p3dMenuVisibleStart(10,7)==3);
 assert(p3dMenuVisibleStart(10,9)==4);
 assert(p3dMenuHitTest(20,105,10,6)==2);
 assert(p3dMenuHitTest(20,105,10,7)==3);
 assert(p3dMenuHitTest(20,155,10,6)==7);
 assert(p3dMenuHitTest(13,105,6,0)==-1);
 assert(p3dFeatureHitTest(20,100,8)==0);
 assert(p3dAlbumPageTouch(20,185)==-1);
 assert(p3dAlbumPageTouch(220,185)==1);
 assert(p3dAlbumDeleteTouch(40,130)==1);
 assert(p3dAlbumDeleteTouch(200,130)==-1);
 puts("Menu layout and touch hitboxes: PASS");
 return 0;
}
