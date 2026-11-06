#include "saved_entry_browser.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
static void favorites(void){
 P3DMenu menu;memset(&menu,0,sizeof(menu));menu.favorites_count=6;
 for(int i=0;i<6;i++)menu.favorites[i]=i==5?648:i;
 P3DMenu before=menu;
 /* The visible first favorite previously ignored all touchscreen input. */
 assert(p3dFavoriteTouch(&menu,1,24,95)==0);
 for(int row=0;row<6;row++){
  assert(p3dSavedEntryRow((unsigned)row)==11+row*2);
  int first=88+row*16,last=row==5?175:first+15;
  for(int y=first;y<=last;y++){
   assert(p3dFavoriteTouch(&menu,1,8,y)==row);
   assert(p3dFavoriteTouch(&menu,1,247,y)==row);
  }
 }
 assert(!memcmp(&menu,&before,sizeof(menu)));
 assert(p3dSavedEntryRow(6)==-1);assert(p3dSavedEntryRow(UINT_MAX)==-1);
 const int points[][2]={{7,88},{248,88},{8,87},{8,176},{-1,-1},{256,192}};
 for(unsigned i=0;i<sizeof(points)/sizeof(points[0]);i++)
  assert(p3dFavoriteTouch(&menu,1,points[i][0],points[i][1])==-1);
 assert(p3dFavoriteTouch(&menu,0,24,95)==-1);
 assert(p3dFavoriteTouch(NULL,1,24,95)==-1);
 assert(!memcmp(&menu,&before,sizeof(menu)));
 for(int count=1;count<=6;count++){
  menu.favorites_count=count;before=menu;
  assert(p3dFavoriteTouch(&menu,1,24,88+(count-1)*16)==count-1);
  assert(p3dFavoriteTouch(&menu,1,24,88+count*16)==-1);
  assert(!memcmp(&menu,&before,sizeof(menu)));
 }
 const int bad_counts[]={-1,0,7,INT_MAX};
 for(unsigned i=0;i<sizeof(bad_counts)/sizeof(bad_counts[0]);i++){
  menu.favorites_count=bad_counts[i];before=menu;
  assert(p3dFavoriteTouch(&menu,1,24,95)==-1);
  assert(!memcmp(&menu,&before,sizeof(menu)));
 }
 menu.favorites_count=6;
 menu.favorites[2]=-1;before=menu;
 assert(p3dFavoriteTouch(&menu,1,24,120)==-1);
 assert(p3dFavoriteTouch(&menu,1,24,88)==0);
 assert(!memcmp(&menu,&before,sizeof(menu)));
 menu.favorites[2]=649;before=menu;
 assert(p3dFavoriteTouch(&menu,1,24,120)==-1);
 assert(!memcmp(&menu,&before,sizeof(menu)));
}
static void recent(void){
 P3DRecords records;memset(&records,0,sizeof(records));
 for(int i=0;i<8;i++)records.recent[i]=(uint16_t)(i==7?648:i);
 P3DRecords before=records;
 for(int cursor=0;cursor<8;cursor++){
  int base=cursor<5?0:5;
  for(int row=0;row<5;row++)for(int y=88+row*16;y<104+row*16;y++){
   int expected=base+row<8?base+row:-1;
   assert(p3dRecentTouch(&records,cursor,1,8,y)==expected);
   assert(p3dRecentTouch(&records,cursor,1,247,y)==expected);
  }
 }
 assert(!memcmp(&records,&before,sizeof(records)));
 const int points[][2]={{7,88},{248,88},{8,87},{8,168},{8,176},{-1,-1},{256,192}};
 for(unsigned i=0;i<sizeof(points)/sizeof(points[0]);i++)
  assert(p3dRecentTouch(&records,0,1,points[i][0],points[i][1])==-1);
 const int bad_cursors[]={INT_MIN,-1,8,INT_MAX};
 for(unsigned i=0;i<sizeof(bad_cursors)/sizeof(bad_cursors[0]);i++)
  assert(p3dRecentTouch(&records,bad_cursors[i],1,24,95)==-1);
 assert(p3dRecentTouch(&records,0,0,24,95)==-1);
 assert(p3dRecentTouch(NULL,0,1,24,95)==-1);
 assert(!memcmp(&records,&before,sizeof(records)));
 records.recent[6]=P3D_RECORD_NO_SPECIES;before=records;
 assert(p3dRecentTouch(&records,5,1,24,104)==-1);
 assert(p3dRecentTouch(&records,5,1,24,120)==7);
 assert(!memcmp(&records,&before,sizeof(records)));
 records.recent[6]=649;before=records;
 assert(p3dRecentTouch(&records,5,1,24,104)==-1);
 assert(!memcmp(&records,&before,sizeof(records)));
}
int main(void){
 favorites();recent();
 puts("C402 saved-entry list touch bounds, paging, validation and immutability: PASS");return 0;
}
