/* C179: run the ACTUAL native pair loader and GL draw adapter on owner-supplied
 * private P3VX/P3IX sidecars. No asset data is printed or committed. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "verified_geometry_pair.h"
#include "verified_primitive_draw.h"
static P3DVerifiedGeometryPair pair;
static uint32_t vertices;
static unsigned begins,ends;
void p3dTestBegin(int mode){if(mode!=0||begins!=ends)abort();begins++;}
void p3dTestVertex(int16_t x,int16_t y,int16_t z){
    (void)x;(void)y;(void)z;
    if(begins!=ends+1u)abort();
    vertices++;
}
void p3dTestEnd(void){if(begins!=ends+1u)abort();ends++;}
int main(int argc,char **argv){
    char *end;
    unsigned long model,expected;
    uint32_t drawn=0;
    if(argc!=5){fputs("usage: probe vertex.p3vx index.p3ix model expected_triangles\n",stderr);return 2;}
    model=strtoul(argv[3],&end,10);
    if(!*argv[3]||*end||model>733){fputs("invalid model\n",stderr);return 2;}
    expected=strtoul(argv[4],&end,10);
    if(!*argv[4]||*end||!expected||expected>P3D_GEOMETRY_MAX_TRIANGLES){
        fputs("invalid expected triangle count\n",stderr);return 2;
    }
    if(!p3dVerifiedGeometryPairLoad(&pair,argv[1],argv[2],(uint16_t)model)||
       !pair.ready||pair.triangles!=expected||
       !p3dVerifiedPrimitiveDraw(pair.ix,pair.ix_size,(uint16_t)model,
                                 pair.meshes,pair.mesh_count,&drawn)||
       drawn!=expected||vertices!=drawn*3u||begins!=1||ends!=1){
        fputs("C179 private geometry draw probe FAILED\n",stderr);
        return 1;
    }
    printf("C179 verified model %lu: %lu triangles, %lu meshes, native GL path OK\n",
           model,expected,(unsigned long)pair.mesh_count);
    return 0;
}
