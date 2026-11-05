#include "bookmark_edit.h"
#include <assert.h>
#include <string.h>
int main(void){
 P3DBookmarkList pokemon={0},moves={0};
 for(unsigned i=0;i<16;i++){assert(p3dBookmarkAdd(&pokemon,(uint16_t)i,738));assert(p3dBookmarkAdd(&moves,(uint16_t)(i+20),559));}
 assert(!p3dBookmarkAdd(&pokemon,17,738));
 assert(!p3dBookmarkAdd(&pokemon,0,738));
 assert(!p3dBookmarkAdd(&moves,559,559));
 assert(!p3dBookmarkEditTap(&pokemon,3));
 p3dBookmarkSetEditing(&pokemon,1);
 assert(p3dBookmarkEditTap(&pokemon,3));
 assert(pokemon.count==15&&pokemon.ids[3]==4&&pokemon.ids[14]==15);
 assert(moves.count==16&&moves.ids[3]==23);
 assert(!p3dBookmarkEditTap(&pokemon,15));
 assert(p3dBookmarkAdd(&pokemon,100,738));
 p3dBookmarkSetEditing(&pokemon,0);
 assert(!p3dBookmarkEditTap(&pokemon,0));
 assert(p3dBookmarkValid(&pokemon,738));
 assert(p3dBookmarkValid(&moves,559));
 pokemon.ids[1]=pokemon.ids[0];assert(!p3dBookmarkValid(&pokemon,738));
 assert(!p3dBookmarkAdd(&pokemon,101,738));
 memset(&pokemon,0,sizeof(pokemon));
 assert(p3dBookmarkAdd(&pokemon,737,738));
 assert(!p3dBookmarkAdd(&pokemon,738,738));
 return 0;
}
