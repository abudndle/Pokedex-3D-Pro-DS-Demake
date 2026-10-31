#ifndef P3D_FEATURE_MENU_H
#define P3D_FEATURE_MENU_H
#include "dsi_features.h"
#include <stddef.h>
typedef enum {P3D_PAGE_HOME=0,P3D_PAGE_DEX,P3D_PAGE_SEARCH,P3D_PAGE_MOVES,P3D_PAGE_TYPES,P3D_PAGE_FAVORITES,P3D_PAGE_CHALLENGE,P3D_PAGE_SETTINGS,P3D_PAGE_ALBUM,P3D_PAGE_AR,P3D_PAGE_RECORDS,P3D_PAGE_COUNT} P3DPage;
#define P3D_FAVORITES_MAX 6
#define P3D_MENU_MAX 10
typedef struct {P3DPage page;int cursor,selected_dex,move_index,move_effect,move_page;int favorites[P3D_FAVORITES_MAX],favorites_count;char search_query[13];int search_number_mode,type_defend2,type_select_second,search_letter;int favorite_cursor,type_attack,type_defend,backdrop,rotate;int challenge_answer,challenge_cursor,challenge_correct,challenge_total;} P3DMenu;
void p3dMenuReset(P3DMenu *s);
size_t p3dMenuEntries(P3DCapabilities caps,P3DPage pages[P3D_MENU_MAX]);
int p3dMenuEnter(P3DMenu *s,P3DCapabilities caps,P3DPage page);
const char *p3dPageName(P3DPage page);
int p3dFavoriteToggle(P3DMenu *s,int model_index);
int p3dFavoriteContains(const P3DMenu *s,int model_index);
const char *p3dTypeName(int type);
int p3dTypeEffect(int attacking,int defending);
int p3dTypeEffectDual(int attacking,int defending1,int defending2);
int p3dSearchNext(const char *const names[],size_t count,int from,char initial,int direction);
#endif
