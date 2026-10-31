#include "dex_info.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
 P3DDexInfo info;char a[29],b[29];
 assert(argc==2);
 assert(!p3dDexInfoLoad(&info,0));
 assert(!info.ready && !info.text.name[0]);
 assert(p3dDexTextInit(argv[1]));
 assert(p3dDexInfoLoad(&info,0));
 assert(info.ready && info.index==0 && info.page==0 && info.pages==4);
 assert(!strcmp(info.text.name,"Synthetic entry"));
 assert(!strcmp(info.text.height,"1.2m") && !strcmp(info.text.weight,"3.4kg"));
 assert(!p3dDexInfoStep(&info,-1));
 for(int page=0;page<4;page++){
  size_t start=(size_t)page*56;
  p3dDexInfoLines(&info,a,b);
  size_t first=191-start;if(first>28)first=28;
  assert(strlen(a)==first && !strncmp(a,info.text.description+start,first));
  size_t second=191-start-first;if(second>28)second=28;
  assert(strlen(b)==second && !strncmp(b,info.text.description+start+first,second));
  if(page<3)assert(p3dDexInfoStep(&info,1));
 }
 assert(!p3dDexInfoStep(&info,1));
 assert(!p3dDexInfoStep(&info,2));
 assert(!p3dDexInfoStep(&info,0));
 assert(p3dDexInfoStep(&info,-1) && info.page==2);
 assert(p3dDexInfoLoad(&info,1));
 assert(info.page==0 && info.pages==1);
 p3dDexInfoLines(&info,a,b);assert(!a[0] && !b[0]);
 assert(!p3dDexInfoStep(&info,1));
 assert(p3dDexInfoLoad(&info,648));
 assert(!strcmp(info.text.name,"Last entry"));
 assert(!p3dDexInfoLoad(&info,649));
 assert(!info.ready && !info.text.name[0] && info.page==0);
 p3dDexInfoLines(&info,a,b);assert(!a[0] && !b[0]);
 p3dDexTextClose();
 assert(!p3dDexInfoLoad(&info,0));
 assert(!p3dDexInfoLoad(NULL,0));
 assert(!p3dDexInfoStep(NULL,1));
 p3dDexInfoLines(NULL,a,b);assert(!a[0] && !b[0]);
 assert(p3dDexInfoTouchToggle(64,160));
 assert(p3dDexInfoTouchToggle(191,175));
 assert(!p3dDexInfoTouchToggle(63,160));
 assert(!p3dDexInfoTouchToggle(192,160));
 assert(!p3dDexInfoTouchToggle(64,159));
 assert(!p3dDexInfoTouchToggle(64,176));
 puts("Private Pokédex entry loading, pagination, missing data and touch bounds: PASS");
}
