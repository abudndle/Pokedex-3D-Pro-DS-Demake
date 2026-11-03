#include <assert.h>
#include <stdint.h>
#include "verified_primitive_draw.h"

static int begins,ends,vertices;
void p3dTestBegin(int mode){assert(mode==0);begins++;}
void p3dTestVertex(int16_t x,int16_t y,int16_t z){
    (void)x;(void)y;(void)z;vertices++;
}
void p3dTestEnd(void){ends++;}

int main(void){
    /* Two triangles; the second is invalid only in the failing case.
       The first triangle must NOT be submitted before discovering it. */
    uint8_t indices[]={
        'P','3','I','X',1,0,14,0,1,0,
        7,0,2,0,0,0,
        0,0,1,0,2,0,
        0,0,2,0,3,0
    };
    const int16_t xyz[]={
        0,0,0,4096,0,0,0,4096,0,4096,4096,0
    };
    P3DPrimitiveVertices mesh={7,xyz,4};
    uint32_t drawn=999;
    indices[26]=9; /* Last index of second triangle: invalid vertex. */
    assert(!p3dVerifiedPrimitiveDraw(indices,sizeof(indices),14,
                                      &mesh,1,&drawn));
    assert(drawn==0&&begins==0&&ends==0&&vertices==0);
    indices[26]=3;
    assert(p3dVerifiedPrimitiveDraw(indices,sizeof(indices),14,
                                     &mesh,1,&drawn));
    assert(drawn==2&&begins==1&&ends==1&&vertices==6);
    drawn=999;
    assert(!p3dVerifiedPrimitiveDraw(indices,sizeof(indices),15,
                                      &mesh,1,&drawn));
    assert(drawn==0&&begins==1&&ends==1&&vertices==6);
    return 0;
}
