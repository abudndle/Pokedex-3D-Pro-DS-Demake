#include "verified_vertex_uv.h"
#include <stdio.h>
#include <string.h>
#define UV_HEADER 20u
#define UV_ROW 8u
static uint16_t rd16(const uint8_t *p){
    return (uint16_t)((unsigned)p[0]|((unsigned)p[1]<<8));
}
static uint32_t rd32(const uint8_t *p){
    return (uint32_t)rd16(p)|((uint32_t)rd16(p+2)<<16);
}
static uint32_t crc32_bytes(const uint8_t *p,size_t n){
    uint32_t crc=0xffffffffu;
    for(size_t i=0;i<n;i++){
        crc^=p[i];
        for(unsigned j=0;j<8;j++)crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
    }
    return crc^0xffffffffu;
}
void p3dVerifiedVertexUvClear(P3DVerifiedVertexUv *uv){
    if(uv)memset(uv,0,sizeof(*uv));
}
static int validate(P3DVerifiedVertexUv *uv,const P3DVerifiedGeometryPair *g){
    unsigned count,cursor=0;
    size_t table_bytes,payload;
    if(!g||!g->ready||g->model>733||
       (g->model>=721&&g->model<=724)||!g->mesh_count||
       g->mesh_count>P3D_VERTEX_MAX_MESHES||
       !g->vx_size||g->vx_size>sizeof(g->vx)||
       uv->size<UV_HEADER||memcmp(uv->bytes,"P3VU",4)!=0||
       rd16(uv->bytes+4)!=1||rd16(uv->bytes+6)!=g->model||
       rd16(uv->bytes+10)!=0)return 0;
    count=rd16(uv->bytes+8);
    if(count!=g->mesh_count||count>P3D_VERTEX_MAX_MESHES)return 0;
    table_bytes=(size_t)count*UV_ROW;
    if(uv->size<UV_HEADER+table_bytes||
       crc32_bytes(g->vx,g->vx_size)!=rd32(uv->bytes+12)||
       crc32_bytes(uv->bytes+UV_HEADER,uv->size-UV_HEADER)!=rd32(uv->bytes+16))
        return 0;
    for(unsigned i=0;i<count;i++){
        const uint8_t *row=uv->bytes+UV_HEADER+(size_t)i*UV_ROW;
        unsigned id=rd16(row),vertices=rd16(row+2);
        uint32_t first=rd32(row+4);
        if(id!=g->meshes[i].mesh_id||vertices!=g->meshes[i].vertex_count||
           vertices<3||first!=cursor||vertices>P3D_VERTEX_MAX_VERTICES-cursor||
           g->meshes[i].xyz!=g->xyz+(size_t)cursor*3u)
            return 0;
        cursor+=vertices;
    }
    payload=UV_HEADER+table_bytes;
    if(!cursor||uv->size-payload!=(size_t)cursor*4u)return 0;
    /* The DS texture repeat/mirror operation is not yet established. Never
     * transform/out-of-range sample a source UV just to make it look right. */
    for(unsigned i=0;i<cursor*2u;i++){
        int16_t uvcoord=(int16_t)rd16(uv->bytes+payload+(size_t)i*2u);
        if(uvcoord<0||uvcoord>4096)return 0;
    }
    uv->mesh_count=count;
    uv->vertex_count=cursor;
    uv->model=g->model;
    uv->ready=1;
    return 1;
}
int p3dVerifiedVertexUvLoad(P3DVerifiedVertexUv *uv,const char *path,
                            const P3DVerifiedGeometryPair *geometry){
    FILE *f;
    int trailing,bad;
    if(!uv)return 0;
    p3dVerifiedVertexUvClear(uv);
    if(!path||!geometry||!geometry->ready)return 0;
    f=fopen(path,"rb");
    if(!f)return 0;
    /* Header first: reject oversized and truncated input before a bulk read. */
    uv->size=fread(uv->bytes,1,UV_HEADER,f);
    if(uv->size!=UV_HEADER){fclose(f);p3dVerifiedVertexUvClear(uv);return 0;}
    unsigned count=rd16(uv->bytes+8);
    if(count==0||count>P3D_VERTEX_MAX_MESHES){
        fclose(f);p3dVerifiedVertexUvClear(uv);return 0;
    }
    size_t remaining=sizeof(uv->bytes)-UV_HEADER;
    uv->size+=fread(uv->bytes+UV_HEADER,1,remaining,f);
    trailing=fgetc(f);
    bad=ferror(f)||trailing!=EOF;
    if(fclose(f)!=0)bad=1;
    if(bad){
        p3dVerifiedVertexUvClear(uv);
        return 0;
    }
    if(!validate(uv,geometry)){
        p3dVerifiedVertexUvClear(uv);
        return 0;
    }
    return 1;
}
int p3dVerifiedVertexUvGet(const P3DVerifiedVertexUv *uv,
                           unsigned mesh_index,unsigned vertex_index,
                           int16_t *u,int16_t *v){
    const uint8_t *row;
    size_t idx,offset;
    if(!uv||!uv->ready||!u||!v||!uv->mesh_count||
       uv->mesh_count>P3D_VERTEX_MAX_MESHES||
       uv->vertex_count>P3D_VERTEX_MAX_VERTICES||
       uv->size>sizeof(uv->bytes)||
       uv->size<UV_HEADER+(size_t)uv->mesh_count*UV_ROW||
       mesh_index>=uv->mesh_count)return 0;
    row=uv->bytes+UV_HEADER+(size_t)mesh_index*UV_ROW;
    if(vertex_index>=rd16(row+2))return 0;
    /* Recheck table integrity even if a caller damaged the staged state. */
    if(rd16(row+2)<3u||rd32(row+4)>uv->vertex_count||
       rd16(row+2)>uv->vertex_count-rd32(row+4))return 0;
    idx=(size_t)rd32(row+4)+vertex_index;
    if(idx>=uv->vertex_count)return 0;
    offset=UV_HEADER+(size_t)uv->mesh_count*UV_ROW+idx*4u;
    if(offset>uv->size||uv->size-offset<4u)return 0;
    /* Revalidate staged bytes before exposing either coordinate. */
    int16_t next_u=(int16_t)rd16(uv->bytes+offset);
    int16_t next_v=(int16_t)rd16(uv->bytes+offset+2);
    if(next_u<0||next_u>4096||next_v<0||next_v>4096)return 0;
    *u=next_u;
    *v=next_v;
    return 1;
}

