#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "verified_primitive_bridge.h"
#include "verified_primitive_stream.h"
typedef struct {int calls;int16_t first;} Seen;
static int collect(void *ctx,uint16_t mesh,const int16_t *a,const int16_t *b,const int16_t *c){
    Seen *s=(Seen*)ctx;
    assert(mesh==7&&a[0]==10&&b[0]==20&&c[0]==30);
    s->calls++;s->first=a[0];return 1;
}
int main(void){
    uint8_t index[]={'P','3','I','X',1,0,0,0,1,0,7,0,1,0,0,0,0,0,1,0,2,0};
    const int16_t xyz[]={10,0,0,20,0,0,30,0,0};
    P3DPrimitiveVertices mesh={7,xyz,3};
    Seen seen={0,0};
    uint32_t count=99;
    assert(p3dVerifiedPrimitiveBridge(index,sizeof(index),0,&mesh,1,collect,&seen,&count));
    assert(seen.calls==1&&count==1&&seen.first==10);
    index[20]=3;
    assert(!p3dVerifiedPrimitiveBridge(index,sizeof(index),0,&mesh,1,collect,&seen,&count));
    assert(seen.calls==1&&count==0);
    index[20]=2;
    mesh.mesh_id=8;
    assert(!p3dVerifiedPrimitiveBridge(index,sizeof(index),0,&mesh,1,collect,&seen,&count));
    assert(seen.calls==1);
    mesh.mesh_id=7;
    /* C196: direct native index inspection must reject mesh ID 64. */
    P3DVerifiedIndexInfo info={0};
    index[10]=64;
    assert(!p3dVerifiedIndexInspect(index,sizeof(index),0,&info));
    index[10]=7;
    assert(!p3dVerifiedPrimitiveBridge(index,sizeof(index)-1,0,&mesh,1,collect,&seen,&count));
    return 0;
}
