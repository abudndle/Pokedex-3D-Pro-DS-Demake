#ifndef P3D_DEX_SEARCH_H
#define P3D_DEX_SEARCH_H
#include <stddef.h>
int p3dDexPrefixMatches(const char *name,const char *prefix);
int p3dDexFindPrefix(const char *query,int start,int direction);
int p3dDexQueryAppend(char query[13],char ch);
void p3dDexQueryBackspace(char query[13]);
/* Returns A-Z, 8 (backspace), 127 (clear), or 0 outside a key. */
int p3dDexSearchTouchKey(int x,int y);
#endif
