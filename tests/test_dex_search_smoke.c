#include "dex_search.h"
#include "dex_text.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
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
 p3dDexTextClose();
 puts("Dex search smoke: PASS");
 return 0;
}
