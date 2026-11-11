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
/* Validate the currently displayed numeric cursor against active filters.
 * A stale cursor may remain visible but cannot be opened or favorited. */
int p3dDexSelectionMatches(const char *query,int index,int field,int region,int scope,
                           const P3DRecords *records,const P3DMenu *menu);
/* Preserve a valid cursor or move to the next valid original entry. On
 * no match, leave the numeric cursor alone and return 0. */
int p3dDexRefreshSelection(const char *query,int *selection,int field,int region,int scope,
                           const P3DRecords *records,const P3DMenu *menu);
/* Unfiltered keypad browsing keeps numeric offsets. Active filters step
 * between matching entries and retain the cursor if no match exists. */
int p3dDexKeypadSelection(const char *query,int selection,int delta,int field,int region,int scope,
                         const P3DRecords *records,const P3DMenu *menu);
/* Apply a name-initial jump only when the active region and scope have a match. */
int p3dDexJumpInitial(P3DMenu *menu,int *field,int direction,int region,int scope,const P3DRecords *records);
#endif
