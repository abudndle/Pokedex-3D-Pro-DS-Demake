#include "dex_text.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
 P3DDexText d;
 if(argc!=2)return 2;
 assert(!p3dDexTextRead(0,&d));
 assert(p3dDexTextInit(argv[1]));
 assert(p3dDexTextRead(0,&d));
 assert(strcmp(d.name,"Bulbasaur")==0);
 assert(!p3dDexTextRead(-1,&d));
 assert(!p3dDexTextRead(649,&d));
 p3dDexTextClose();
 puts("Dex text read: PASS");
 return 0;
}
