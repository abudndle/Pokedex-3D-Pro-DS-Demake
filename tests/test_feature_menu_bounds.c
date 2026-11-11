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
    assert(count==7);
    assert(pages[count]==(P3DPage)255);
    assert(pages[0]==P3D_PAGE_DEX);
    assert(p3dMenuEntries(dsi,pages)==7);
    assert(pages[5]==P3D_PAGE_AR);
    assert(pages[6]==P3D_PAGE_SETTINGS);
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
    /* Removing a favorite before the current selection must keep the
     * same Pokémon highlighted after the array shifts left. */
    p3dMenuReset(&state);
    for(int i=0;i<4;i++) assert(p3dFavoriteToggle(&state,i)==1);
    state.favorite_cursor=3;
    assert(p3dFavoriteToggle(&state,1)==-1);
    assert(state.favorite_cursor==2);
    assert(state.favorites[state.favorite_cursor]==3);
    assert(p3dFavoriteToggle(&state,3)==-1);
    assert(state.favorite_cursor==1);
    assert(state.favorites[state.favorite_cursor]==2);
    assert(p3dFavoriteToggle(&state,0)==-1);
    assert(p3dFavoriteToggle(&state,2)==-1);
    assert(state.favorites_count==0 && state.favorite_cursor==0);
    /* Recover from a damaged persisted Favorites selection. */
    p3dMenuReset(&state);
    assert(p3dFavoriteToggle(&state,10)==1);
    assert(p3dFavoriteToggle(&state,11)==1);
    state.favorite_cursor=999;
    assert(p3dFavoriteToggle(&state,12)==1);
    assert(state.favorite_cursor==1);
    state.favorite_cursor=-7;
    assert(p3dFavoriteToggle(&state,12)==-1);
    assert(state.favorite_cursor==0);
    /* Search origins can come from damaged save data. A very negative
     * position must wrap safely rather than index before the array. */
    const char *labels[]={"Alpha","Bravo","Charlie","Delta"};
    assert(p3dSearchNext(labels,4,-1000,'B',1)==1);
    assert(p3dSearchNext(labels,4,-1000,'D',-1)==3);
    assert(p3dSearchNext(labels,4,-2147483647-1,'A',1)==0);
    assert(p3dSearchNext(labels,4,0,'c',1)==2);
    assert(p3dSearchNext(labels,4,0,'Z',1)==-1);
    assert(p3dSearchNext(labels,4,0,'A',0)==-1);
    /* Generation V type matchup examples (scale: 0, 5, 10, 20).
     * Immunity must remain zero even for dual-type defenders. */
    assert(p3dTypeEffect(3,8)==0);  /* Electric -> Ground */
    assert(p3dTypeEffect(1,4)==20); /* Fire -> Grass */
    assert(p3dTypeEffect(1,2)==5);  /* Fire -> Water */
    assert(p3dTypeEffectDual(3,2,8)==0);
    assert(p3dTypeEffectDual(1,4,6)==20);
    assert(p3dTypeEffectDual(1,4,-1)==20);
    assert(p3dTypeEffectDual(1,4,-2)==-1);
    assert(p3dTypeEffectDual(-1,4,2)==-1);
    assert(p3dTypeEffectDual(1,4,17)==-1);
    assert(p3dTypeStepDefender(3,4,1)==5);
    assert(p3dTypeStepDefender(5,4,-1)==3);
    assert(p3dTypeStepDefender(16,0,1)==1);
    assert(p3dTypeStepDefender(0,16,-1)==15);
    assert(p3dTypeStepDefender(16,-1,1)==0);
    assert(p3dTypeStepDefender(4,5,0)==4);
    /* C311: Type Chart's original Pokémon Search path must reject bad
     * source pages and IDs without damaging a restored saved selection. */
    p3dMenuReset(&state);
    state.selected_dex=42;
    strcpy(state.search_query,"STALE");
    assert(!p3dTypeChartOpenSearch(&state,25));
    assert(state.page==P3D_PAGE_HOME && state.selected_dex==42);
    state.page=P3D_PAGE_TYPES;
    assert(!p3dTypeChartOpenSearch(NULL,25));
    assert(!p3dTypeChartOpenSearch(&state,-1));
    assert(!p3dTypeChartOpenSearch(&state,649));
    assert(state.page==P3D_PAGE_TYPES && state.selected_dex==42);
    assert(!strcmp(state.search_query,"STALE"));
    assert(p3dTypeChartOpenSearch(&state,648));
    assert(state.page==P3D_PAGE_SEARCH && state.selected_dex==648);
    assert(state.search_query[0]==0 && state.search_number_mode==0);
    assert(!p3dTypeChartOpenSearch(&state,100));
    state.page=P3D_PAGE_TYPES;
    strcpy(state.search_query,"OLD");
    state.search_number_mode=1;
    state.cursor=7;
    assert(p3dTypeChartOpenSearch(&state,0));
    assert(state.selected_dex==0 && state.cursor==0 &&
           !state.search_number_mode && !state.search_query[0]);
    return 0;
}
