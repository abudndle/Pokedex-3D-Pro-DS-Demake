/* Regression tests for the actual native DS menu navigation modules.
 * Host compile:
 * cc -std=c11 -Wall -Wextra -Werror -Isource tests/test_menu_navigation.c
 *   source/menu_navigation.c source/menu_layout.c -o /tmp/p3d-menu-test
 * /tmp/p3d-menu-test
 */
#include "menu_navigation.h"
#include "menu_layout.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 for(int count=0;count<20;count++)
  for(int cursor=-1;cursor<count+1;cursor++)
   for(int row=0;row<6;row++){
    int expected=count?(int)p3dMenuVisibleStart((size_t)count,cursor)+row:-1;
    if(expected>=count)expected=-1;
    assert(p3dMenuTouchIndex(120,88+16*row,count,cursor)==expected);
   }
 assert(p3dMenuTouchIndex(10,88,8,0)==0);
 assert(p3dMenuTouchIndex(10,104,8,0)==1);
 assert(p3dMenuTouchIndex(10,88,8,7)==2);
 assert(p3dMenuTouchIndex(10,183,8,7)==7);
 assert(p3dMenuTouchIndex(10,184,8,0)==-1);
 assert(p3dMenuTouchIndex(120,87,8,0)==-1);
 assert(p3dMenuTouchIndex(-1,100,8,0)==-1);
 assert(p3dMenuTouchIndex(256,100,8,0)==-1);
 assert(p3dMenuScroll(7,8,1)==7);
 assert(p3dMenuScroll(0,8,-1)==0);
 assert(p3dDexNavigate(0,-1)==0);
 assert(p3dDexNavigate(0,1)==1);
 assert(p3dDexNavigate(648,1)==648);
 assert(p3dDexNavigate(648,-1)==647);
 assert(p3dDexNavigate(-10,1)==1);
 assert(p3dDexNavigate(900,-1)==647);
 assert(p3dDexNavigate(100,0)==100);
 puts("Graphical and Pokedex navigation: PASS");
 return 0;
}