/* Reject stale geometry, changed model bytes, or altered mesh descriptors.
 * Keep caller outputs unchanged on every failure. */
int p3dVerifiedVertexUvGetPaired(const P3DVerifiedVertexUv *uv,
    const P3DVerifiedGeometryPair *geometry,unsigned mesh_index,
    unsigned vertex_index,int16_t *u,int16_t *v){
    if(!uv||!geometry||!uv->ready||!geometry->ready||
       uv->model!=geometry->model||
       uv->mesh_count!=geometry->mesh_count||
       !geometry->vx_size||geometry->vx_size>sizeof(geometry->vx)||
       uv->size<UV_HEADER||uv->size>sizeof(uv->bytes)||
       crc32_bytes(geometry->vx,geometry->vx_size)!=rd32(uv->bytes+12)||
       geometry->mesh_count>P3D_VERTEX_MAX_MESHES||
       uv->mesh_count>P3D_VERTEX_MAX_MESHES||
       mesh_index>=geometry->mesh_count||
       uv->size<UV_HEADER+(size_t)uv->mesh_count*UV_ROW)return 0;
    const uint8_t *row=uv->bytes+UV_HEADER+(size_t)mesh_index*UV_ROW;
    if(
       rd16(row)!=geometry->meshes[mesh_index].mesh_id||
       rd16(row+2)!=geometry->meshes[mesh_index].vertex_count)return 0;
    return p3dVerifiedVertexUvGet(uv,mesh_index,vertex_index,u,v);
}
