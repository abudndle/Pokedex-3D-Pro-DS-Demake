#include "original_home_hotspots.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static int read_map(P3DHomeHotspots *map,const char *folder,const char *file){
    char path[320];
    assert(snprintf(path,sizeof(path),"%s/%s",folder,file)>0);
    return p3dHomeHotspotsLoad(map,path);
}
int main(int argc,char **argv){
    P3DHomeHotspots map;
    assert(argc==2);
    assert(read_map(&map,argv[1],"valid.p3hm"));
    assert(map.ready && p3dHomeHotspotsValidate(&map));
    assert(p3dHomeHotspotsHit(&map,8,8)==P3D_PAGE_DEX);
    assert(p3dHomeHotspotsHit(&map,64,42)==P3D_PAGE_DEX);
    assert(p3dHomeHotspotsHit(&map,65,42)==-1);
    assert(p3dHomeHotspotsHit(&map,75,8)==P3D_PAGE_MOVES);
    assert(p3dHomeHotspotsHit(&map,142,8)==P3D_PAGE_CHALLENGE);
    assert(p3dHomeHotspotsHit(&map,8,60)==P3D_PAGE_RECORDS);
    assert(p3dHomeHotspotsHit(&map,75,60)==P3D_PAGE_ALBUM);
    assert(p3dHomeHotspotsHit(&map,142,60)==P3D_PAGE_AR);
    assert(p3dHomeHotspotsHit(&map,8,112)==P3D_PAGE_SETTINGS);
    assert(p3dHomeHotspotsHit(&map,-1,10)==-1);
    assert(p3dHomeHotspotsHit(&map,256,10)==-1);
    assert(p3dHomeHotspotsHit(&map,0,192)==-1);
    assert(p3dHomeHotspotsHit(&map,200,150)==-1);
    assert(p3dHomeHotspotsHit(NULL,10,10)==-1);
    /* Invalid source cannot leave a previous page's touch rectangles live. */
    const char *invalid[]={"truncated.p3hm","trailing.p3hm",
        "badcrc.p3hm","duplicate.p3hm","overlap.p3hm",
        "outside.p3hm","unknown.p3hm","thin.p3hm"};
    for(unsigned i=0;i<sizeof(invalid)/sizeof(invalid[0]);i++){
        assert(!read_map(&map,argv[1],invalid[i]));
        assert(!map.ready);
        assert(p3dHomeHotspotsHit(&map,8,8)==-1);
    }
    assert(!read_map(&map,argv[1],"missing.p3hm"));
    assert(!p3dHomeHotspotsLoad(&map,NULL));
    assert(!p3dHomeHotspotsLoad(NULL,argv[1]));
    puts("C123 original 3DS private HOME icons: 7 hitboxes, CRC and fail-closed: PASS");
    return 0;
}
