#include "model_texture_catalog.h"
#include <stdio.h>
#include <string.h>
#define FILE_MAX 8192u
#define HEADER_SIZE 20u
#define ENTRY_SIZE 48u
static unsigned rd16(const unsigned char *p){return (unsigned)p[0] | ((unsigned)p[1]<<8);}
static unsigned rd32(const unsigned char *p){return rd16(p)|(rd16(p+2)<<16);}
static uint32_t crc32bytes(const unsigned char *p,unsigned n){
    uint32_t c=0xffffffffu;
    for(unsigned i=0;i<n;++i){
        c^=p[i];
        for(unsigned b=0;b<8;++b)c=(c>>1)^((c&1u)?0xedb88320u:0u);
    }
    return c^0xffffffffu;
}
int p3dTextureCatalogLoad(P3DModelTextureCatalog *out,const char *path,unsigned expected_model_id){
    unsigned char buf[FILE_MAX];
    unsigned n,count,pos;
    FILE *fp;
    if(!out)return 0;
    memset(out,0,sizeof(*out));
    if(!path || expected_model_id>=738)return 0;
    fp=fopen(path,"rb");if(!fp)return 0;
    n=(unsigned)fread(buf,1,sizeof(buf),fp);
    if(ferror(fp)||fgetc(fp)!=EOF){fclose(fp);return 0;}
    fclose(fp);
    if(n<HEADER_SIZE || memcmp(buf,"P3TM",4) || rd16(buf+4)!=1 ||
       rd16(buf+6)!=expected_model_id || rd16(buf+10)!=0 ||
       rd32(buf+12)!=n-HEADER_SIZE ||
       crc32bytes(buf+HEADER_SIZE,n-HEADER_SIZE)!=rd32(buf+16))return 0;
    count=rd16(buf+8);
    if(count==0 || count>P3D_TX_MAX_ENTRIES)return 0;
    pos=HEADER_SIZE;
    for(unsigned i=0;i<count;++i){
        P3DTextureDescriptor *t=&out->entries[i];
        unsigned sz;
        if(n-pos<ENTRY_SIZE)return 0;
        if(rd16(buf+pos)!=i)return 0;
        t->width=(uint16_t)rd16(buf+pos+2);
        t->height=(uint16_t)rd16(buf+pos+4);
        t->original_format=rd32(buf+pos+6);
        t->original_offset=rd32(buf+pos+10);
        memcpy(t->original_sha256,buf+pos+14,32);
        sz=rd16(buf+pos+46);
        pos+=ENTRY_SIZE;
        if(sz==0 || sz>=P3D_TX_MAX_NAME || sz>n-pos ||
           !t->width || !t->height || t->width>4096 || t->height>4096 ||
           !t->original_offset)return 0;
        for(unsigned k=0;k<sz;++k){
            if(buf[pos+k]<32 || buf[pos+k]>126)return 0;
        }
        memcpy(t->original_name,buf+pos,sz);
        t->original_name[sz]='\0';
        pos+=sz;
    }
    if(pos!=n)return 0;
    out->model_id=(uint16_t)expected_model_id;
    out->texture_count=(uint16_t)count;
    out->ready=1;
    return 1;
}
