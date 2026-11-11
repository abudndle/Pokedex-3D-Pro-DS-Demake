#include "menu_layout.h"
int p3dMenuClampCursor(int cursor,size_t count){
 if(!count)return -1;
 if(cursor<0)return 0;
 if((size_t)cursor>=count)return (int)count-1;
 return cursor;
}
size_t p3dMenuVisibleStart(size_t count,int cursor){
 size_t first,selected;int idx=p3dMenuClampCursor(cursor,count);
 if(idx<0||count<=P3D_MENU_VISIBLE_ROWS)return 0;
 selected=(size_t)idx;
 first=selected>=P3D_MENU_VISIBLE_ROWS-1?selected-(P3D_MENU_VISIBLE_ROWS-2):0;
 if(first+P3D_MENU_VISIBLE_ROWS>count)first=count-P3D_MENU_VISIBLE_ROWS;
 return first;
}
int p3dMenuHitTest(int x,int y,size_t count,int cursor){
 int slot,selected;size_t index;
 if(x<P3D_MENU_LEFT||x>=P3D_MENU_RIGHT||y<P3D_MENU_FIRST_Y||
 y>=P3D_MENU_FIRST_Y+P3D_MENU_ROW_HEIGHT*P3D_MENU_VISIBLE_ROWS)return -1;
 selected=p3dMenuClampCursor(cursor,count);
 if(selected<0)return -1;
 slot=(y-P3D_MENU_FIRST_Y)/P3D_MENU_ROW_HEIGHT;
 index=p3dMenuVisibleStart(count,selected)+(size_t)slot;
 return index<count?(int)index:-1;
}
int p3dFeatureHitTest(int x,int y,size_t row_count){
 int row;
 if(x<P3D_MENU_LEFT||x>=P3D_MENU_RIGHT||y<P3D_MENU_FIRST_Y||
 y>=P3D_MENU_FIRST_Y+P3D_MENU_ROW_HEIGHT*P3D_MENU_VISIBLE_ROWS)return -1;
 row=(y-P3D_MENU_FIRST_Y)/P3D_MENU_ROW_HEIGHT;
 return row<(int)row_count?row:-1;
}
int p3dAlbumPageTouch(int x,int y){
 if(y<178||y>=192||x<0||x>=256)return 0;
 return x<88?-1:x>=168?1:0;
}
int p3dAlbumDeleteTouch(int x,int y){
 if(x<12||x>=246||y<126||y>=150)return 0;
 return x<124?1:-1;
}
