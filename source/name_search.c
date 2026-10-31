#include "name_search.h"
#include <string.h>
void p3dNameSearchReset(P3DNameSearch *s){
 if(!s)return;
 memset(s,0,sizeof(*s));s->letter='A';s->match=-1;
}
void p3dNameSearchApply(P3DNameSearch *s,P3DNameAction action){
 int start;
 if(!s)return;
 switch(action){
 case P3D_NAME_UP:s->letter=s->letter=='A'?'Z':(char)(s->letter-1);return;
 case P3D_NAME_DOWN:s->letter=s->letter=='Z'?'A':(char)(s->letter+1);return;
 case P3D_NAME_APPEND:
  if(!p3dDexQueryAppend(s->query,s->letter))return;
  break;
 case P3D_NAME_ERASE:p3dDexQueryBackspace(s->query);break;
 case P3D_NAME_PREVIOUS:case P3D_NAME_NEXT:
  s->match=p3dDexFindPrefix(s->query,s->match,action==P3D_NAME_NEXT?1:-1);
  return;
 default:return;
 }
 /* Query edits retain the current result when it still matches. */
 start=s->match>=0?s->match-1:-1;
 s->match=p3dDexFindPrefix(s->query,start,1);
}
int p3dNameSearchTouchAction(int x,int y){
 if(x<0||x>=256)return -1;
 if(y>=112&&y<128)return x<128?P3D_NAME_UP:P3D_NAME_DOWN;
 if(y>=128&&y<144)return x<128?P3D_NAME_ERASE:P3D_NAME_APPEND;
 if(y>=160&&y<176)return x<128?P3D_NAME_PREVIOUS:P3D_NAME_NEXT;
 return -1;
}
