#include "verified_primitive_bridge.h"
#include "verified_primitive_stream.h"
#include <stdint.h>
static uint16_t rd16(const uint8_t *p){
    return (uint16_t)((uint16_t)p[0]|((uint16_t)p[1]<<8));
}
static uint32_t rd32(const uint8_t *p){
    return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
}
int p3dVerifiedPrimitiveBridge(const uint8_t *indices,size_t size,
    uint16_t expected_model,const P3DPrimitiveVertices *meshes,size_t mesh_count,
    P3DPrimitiveTriangleSink sink,void *context,uint32_t *emitted){
    P3DVerifiedIndexInfo info;
    size_t pos;
    uint32_t total=0;
    if(emitted)*emitted=0;
    if(!indices||!meshes||!sink||!mesh_count||mesh_count>UINT16_MAX||
       !p3dVerifiedIndexInspect(indices,size,expected_model,&info)||
       mesh_count!=info.mesh_count)return 0;
    /* First pass checks every referenced source vertex, before any callback. */
    for(int pass=0;pass<2;pass++){
        pos=10;
        for(size_t m=0;m<mesh_count;m++){
            uint16_t mesh=rd16(indices+pos);
            uint32_t count=rd32(indices+pos+2);
            pos+=6;
            if(mesh!=meshes[m].mesh_id||!meshes[m].xyz||
               meshes[m].vertex_count<3||meshes[m].vertex_count>UINT16_MAX+1u)return 0;
            for(uint32_t t=0;t<count;t++){
                uint16_t a=rd16(indices+pos),b=rd16(indices+pos+2),
                         c=rd16(indices+pos+4);
                if(a>=meshes[m].vertex_count||b>=meshes[m].vertex_count||
                   c>=meshes[m].vertex_count)return 0;
                if(pass==1){
                    if(!sink(context,mesh,meshes[m].xyz+(size_t)a*3,
                        meshes[m].xyz+(size_t)b*3,
                        meshes[m].xyz+(size_t)c*3))return 0;
                    total++;
                }
                pos+=6;
            }
        }
    }
    if(emitted)*emitted=total;
    return total==info.triangles;
}
