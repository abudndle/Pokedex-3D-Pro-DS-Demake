#include <assert.h>
#include <stdint.h>
#include "verified_primitive_draw.h"
static int began=0,ended=0,vertices=0;
static int16_t observed[9];
void p3dTestBegin(int mode){assert(mode==0);began++;}
void p3dTestVertex(int16_t x,int16_t y,int16_t z){
    assert(began==1&&ended==0&&vertices<3);
    observed[vertices*3]=x;observed[vertices*3+1]=y;observed[vertices*3+2]=z;
    vertices++;
}
void p3dTestEnd(void){ended++;}
int main(void){
    uint8_t index[]={'P','3','I','X',1,0,0,0,1,0,7,0,1,0,0,0,0,0,1,0,2,0};
    const int16_t xyz[]={100,101,102,200,201,202,300,301,302};
    P3DPrimitiveVertices mesh={7,xyz,3};
    uint32_t drawn=99;
    assert(p3dVerifiedPrimitiveDraw(index,sizeof(index),0,&mesh,1,&drawn));
    assert(drawn==1&&began==1&&ended==1&&vertices==3);
    assert(observed[0]==100&&observed[3]==200&&observed[6]==300);
    index[20]=4;
    assert(!p3dVerifiedPrimitiveDraw(index,sizeof(index),0,&mesh,1,&drawn));
    assert(drawn==0&&began==1&&ended==1);
    return 0;
}
