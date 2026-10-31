#include "dex_text.h"
#include "dex_search.h"
#include "records.h"
#include "feature_menu.h"
#include <assert.h>
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
    assert(p3dDexFindScoped("PI",0,1,P3D_DEX_SEARCH_NAME,0,9,P3D_DEX_SCOPE_ALL,&history,&menu)==-1);
    assert(strcmp(p3dDexRegionName(5),"UNOVA")==0);
    assert(strcmp(p3dDexScopeName(1),"VIEWED")==0);
    p3dDexTextClose();
    assert(!p3dDexTextRead(0,&entry));
    puts("C82 original species text and region/viewed/favorite search: PASS");
    return 0;
}
