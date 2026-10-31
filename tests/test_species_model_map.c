#include "species_model_map.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
    P3DModelMap map={0};
    assert(argc==3);
    assert(p3dModelMapResolve(&map,0)==-1);
    assert(!p3dModelMapLoad(&map,argv[2]));
    assert(p3dModelMapResolve(&map,0)==-1);
    assert(p3dModelMapLoad(&map,argv[1]));
    assert(p3dModelMapResolve(&map,0)==737);
    assert(p3dModelMapResolve(&map,1)==-1);
    assert(p3dModelMapResolve(&map,648)==0);
    assert(p3dModelMapResolve(&map,649)==-1);
    assert(p3dModelMapResolve(&map,-1)==-1);
    puts("Verified species model mapping: PASS");
    return 0;
}
