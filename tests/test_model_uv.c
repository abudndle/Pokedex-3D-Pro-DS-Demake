#include "model_uv.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 P3DUvMap uv={0};
 assert(argc==3);
 assert(p3dUvLoad(&uv,argv[1],2));
 assert(uv.triangles==2 && uv.uv[0]==4096 && uv.uv[11]==-2048);
 assert(!p3dUvLoad(&uv,argv[1],1));
 assert(!uv.ready && uv.triangles==0);
 assert(!p3dUvLoad(&uv,argv[2],2));
 assert(!uv.ready && uv.triangles==0);
 puts("Original UV metadata transport: PASS");
 return 0;
}
