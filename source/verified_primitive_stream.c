#include "verified_primitive_stream.h"
#include <limits.h>
#include <string.h>
static uint16_t u16(const uint8_t *p){
    return (uint16_t)((uint16_t)p[0]|((uint16_t)p[1]<<8));
}
static uint32_t u32(const uint8_t *p){
    return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
}
int p3dVerifiedIndexInspect(const uint8_t *data,size_t size,
                            uint16_t expected_model,P3DVerifiedIndexInfo *out){
    size_t pos=10;
    uint32_t total=0;
    uint16_t previous=0;
    if(!data||!out||size<10||memcmp(data,"P3IX",4)!=0||
       u16(data+4)!=1||u16(data+6)!=expected_model||expected_model>733||
       (expected_model>=721&&expected_model<=724)||!u16(data+8)||
       u16(data+8)>64u)return 0;
    for(uint32_t m=0;m<u16(data+8);m++){
        uint16_t mesh;
        uint32_t count;
        size_t bytes;
        if(pos>size||size-pos<6)return 0;
        mesh=u16(data+pos);
        count=u32(data+pos+2);
        pos+=6;
        if(mesh>=64u||!count||(m&&mesh<=previous)||
           count>UINT32_MAX/3)return 0;
        previous=mesh;
        if(count>(size-pos)/6)return 0;
        bytes=(size_t)count*6;
        for(size_t j=0;j<bytes;j+=6){
            uint16_t a=u16(data+pos+j),b=u16(data+pos+j+2),c=u16(data+pos+j+4);
            if(a==b||b==c||a==c)return 0;
        }
        pos+=bytes;
        if(count>UINT32_MAX-total)return 0;
        total+=count;
    }
    if(pos!=size)return 0;
    out->model=expected_model;
    out->mesh_count=u16(data+8);
    out->triangles=total;
    return 1;
}
