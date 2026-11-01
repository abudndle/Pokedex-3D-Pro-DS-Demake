#include "feature_menu.h"
#include <assert.h>
#include <stdio.h>
int main(void){P3DMenu m;P3DPage pages[P3D_MENU_MAX];P3DCapabilities ds=p3dCapabilities(0,0,0),dsi=p3dCapabilities(1,1,1);p3dMenuReset(&m);assert(p3dMenuEntries(ds,pages)==7);
assert(pages[0]==P3D_PAGE_DEX);
assert(pages[1]==P3D_PAGE_MOVES);
assert(pages[2]==P3D_PAGE_CHALLENGE);
assert(pages[3]==P3D_PAGE_RECORDS);
assert(pages[4]==P3D_PAGE_ALBUM);
assert(pages[5]==P3D_PAGE_AR);
assert(pages[6]==P3D_PAGE_SETTINGS);assert(p3dFeatureVisible(ds,P3D_FEATURE_AR));assert(p3dMenuEnter(&m,ds,P3D_PAGE_RECORDS));assert(m.page==P3D_PAGE_RECORDS);assert(!p3dMenuEnter(&m,ds,P3D_PAGE_AR));assert(p3dMenuEntries(dsi,pages)==7);assert(pages[5]==P3D_PAGE_AR);assert(p3dMenuEnter(&m,dsi,P3D_PAGE_AR));assert(p3dFavoriteToggle(&m,-1)==0);assert(p3dFavoriteToggle(&m,738)==0);assert(!p3dFavoriteContains(&m,-1));assert(!p3dFavoriteContains(&m,738));assert(m.favorites_count==0);m.favorites_count=P3D_FAVORITES_MAX+1;assert(!p3dFavoriteContains(&m,0));assert(p3dFavoriteToggle(&m,0)==0);m.favorites_count=-1;assert(!p3dFavoriteContains(&m,0));assert(p3dFavoriteToggle(&m,0)==0);m.favorites_count=0;assert(p3dFavoriteToggle(&m,0)==1);assert(p3dFavoriteContains(&m,0));assert(p3dFavoriteToggle(&m,0)==-1);assert(!p3dFavoriteContains(&m,0));assert(p3dFavoriteToggle(&m,648)==1);assert(p3dFavoriteContains(&m,648));assert(p3dFavoriteToggle(&m,648)==-1);assert(!p3dFavoriteContains(&m,648));assert(p3dTypeEffect(1,4)==20);assert(p3dTypeEffectDual(1,4,11)==40);puts("Feature menu: PASS");return 0;}
