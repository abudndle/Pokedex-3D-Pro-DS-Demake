#include "feature_menu.h"
#include <assert.h>
#include <string.h>

int main(void) {
    P3DPage pages[P3D_MENU_MAX + 1];
    P3DCapabilities ds=p3dCapabilities(0,0,0);
    P3DCapabilities dsi=p3dCapabilities(1,1,1);
    for(size_t i=0;i<P3D_MENU_MAX+1;i++) pages[i]=(P3DPage)255;
    size_t count=p3dMenuEntries(ds,pages);
    assert(count<=P3D_MENU_MAX);
    assert(count==P3D_MENU_MAX-1);
    assert(pages[count]==(P3DPage)255);
    assert(pages[0]==P3D_PAGE_DEX);
    assert(p3dMenuEntries(dsi,pages)==P3D_MENU_MAX);
    assert(pages[P3D_MENU_MAX-1]==P3D_PAGE_AR);
    P3DMenu state;
    p3dMenuReset(&state);
    assert(state.type_defend2==-1);
    assert(state.search_letter=='A');
    assert(!strcmp(p3dPageName((P3DPage)255),"UNKNOWN"));
    assert(!p3dMenuEnter(&state,ds,(P3DPage)255));
    assert(!p3dMenuEnter(&state,ds,P3D_PAGE_AR));
    assert(p3dMenuEnter(&state,dsi,P3D_PAGE_AR));
    assert(state.page==P3D_PAGE_AR);
    /* Corrupt or out-of-range page IDs cannot index the menu label table. */
    assert(!strcmp(p3dPageName((P3DPage)-1),"UNKNOWN"));
    assert(!p3dMenuEnter(&state,dsi,(P3DPage)-1));
    assert(!p3dMenuEnter(&state,dsi,P3D_PAGE_COUNT));
    assert(state.page==P3D_PAGE_AR);
    /* Filling favorites must never write beyond its fixed DS capacity. */
    for(int i=0;i<P3D_FAVORITES_MAX;i++) {
        assert(p3dFavoriteToggle(&state,i)==1);
        assert(p3dFavoriteContains(&state,i)==1);
    }
    assert(state.favorites_count==P3D_FAVORITES_MAX);
    assert(p3dFavoriteToggle(&state,100)==0);
    assert(!p3dFavoriteContains(&state,100));
    assert(p3dFavoriteToggle(&state,2)==-1);
    assert(!p3dFavoriteContains(&state,2));
    assert(state.favorites_count==P3D_FAVORITES_MAX-1);
    assert(p3dFavoriteToggle(&state,100)==1);
    assert(state.favorites_count==P3D_FAVORITES_MAX);
    return 0;
}
