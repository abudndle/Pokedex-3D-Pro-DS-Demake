#include "menu_navigation.h"
#include "menu_layout.h"
#define TOUCH_Y 88
#define TOUCH_STEP 16
#define VISIBLE 6
int p3dMenuTouchIndex(int x,int y,int count,int cursor){
 if(x<0||x>=256||y<TOUCH_Y||y>=TOUCH_Y+TOUCH_STEP*VISIBLE||count<=0)return -1;
 size_t start=p3dMenuVisibleStart((size_t)count,cursor);
 size_t item=start+(size_t)((y-TOUCH_Y)/TOUCH_STEP);
 return item<(size_t)count?(int)item:-1;
}
int p3dMenuScroll(int cursor,int count,int direction){
 if(count<=0)return -1;
 int next=cursor+direction;
 if(next<0)return 0;
 if(next>=count)return count-1;
 return next;
}
