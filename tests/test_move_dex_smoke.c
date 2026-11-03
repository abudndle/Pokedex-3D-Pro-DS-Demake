#include "move_dex.h"
#include <assert.h>
#include <limits.h>
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

 /* C307: compare extreme saved cursors to an overflow-safe reference. */
 for(int k=0;k<4;k++){
   int starts[]={INT_MIN,INT_MAX,-559*3-1,559*3+1};
   int start=starts[k];
   for(int dir=-1;dir<=1;dir+=2){
     int base=start%559;
     if(base<0)base+=559;
     int expected=-1;
     for(int step=1;step<=559;step++){
       int index=dir==1?(base+step)%559:
         (base+559-(step%559))%559;
       if(index==0||index==1){expected=index;break;}
     }
     assert(p3dMoveDexFindInitial(start,'p',dir)==expected);
   }
 }
 assert(p3dMoveDexFindInitial(INT_MIN,'z',1)==-1);
 assert(p3dMoveDexFindInitial(INT_MAX,'m',1)>=2);
 assert(p3dMoveDexFindInitial(INT_MAX,'p',0)==-1);
 puts("Move Dex catalog: PASS");return 0;
}
