#ifndef P3D_NAME_SEARCH_H
#define P3D_NAME_SEARCH_H
#include "dex_search.h"
typedef enum { P3D_NAME_UP, P3D_NAME_DOWN, P3D_NAME_APPEND,
               P3D_NAME_ERASE, P3D_NAME_PREVIOUS, P3D_NAME_NEXT } P3DNameAction;
typedef struct { char query[13]; char letter; int match; } P3DNameSearch;
void p3dNameSearchReset(P3DNameSearch *search);
/* Uses the currently initialized private P3DX catalog. Empty or unmatched
 * queries have match=-1 and must not open/favorite a stale numeric selection. */
/* Text-mode touch rows: letter 15, erase/append 17, matches 21. */
int p3dNameSearchTouchAction(int x,int y);
void p3dNameSearchApply(P3DNameSearch *search,P3DNameAction action);
#endif
