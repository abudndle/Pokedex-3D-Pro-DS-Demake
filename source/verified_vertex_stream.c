#include "verified_vertex_stream.h"
#include <limits.h>
#include <string.h>
#define HEADER_BYTES 16u
#define TABLE_BYTES 8u
static uint16_t rd16(const uint8_t *p){
    return (uint16_t)((uint16_t)p[0]|((uint16_t)p[1]<<8));
}
static uint32_t rd32(const uint8_t *p){
    return (uint32_t)rd16(p)|((uint32_t)rd16(p+2)<<16);
}
static uint32_t crc32_bytes(const uint8_t *p,size_t n){
    uint32_t crc=0xffffffffu;
    for(size_t i=0;i<n;i++){
        crc^=p[i];
        for(unsigned j=0;j<8;j++)
            crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
    }
    return crc^0xffffffffu;
}
int p3dVerifiedVerticesDecode(const uint8_t *data,size_t size,
    uint16_t expected_model,P3DPrimitiveVertices *meshes,size_t mesh_capacity,
    int16_t *xyz,size_t xyz_capacity,size_t *decoded_mesh_count){
    size_t table_size,vertices=0,xyz_count;
    unsigned count;
    uint16_t previous=0;
    if(decoded_mesh_count)*decoded_mesh_count=0;
    if(!data||!meshes||!xyz||!decoded_mesh_count||size<HEADER_BYTES||
       memcmp(data,"P3VX",4)!=0||rd16(data+4)!=1||
       rd16(data+6)!=expected_model||expected_model>733||
       (expected_model>=721&&expected_model<=724)||rd16(data+10)!=0)
        return 0;
    count=rd16(data+8);
    if(!count||count>P3D_VERTEX_MAX_MESHES||count>mesh_capacity)return 0;
    table_size=(size_t)count*TABLE_BYTES;
    if(size<HEADER_BYTES+table_size)return 0;
    /* Validate every mesh and exact total size before touching outputs. */
    for(unsigned i=0;i<count;i++){
        const uint8_t *row=data+HEADER_BYTES+(size_t)i*TABLE_BYTES;
        uint16_t mesh=rd16(row),n=rd16(row+2);
        uint32_t first=rd32(row+4);
        if((i&&mesh<=previous)||n<3||first!=vertices||
           n>P3D_VERTEX_MAX_VERTICES-vertices)return 0;
        previous=mesh;
        vertices+=n;
    }
    if(vertices>SIZE_MAX/6u||
       vertices!=(size-HEADER_BYTES-table_size)/6u||
       (size-HEADER_BYTES-table_size)%6u||
       vertices>xyz_capacity/3u)return 0;
    xyz_count=vertices*3u;
    if(crc32_bytes(data+HEADER_BYTES,size-HEADER_BYTES)!=rd32(data+12))
        return 0;
    /* Output mutation starts only after the complete preflight succeeds. */
    const uint8_t *payload=data+HEADER_BYTES+table_size;
    for(size_t i=0;i<xyz_count;i++)xyz[i]=(int16_t)rd16(payload+i*2u);
    for(unsigned i=0;i<count;i++){
        const uint8_t *row=data+HEADER_BYTES+(size_t)i*TABLE_BYTES;
        meshes[i].mesh_id=rd16(row);
        meshes[i].vertex_count=rd16(row+2);
        meshes[i].xyz=xyz+(size_t)rd32(row+4)*3u;
    }
    *decoded_mesh_count=count;
    return 1;
}
