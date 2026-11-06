#include "saved_entry_browser.h"
int p3dSavedEntryRow(unsigned visible_row){
 if(visible_row>=P3D_FAVORITES_MAX)return -1;
 return P3D_SAVED_ENTRY_FIRST_ROW+(int)visible_row*P3D_SAVED_ENTRY_ROW_STEP;
}
static int touch_row(int visible,int x,int y,int bottom){
 if(!visible||x<8||x>=248||y<P3D_SAVED_ENTRY_FIRST_ROW*8||y>=bottom)return -1;
 return (y-P3D_SAVED_ENTRY_FIRST_ROW*8)/(P3D_SAVED_ENTRY_ROW_STEP*8);
}
int p3dFavoriteTouch(const P3DMenu *menu,int controls_visible,int x,int y){
 int row=touch_row(controls_visible,x,y,176);
 if(!menu||row<0||menu->favorites_count<1||
    menu->favorites_count>P3D_FAVORITES_MAX||row>=menu->favorites_count)return -1;
 if(menu->favorites[row]<0||menu->favorites[row]>=P3D_RECORD_SPECIES)return -1;
 return row;
}
int p3dRecentTouch(const P3DRecords *records,int cursor,int controls_visible,int x,int y){
 int row=touch_row(controls_visible,x,y,168),index;
 if(!records||cursor<0||cursor>=P3D_RECORD_RECENT||row<0||row>=P3D_SAVED_RECENT_PAGE_SIZE)return -1;
 index=(cursor/P3D_SAVED_RECENT_PAGE_SIZE)*P3D_SAVED_RECENT_PAGE_SIZE+row;
 if(index>=P3D_RECORD_RECENT||records->recent[index]>=P3D_RECORD_SPECIES)return -1;
 return index;
}
