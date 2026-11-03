#include "verified_primitive_uv_bridge.h"
#include "verified_primitive_stream.h"
#include <stddef.h>
static uint16_t rd16(const uint8_t *p){
    return (uint16_t)((uint16_t)p[0]|((uint16_t)p[1]<<8));
}
static int vertex(const P3DVerifiedGeometryPair *g,
    const P3DVerifiedVertexUv *uv,unsigned mesh,unsigned index,
    P3DPrimitiveUvVertex *out){
    if(!out||mesh>=g->mesh_count||
       !p3dVerifiedVertexUvGetPaired(uv,g,mesh,index,&out->u,&out->v))
        return 0;
    out->xyz=g->meshes[mesh].xyz+(size_t)index*3u;
    return 1;
}
int p3dVerifiedPrimitiveUvBridge(const P3DVerifiedGeometryPair *g,
    const P3DVerifiedVertexUv *uv,P3DPrimitiveUvTriangleSink sink,
    void *context){
    P3DVerifiedIndexInfo info;
    size_t pos=10;
    if(!g||!uv||!sink||!g->ready||!uv->ready||
       !g->mesh_count||g->mesh_count>P3D_VERTEX_MAX_MESHES||
       !g->ix_size||g->ix_size>sizeof(g->ix)||
       !p3dVerifiedIndexInspect(g->ix,g->ix_size,g->model,&info)||
       info.mesh_count!=g->mesh_count||info.triangles!=g->triangles||
       uv->model!=g->model||uv->mesh_count!=g->mesh_count)
        return 0;
    /* Pass one is side-effect free: every indexed vertex must have a valid
     * source-paired UV before the first renderer callback is allowed. */
    for(unsigned m=0;m<info.mesh_count;m++){
        uint16_t id=rd16(g->ix+pos);
        uint32_t count=(uint32_t)g->ix[pos+2]|
            ((uint32_t)g->ix[pos+3]<<8)|((uint32_t)g->ix[pos+4]<<16)|
            ((uint32_t)g->ix[pos+5]<<24);
        pos+=6;
        if(id!=g->meshes[m].mesh_id||count>info.triangles)return 0;
        for(uint32_t t=0;t<count;t++){
            uint16_t a=rd16(g->ix+pos),b=rd16(g->ix+pos+2),
                     c=rd16(g->ix+pos+4);
            P3DPrimitiveUvVertex va,vb,vc;
            if(!vertex(g,uv,m,a,&va)||!vertex(g,uv,m,b,&vb)||
               !vertex(g,uv,m,c,&vc))return 0;
            pos+=6;
        }
    }
    if(pos!=g->ix_size)return 0;
    /* Pass two repeats the validated walk and publishes complete triangles. */
    pos=10;
    for(unsigned m=0;m<info.mesh_count;m++){
        uint16_t id=rd16(g->ix+pos);
        uint32_t count=(uint32_t)g->ix[pos+2]|
            ((uint32_t)g->ix[pos+3]<<8)|((uint32_t)g->ix[pos+4]<<16)|
            ((uint32_t)g->ix[pos+5]<<24);
        pos+=6;
        for(uint32_t t=0;t<count;t++){
            uint16_t a=rd16(g->ix+pos),b=rd16(g->ix+pos+2),
                     c=rd16(g->ix+pos+4);
            P3DPrimitiveUvVertex va,vb,vc;
            if(!vertex(g,uv,m,a,&va)||!vertex(g,uv,m,b,&vb)||
               !vertex(g,uv,m,c,&vc)||
               !sink(context,id,&va,&vb,&vc))return 0;
            pos+=6;
        }
    }
    return 1;
}
