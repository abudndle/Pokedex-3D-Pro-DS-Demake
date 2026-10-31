#ifndef P3D_DEX_SEARCH_H
#define P3D_DEX_SEARCH_H
#include <stddef.h>
int p3dDexPrefixMatches(const char *name,const char *prefix);
int p3dDexFindPrefix(const char *query,int start,int direction);
int p3dDexQueryAppend(char query[13],char ch);
void p3dDexQueryBackspace(char query[13]);
#include "records.h"
#include "feature_menu.h"
#define P3D_DEX_SEARCH_NAME 0
#define P3D_DEX_SEARCH_DESCRIPTION 1
#define P3D_DEX_REGIONS 6
#define P3D_DEX_SCOPE_ALL 0
#define P3D_DEX_SCOPE_VIEWED 1
#define P3D_DEX_SCOPE_FAVORITES 2
#define P3D_DEX_SCOPE_COUNT 3
const char *p3dDexRegionName(int region);
const char *p3dDexScopeName(int scope);
int p3dDexRegionBounds(int region,int *first,int *last);
int p3dDexContains(const char *text,const char *query);
/* Search only the original text records. No synthetic Pokémon names. */
int p3dDexFindScoped(const char *query,int start,int direction,int field,int region,int scope,const P3DRecords *records,const P3DMenu *menu);
int p3dDexFindFiltered(const char *query,int start,int direction,int field,int region);
#endif
