#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "verified_primitive_stream.h"
int main(void){
    const uint8_t valid[]={
        'P','3','I','X',1,0,0,0,1,0,
        0,0,2,0,0,0,
        0,0,1,0,2,0,1,0,2,0,3,0
    };
    uint8_t corrupt[sizeof(valid)];
    P3DVerifiedIndexInfo info={0};
    assert(p3dVerifiedIndexInspect(valid,sizeof(valid),0,&info));
    assert(info.model==0&&info.mesh_count==1&&info.triangles==2);
    assert(!p3dVerifiedIndexInspect(valid,sizeof(valid)-1,0,&info));
    assert(!p3dVerifiedIndexInspect(valid,sizeof(valid),1,&info));
    memcpy(corrupt,valid,sizeof(valid));
    corrupt[0]='X';
    assert(!p3dVerifiedIndexInspect(corrupt,sizeof(corrupt),0,&info));
    memcpy(corrupt,valid,sizeof(valid));
    corrupt[18]=0;corrupt[19]=0;
    assert(!p3dVerifiedIndexInspect(corrupt,sizeof(corrupt),0,&info));
    return 0;
}
