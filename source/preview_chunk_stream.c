#include "preview_chunk_stream.h"
#include <string.h>
#define P3CS_HEADER_BYTES 24u
#define P3CS_INDEX_BYTES 16u
static unsigned rd16(const unsigned char *b){return (unsigned)b[0]|((unsigned)b[1]<<8);}
static uint32_t rd32(const unsigned char *b){return (uint32_t)rd16(b)|((uint32_t)rd16(b+2)<<16);}
static uint32_t crc_update(uint32_t crc,const unsigned char *b,unsigned n){
    for(unsigned i=0;i<n;i++){
        crc^=b[i];
        for(unsigned j=0;j<8;j++)crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
    }
    return crc;
}
void p3dChunkClose(P3DChunkStream *s){
    if(!s)return;
    if(s->file)fclose(s->file);
    memset(s,0,sizeof(*s));
}
int p3dChunkOpen(P3DChunkStream *s,const char *path,unsigned model_id){
    unsigned char h[P3CS_HEADER_BYTES],table[P3D_CHUNK_MAX*P3CS_INDEX_BYTES];
    FILE *f;long file_size;
    uint32_t cursor,tri_cursor=0,total;
    unsigned count;
    if(!s)return 0;
    p3dChunkClose(s);
    if(!path||model_id>=738)return 0;
    f=fopen(path,"rb");if(!f)return 0;
    if(fread(h,1,sizeof(h),f)!=sizeof(h)||memcmp(h,"P3CS",4)!=0||
       rd16(h+4)!=1||rd16(h+6)!=model_id||rd16(h+10)!=0){fclose(f);return 0;}
    count=rd16(h+8);total=rd32(h+12);
    if(count<1||count>P3D_CHUNK_MAX||total<1||total>P3D_CHUNK_MAX_TOTAL||
       rd32(h+16)<total||
       fread(table,1,count*P3CS_INDEX_BYTES,f)!=count*P3CS_INDEX_BYTES||
       (crc_update(0xffffffffu,table,count*P3CS_INDEX_BYTES)^0xffffffffu)!=rd32(h+20)){
        fclose(f);return 0;
    }
    cursor=P3CS_HEADER_BYTES+count*P3CS_INDEX_BYTES;
    for(unsigned i=0;i<count;i++){
        const unsigned char *p=table+i*P3CS_INDEX_BYTES;
        P3DChunkInfo *entry=&s->chunks[i];
        uint32_t first=rd32(p),offset=rd32(p+8);
        unsigned triangles=rd16(p+4);
        if(first!=tri_cursor||!triangles||triangles>P3D_CHUNK_TRIANGLES||
           rd16(p+6)!=0||offset!=cursor||triangles>total-tri_cursor){
            fclose(f);memset(s,0,sizeof(*s));return 0;
        }
        entry->first_triangle=first;
        entry->triangles=(uint16_t)triangles;
        entry->offset=offset;
        entry->crc32=rd32(p+12);
        tri_cursor+=triangles;
        cursor+=triangles*P3D_CHUNK_RECORD_BYTES;
    }
    if(tri_cursor!=total||fseek(f,0,SEEK_END)||
       (file_size=ftell(f))<0||(uint32_t)file_size!=cursor){
        fclose(f);memset(s,0,sizeof(*s));return 0;
    }
    /* Read and checksum every chunk before any geometry is marked renderable.
     * The bounded scanner allocates 128 bytes, never the whole source model. */
    for(unsigned i=0;i<count;i++){
        unsigned char scratch[128];
        uint32_t crc=0xffffffffu;
        unsigned remain=s->chunks[i].triangles*P3D_CHUNK_RECORD_BYTES;
        if(fseek(f,(long)s->chunks[i].offset,SEEK_SET)){
            fclose(f);memset(s,0,sizeof(*s));return 0;
        }
        while(remain){
            unsigned take=remain<sizeof(scratch)?remain:(unsigned)sizeof(scratch);
            if(fread(scratch,1,take,f)!=take){
                fclose(f);memset(s,0,sizeof(*s));return 0;
            }
            crc=crc_update(crc,scratch,take);
            remain-=take;
        }
        if((crc^0xffffffffu)!=s->chunks[i].crc32){
            fclose(f);memset(s,0,sizeof(*s));return 0;
        }
    }
    s->file=f;
    s->model_id=(uint16_t)model_id;
    s->chunk_count=(uint16_t)count;
    s->total_triangles=total;
    s->original_triangles=rd32(h+16);
    s->ready=1;
    return 1;
}
int p3dChunkRead(P3DChunkStream *s,unsigned index,
                 int16_t xyz[P3D_CHUNK_TRIANGLES*9],
                 int16_t uv[P3D_CHUNK_TRIANGLES*6],
                 unsigned char rgb[P3D_CHUNK_TRIANGLES*3]){
    unsigned char b[P3D_CHUNK_RECORD_BYTES];
    uint32_t crc=0xffffffffu;
    const P3DChunkInfo *c;
    if(!s||!s->ready||!s->file||index>=s->chunk_count||!xyz||!uv||!rgb)return 0;
    c=&s->chunks[index];
    if(fseek(s->file,(long)c->offset,SEEK_SET))return 0;
    for(unsigned i=0;i<c->triangles;i++){
        if(fread(b,1,sizeof(b),s->file)!=sizeof(b))return 0;
        crc=crc_update(crc,b,sizeof(b));
        for(unsigned j=0;j<9;j++)xyz[i*9+j]=(int16_t)rd16(b+j*2);
        for(unsigned j=0;j<6;j++)uv[i*6+j]=(int16_t)rd16(b+18+j*2);
        memcpy(rgb+i*3,b+30,3);
    }
    return (crc^0xffffffffu)==c->crc32;
}
