#include "move_dex.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
 P3DMove m;
 if(argc!=2)return 2;
 assert(p3dMoveDexInit(argv[1]));
 assert(p3dMoveDexCount()==559);
 assert(p3dMoveDexRead(0,&m));assert(m.id==1);assert(strcmp(m.name,"Pound")==0);
 assert(!p3dMoveDexRead(559,&m));
 assert(p3dMoveDexFindInitial(0,'p',1)==1);
 puts("Move Dex catalog: PASS");return 0;
}
