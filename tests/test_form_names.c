#include "form_names.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
int main(int argc,char **argv){
 P3DFormNames names={0};
 assert(argc==3);
 assert(p3dFormName(&names,0,1)==NULL);
 assert(p3dFormNamesLoad(&names,argv[1]));
 assert(strcmp(p3dFormName(&names,0,1),"Test Form")==0);
 assert(p3dFormName(&names,0,2)==NULL);
 assert(p3dFormName(&names,-1,1)==NULL);
 assert(!p3dFormNamesLoad(&names,argv[2]));
 assert(p3dFormName(&names,0,1)==NULL);
 puts("Verified optional form names: PASS");
 return 0;
}
