#include "dex_text.h"
#include "dex_search.h"
#include "records.h"
#include "feature_menu.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
    P3DDexText entry;
    P3DRecords history;
    P3DMenu menu;
    assert(argc==3);
    assert(!p3dDexTextInit(argv[2])); /* Truncated source metadata must fail. */
    assert(p3dDexTextInit(argv[1]));
    assert(p3dDexTextRead(0,&entry));
    assert(strcmp(entry.name,"Bulbasaur")==0);
    assert(strcmp(entry.height,"0.7m")==0);
    assert(!p3dDexTextRead(649,&entry));
    assert(p3dDexPrefixMatches("Pikachu","pIk"));
    assert(p3dDexContains("This creature glows at night","GLOWS"));
    assert(p3dDexFindPrefix("pik",0,1)==24);
    /* C309: restoring corrupt or arbitrary signed cursors cannot overflow,
     * and the search still wraps to the actual original-text species. */
    assert(p3dDexFindPrefix("pik",INT_MAX,1)==24);
    assert(p3dDexFindPrefix("pik",INT_MIN,1)==24);
    assert(p3dDexFindPrefix("pik",INT_MAX,-1)==24);
    assert(p3dDexFindPrefix("pik",INT_MIN,-1)==24);
    assert(p3dDexFindPrefix("PIK",-1,1)==24);
    assert(p3dDexFindPrefix("PIK",649*5+24,-1)==24);
    assert(p3dDexFindPrefix("PIK",0,0)==-1);
    assert(p3dDexFindPrefix(NULL,INT_MIN,1)==-1);
    assert(p3dDexFindPrefix("UNAVAILABLE",INT_MAX,1)==-1);
    assert(p3dDexFindFiltered("seed",150,1,P3D_DEX_SEARCH_DESCRIPTION,1)==0);
    assert(p3dDexFindFiltered("pik",20,1,P3D_DEX_SEARCH_NAME,1)==24);
    assert(p3dDexFindFiltered("pik",20,1,P3D_DEX_SEARCH_NAME,2)==-1);
    assert(p3dDexFindFiltered("",20,1,P3D_DEX_SEARCH_NAME,0)==-1);
    p3dRecordsReset(&history);
    p3dMenuReset(&menu);
    assert(p3dDexFindScoped("pik",0,1,P3D_DEX_SEARCH_NAME,0,P3D_DEX_SCOPE_VIEWED,&history,&menu)==-1);
    assert(p3dRecordsVisit(&history,24));
    assert(p3dDexFindScoped("pik",0,1,P3D_DEX_SEARCH_NAME,0,P3D_DEX_SCOPE_VIEWED,&history,&menu)==24);
    assert(p3dDexFindScoped("",0,1,P3D_DEX_SEARCH_NAME,0,P3D_DEX_SCOPE_FAVORITES,&history,&menu)==-1);
    assert(p3dFavoriteToggle(&menu,24)==1);
    assert(p3dDexFindScoped("PI",0,1,P3D_DEX_SEARCH_NAME,0,P3D_DEX_SCOPE_FAVORITES,&history,&menu)==24);
    assert(p3dDexFindScoped("PI",0,1,P3D_DEX_SEARCH_NAME,0,9,&history,&menu)==-1);
    assert(p3dDexFindScoped("PI",0,1,P3D_DEX_SEARCH_NAME,9,P3D_DEX_SCOPE_ALL,&history,&menu)==-1);
    assert(strcmp(p3dDexRegionName(5),"UNOVA")==0);
    assert(strcmp(p3dDexScopeName(1),"VIEWED")==0);
    /* C231: selecting a previously shown Pokémon must not authorize opening
     * or favoriting it once search text, region, or scope no longer matches. */
    int selection=0;
    assert(p3dDexRefreshSelection("pik",&selection,P3D_DEX_SEARCH_NAME,0,
                                  P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(selection==24);
    assert(p3dDexSelectionMatches("PIK",selection,P3D_DEX_SEARCH_NAME,0,
                                  P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(!p3dDexRefreshSelection("ZZZ",&selection,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(selection==24); /* Stale cursor retained but no longer actionable. */
    assert(!p3dDexSelectionMatches("ZZZ",selection,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(p3dDexRefreshSelection("seed",&selection,
                                   P3D_DEX_SEARCH_DESCRIPTION,1,
                                   P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(selection==0);
    assert(!p3dDexSelectionMatches("seed",selection,
                                   P3D_DEX_SEARCH_DESCRIPTION,2,
                                   P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(!p3dDexSelectionMatches("",selection,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_VIEWED,&history,&menu));
    selection=24;
    assert(p3dDexSelectionMatches("PIK",selection,P3D_DEX_SEARCH_NAME,0,
                                  P3D_DEX_SCOPE_FAVORITES,&history,&menu));
    assert(p3dFavoriteToggle(&menu,24)==-1);
    assert(!p3dDexSelectionMatches("PIK",selection,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_FAVORITES,&history,&menu));
    assert(!p3dDexRefreshSelection("PIK",&selection,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_FAVORITES,&history,&menu));
    assert(selection==24);
    assert(!p3dDexSelectionMatches("",-1,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(!p3dDexSelectionMatches("",649,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(!p3dDexSelectionMatches("",0,3,0,P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(!p3dDexSelectionMatches("",0,P3D_DEX_SEARCH_NAME,9,
                                   P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(!p3dDexSelectionMatches("",0,P3D_DEX_SEARCH_NAME,0,9,&history,&menu));
    assert(!p3dDexSelectionMatches(NULL,0,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(!p3dDexRefreshSelection("pik",NULL,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(!p3dDexSelectionMatches("",24,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_VIEWED,NULL,&menu));
    assert(!p3dDexSelectionMatches("",24,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_FAVORITES,&history,NULL));
    /* Numeric +1 hid the only PIK match behind an unrelated cursor. */
    assert(p3dDexKeypadSelection("PIK",24,1,P3D_DEX_SEARCH_NAME,0,P3D_DEX_SCOPE_ALL,&history,&menu)==24);
    assert(p3dDexKeypadSelection("seed",24,-10,P3D_DEX_SEARCH_DESCRIPTION,1,P3D_DEX_SCOPE_ALL,&history,&menu)==0);
    assert(p3dDexKeypadSelection("",150,1,P3D_DEX_SEARCH_NAME,1,P3D_DEX_SCOPE_ALL,&history,&menu)==0);
    assert(p3dDexKeypadSelection("",24,1,P3D_DEX_SEARCH_NAME,0,P3D_DEX_SCOPE_FAVORITES,&history,&menu)==24);
    assert(p3dDexKeypadSelection("ZZZ",24,1,P3D_DEX_SEARCH_NAME,0,P3D_DEX_SCOPE_ALL,&history,&menu)==24);
    assert(p3dDexKeypadSelection("",24,10,P3D_DEX_SEARCH_NAME,0,P3D_DEX_SCOPE_ALL,&history,&menu)==34);
    assert(p3dDexKeypadSelection("",646,10,P3D_DEX_SEARCH_NAME,0,P3D_DEX_SCOPE_ALL,&history,&menu)==648);
    assert(p3dDexKeypadSelection("",2,-10,P3D_DEX_SEARCH_NAME,0,P3D_DEX_SCOPE_ALL,&history,&menu)==0);
    assert(p3dFavoriteToggle(&menu,0)==1&&p3dFavoriteToggle(&menu,62)==1);
    assert(p3dDexKeypadSelection("",0,1,P3D_DEX_SEARCH_NAME,0,P3D_DEX_SCOPE_FAVORITES,&history,&menu)==62);
    assert(p3dDexKeypadSelection("",62,-10,P3D_DEX_SEARCH_NAME,0,P3D_DEX_SCOPE_FAVORITES,&history,&menu)==0);
    assert(p3dDexKeypadSelection("",0,1,P3D_DEX_SEARCH_NAME,0,P3D_DEX_SCOPE_VIEWED,&history,&menu)==24);
    /* A focused handoff must show Bulbasaur even after a PIK search. */
    menu.page=P3D_PAGE_DEX;
    strcpy(menu.search_query,"PIK");
    assert(p3dMenuOpenPokemonSearch(&menu,0));
    assert(menu.page==P3D_PAGE_SEARCH&&menu.selected_dex==0);
    assert(p3dDexSelectionMatches(menu.search_query,0,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_ALL,&history,&menu));
    menu.page=P3D_PAGE_FAVORITES;
    strcpy(menu.search_query,"PIK");
    assert(p3dMenuOpenPokemonSearch(&menu,62));
    assert(menu.page==P3D_PAGE_SEARCH&&menu.selected_dex==62&&!menu.search_query[0]);
    assert(menu.favorites_count==2);
    menu.page=P3D_PAGE_DEX;
    assert(!p3dMenuOpenPokemonSearch(&menu,649));
    assert(menu.page==P3D_PAGE_DEX&&menu.selected_dex==62);
    menu.page=P3D_PAGE_SEARCH;
    menu.selected_dex=24;
    menu.search_letter='B';
    strcpy(menu.search_query,"electric");
    int jump_field=P3D_DEX_SEARCH_DESCRIPTION;
    assert(p3dDexJumpInitial(&menu,&jump_field,1,1,P3D_DEX_SCOPE_FAVORITES,&history));
    assert(menu.selected_dex==0&&jump_field==P3D_DEX_SEARCH_NAME);
    assert(!strcmp(menu.search_query,"B"));
    assert(p3dDexSelectionMatches(menu.search_query,menu.selected_dex,jump_field,1,
                                  P3D_DEX_SCOPE_FAVORITES,&history,&menu));
    menu.search_letter='P';
    assert(!p3dDexJumpInitial(&menu,&jump_field,1,1,P3D_DEX_SCOPE_FAVORITES,&history));
    assert(menu.selected_dex==0&&jump_field==P3D_DEX_SEARCH_NAME&&!strcmp(menu.search_query,"B"));
    assert(p3dDexJumpInitial(&menu,&jump_field,-1,1,P3D_DEX_SCOPE_VIEWED,&history));
    assert(menu.selected_dex==24&&!strcmp(menu.search_query,"P"));
    p3dDexTextClose();
    assert(!p3dDexSelectionMatches("PIK",24,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(!p3dDexRefreshSelection("PIK",&selection,P3D_DEX_SEARCH_NAME,0,
                                   P3D_DEX_SCOPE_ALL,&history,&menu));
    assert(!p3dDexTextRead(0,&entry));
    puts("C82 original species text and region/viewed/favorite search: PASS");
    return 0;
}
