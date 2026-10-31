#include "menu_navigation.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 assert(p3dMenuTouchIndex(10,88,8,0)==0);
 assert(p3dMenuTouchIndex(10,104,8,0)==1);
 assert(p3dMenuTouchIndex(10,88,8,7)==2);
 assert(p3dMenuTouchIndex(10,183,8,7)==7);
 assert(p3dMenuTouchIndex(10,184,8,0)==-1);
 assert(p3dMenuScroll(7,8,1)==7);
 assert(p3dMenuScroll(0,8,-1)==0);
 puts("Graphical menu navigation: PASS");return 0;
}
