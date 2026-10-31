#include "dex_search.h"
#include "dex_text.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <limits.h>
int main(int argc,char **argv){
 char q[13]=""; P3DDexText d;
 if(argc!=2)return 2;
 assert(p3dDexTextInit(argv[1]));
 assert(p3dDexTextRead(0,&d));
 assert(strcmp(d.name,"Bulbasaur")==0);
 assert(p3dDexPrefixMatches("Bulbasaur","bulb"));
 assert(!p3dDexPrefixMatches("Ivysaur","bulb"));
 assert(p3dDexFindPrefix("CHAR",2,1)==3);
 for(int i=0;i<12;i++)assert(p3dDexQueryAppend(q,'A'));
 assert(!p3dDexQueryAppend(q,'B'));
 p3dDexQueryBackspace(q);assert(strlen(q)==11);
 assert(p3dDexFindPrefix("bulb",648,1)==0);
 assert(p3dDexFindPrefix("CHAR",0,-1)==3);
 assert(p3dDexFindPrefix("missing",0,1)==-1);
 assert(p3dDexFindPrefix("",0,1)==-1);
 assert(p3dDexFindPrefix("CHAR",INT_MAX,1)==3);
 assert(p3dDexFindPrefix("CHAR",INT_MIN,-1)==3);
 for(int i=0;i<26;i++){
  int x=(i%8)*32,y=104+(i/8)*16;
  assert(p3dDexSearchTouchKey(x,y)=='A'+i);
  assert(p3dDexSearchTouchKey(x+31,y+15)=='A'+i);
 }
 assert(p3dDexSearchTouchKey(64,152)==8);
 assert(p3dDexSearchTouchKey(96,152)==127);
 assert(!p3dDexSearchTouchKey(128,152));
 assert(!p3dDexSearchTouchKey(-1,104));
 assert(!p3dDexSearchTouchKey(256,104));
 assert(!p3dDexSearchTouchKey(0,103));
 assert(!p3dDexSearchTouchKey(0,168));
 char empty[13]="";
 p3dDexQueryBackspace(empty);assert(!empty[0]);
 assert(!p3dDexQueryAppend(empty,'!'));
 assert(!p3dDexQueryAppend(empty,'a'));
 p3dDexTextClose();
 assert(p3dDexFindPrefix("CHAR",0,1)==-1);
 puts("Dex search smoke: PASS");
 return 0;
}
