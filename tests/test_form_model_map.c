#include "form_model_map.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 P3DFormMap m={0};
 assert(argc==3);
 assert(p3dFormResolve(&m,0,1)==-1);
 assert(p3dFormMapLoad(&m,argv[1]));
 assert(p3dFormResolve(&m,0,1)==737);
 assert(p3dFormResolve(&m,0,2)==7);
 assert(p3dFormResolve(&m,1,1)==-1);
 assert(p3dFormNext(&m,0,0)==1);
 assert(p3dFormNext(&m,0,1)==2);
 assert(p3dFormNext(&m,0,2)==0);
 assert(p3dFormNext(&m,1,0)==0);
 assert(!p3dFormMapLoad(&m,argv[2]));
 assert(p3dFormResolve(&m,0,1)==-1);
 puts("Verified alternate-form mappings: PASS");
 return 0;
}
