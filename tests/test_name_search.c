#include "name_search.h"
#include "dex_text.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
 P3DNameSearch s;
 P3DDexText text;
 assert(argc==3);
 p3dNameSearchReset(&s);
 assert(s.letter=='A' && s.match==-1 && !s.query[0]);
 p3dNameSearchApply(&s,P3D_NAME_APPEND);
 assert(s.match==-1); /* No initialized catalog; never invent results. */
 assert(p3dDexTextInit(argv[1]));
 assert(p3dDexTextRead(3,&text));
 assert(strlen(text.name)==31 && strlen(text.description)==191);
 assert(strlen(text.height)==15 && strlen(text.weight)==15);
 p3dNameSearchReset(&s);
 p3dNameSearchApply(&s,P3D_NAME_UP);assert(s.letter=='Z');
 p3dNameSearchApply(&s,P3D_NAME_DOWN);assert(s.letter=='A');
 p3dNameSearchApply(&s,P3D_NAME_APPEND);
 assert(!strcmp(s.query,"A") && s.match==0);
 assert(p3dDexTextRead(s.match,&text) && !strcmp(text.name,"Alpha"));
 p3dNameSearchApply(&s,P3D_NAME_NEXT);assert(s.match==1);
 p3dNameSearchApply(&s,P3D_NAME_NEXT);assert(s.match==648);
 p3dNameSearchApply(&s,P3D_NAME_NEXT);assert(s.match==0);
 p3dNameSearchApply(&s,P3D_NAME_PREVIOUS);assert(s.match==648);
 /* Re-editing a query retains the current match when possible. */
 p3dNameSearchApply(&s,P3D_NAME_DOWN); /* B */
 p3dNameSearchApply(&s,P3D_NAME_APPEND);assert(s.match==-1 && !strcmp(s.query,"AB"));
 p3dNameSearchApply(&s,P3D_NAME_NEXT);assert(s.match==-1);
 p3dNameSearchApply(&s,P3D_NAME_ERASE);assert(s.match==0);
 p3dNameSearchApply(&s,P3D_NAME_ERASE);assert(s.match==-1 && !s.query[0]);
 p3dNameSearchApply(&s,P3D_NAME_APPEND);assert(s.match==2 && !strcmp(s.query,"B"));
 p3dNameSearchApply(&s,P3D_NAME_NEXT);assert(s.match==2);
 p3dNameSearchApply(&s,P3D_NAME_PREVIOUS);assert(s.match==2);
 p3dNameSearchReset(&s);
 for(int i=0;i<12;i++)p3dNameSearchApply(&s,P3D_NAME_APPEND);
 assert(strlen(s.query)==12);
 p3dNameSearchApply(&s,P3D_NAME_APPEND);assert(strlen(s.query)==12);
 for(int i=0;i<13;i++)p3dNameSearchApply(&s,P3D_NAME_ERASE);
 assert(!s.query[0] && s.match==-1);
 assert(p3dDexFindPrefix("a",INT_MAX,1)>=0);
 assert(p3dDexFindPrefix("a",INT_MIN,-1)>=0);
 assert(p3dDexFindPrefix("a",0,0)==-1);
 assert(p3dDexFindPrefix("a",0,2)==-1);
 assert(p3dDexFindPrefix("",0,1)==-1);
 assert(p3dDexFindPrefix(NULL,0,1)==-1);
 /* Reinitialization failure closes the prior catalog and clears output. */
 assert(!p3dDexTextInit(argv[2]));
 memset(&text,0x7f,sizeof text);
 assert(!p3dDexTextRead(0,&text));
 P3DDexText empty={0};assert(!memcmp(&text,&empty,sizeof text));
 assert(p3dDexTextInit(argv[1]));
 memset(&text,0x7f,sizeof text);assert(!p3dDexTextRead(649,&text));
 assert(!memcmp(&text,&empty,sizeof text));
 assert(!p3dDexTextRead(0,NULL));
 p3dDexTextClose();
 p3dNameSearchApply(&s,P3D_NAME_APPEND);assert(s.match==-1);
 p3dNameSearchReset(NULL);p3dNameSearchApply(NULL,P3D_NAME_NEXT);
 for(int side=0;side<2;side++){
  int x=side?255:0;
  assert(p3dNameSearchTouchAction(x,112)==(side?P3D_NAME_DOWN:P3D_NAME_UP));
  assert(p3dNameSearchTouchAction(x,127)==(side?P3D_NAME_DOWN:P3D_NAME_UP));
  assert(p3dNameSearchTouchAction(x,128)==(side?P3D_NAME_APPEND:P3D_NAME_ERASE));
  assert(p3dNameSearchTouchAction(x,143)==(side?P3D_NAME_APPEND:P3D_NAME_ERASE));
  assert(p3dNameSearchTouchAction(x,160)==(side?P3D_NAME_NEXT:P3D_NAME_PREVIOUS));
  assert(p3dNameSearchTouchAction(x,175)==(side?P3D_NAME_NEXT:P3D_NAME_PREVIOUS));
 }
 assert(p3dNameSearchTouchAction(-1,112)==-1);
 assert(p3dNameSearchTouchAction(256,112)==-1);
 assert(p3dNameSearchTouchAction(128,111)==-1);
 assert(p3dNameSearchTouchAction(128,144)==-1);
 assert(p3dNameSearchTouchAction(128,159)==-1);
 assert(p3dNameSearchTouchAction(128,176)==-1);
 puts("Native name search editing, wraparound, missing data and touch bounds: PASS");
}
