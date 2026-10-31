#include "feature_menu.h"
#include <assert.h>
#include <stdio.h>
int main(void){P3DMenu m;P3DPage pages[P3D_MENU_MAX];P3DCapabilities ds=p3dCapabilities(0,0,0),dsi=p3dCapabilities(1,1,1);p3dMenuReset(&m);assert(p3dMenuEntries(ds,pages)==8);assert(!p3dMenuEnter(&m,ds,P3D_PAGE_AR));assert(p3dMenuEntries(dsi,pages)==9);assert(p3dMenuEnter(&m,dsi,P3D_PAGE_AR));assert(p3dFavoriteToggle(&m,0)==1);assert(p3dFavoriteContains(&m,0));assert(p3dFavoriteToggle(&m,0)==-1);assert(p3dTypeEffect(1,4)==20);assert(p3dTypeEffectDual(1,4,11)==40);puts("Feature menu: PASS");return 0;}
