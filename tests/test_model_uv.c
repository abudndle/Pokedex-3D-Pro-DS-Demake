#include "model_uv.h"
#include <assert.h>
#include <stdio.h>
static void cleared(const P3DUvMap *uv){
 const unsigned char *p=(const unsigned char *)uv;
 for(unsigned i=0;i<sizeof(*uv);i++)assert(p[i]==0);
}
int main(int argc,char **argv){
 P3DUvMap uv={0};
 assert(argc==8);
 assert(p3dUvLoad(&uv,argv[1],2));
 assert(uv.ready && uv.triangles==2 && uv.uv[0]==4096 && uv.uv[11]==-2048);
 assert(!p3dUvLoad(&uv,argv[1],1));cleared(&uv);
 assert(!p3dUvLoad(&uv,argv[2],2));cleared(&uv);
 assert(!p3dUvLoad(&uv,argv[3],2));cleared(&uv);
 assert(!p3dUvLoad(&uv,argv[4],2));cleared(&uv);
 assert(!p3dUvLoad(&uv,argv[5],2));cleared(&uv);
 assert(!p3dUvLoad(&uv,argv[6],2));cleared(&uv);
 assert(!p3dUvLoad(&uv,argv[7],2));cleared(&uv);
 assert(!p3dUvLoad(&uv,NULL,2));cleared(&uv);
 assert(!p3dUvLoad(&uv,argv[1],0));cleared(&uv);
 assert(!p3dUvLoad(&uv,argv[1],601));cleared(&uv);
 assert(!p3dUvLoad(NULL,argv[1],2));
 assert(p3dUvLoad(&uv,argv[1],2));
 assert(p3dUvLoad(&uv,argv[6],600));
 assert(uv.ready && uv.triangles==600 && uv.uv[0]==-32768 && uv.uv[3599]==32767);
 assert(p3dUvLoad(&uv,argv[1],2));
 assert(uv.ready && uv.triangles==2 && uv.uv[0]==4096 && uv.uv[11]==-2048);
 assert(uv.uv[3599]==0); /* no stale tail from the 600-face model */
 puts("C266 batched original UV transport and atomic failure: PASS");
 return 0;
}
