#include "model_materials.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 P3DMaterialMap m={0};
 assert(argc==3);
 assert(p3dMaterialForTriangle(&m,0)==-1);
 assert(p3dMaterialMapLoad(&m,argv[1],3));
 assert(m.count==2);
 assert(p3dMaterialForTriangle(&m,0)==5);
 assert(p3dMaterialForTriangle(&m,1)==5);
 assert(p3dMaterialForTriangle(&m,2)==9);
 assert(p3dMaterialForTriangle(&m,3)==-1);
 assert(!p3dMaterialMapLoad(&m,argv[2],3));
 assert(p3dMaterialForTriangle(&m,0)==-1);
 puts("Material ranges: PASS");
 return 0;
}
