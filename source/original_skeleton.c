#include "original_skeleton.h"
#include <stdio.h>
#include <string.h>
#define P3SK_HEADER_BYTES 20u
static unsigned get16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
static uint32_t get32(const unsigned char *p){return (uint32_t)get16(p)|((uint32_t)get16(p+2)<<16);}
static uint32_t crc_update(uint32_t crc,const unsigned char *p,unsigned n){
    for(unsigned i=0;i<n;i++){
        crc^=p[i];
        for(unsigned k=0;k<8;k++)
            crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
    }
    return crc;
}
void p3dOriginalSkeletonClear(P3DOriginalSkeleton *out){
    if(out)memset(out,0,sizeof(*out));
}
const char *p3dOriginalSkeletonName(const P3DOriginalSkeleton *s,unsigned index){
    if(!s||!s->ready||index>=s->node_count)return NULL;
    const unsigned char *node=s->records+index*P3D_SKELETON_NODE_BYTES;
    uint32_t offset=get32(node+52);
    if(offset>=s->string_bytes)return NULL;
    return s->strings+offset;
}
int p3dOriginalSkeletonParent(const P3DOriginalSkeleton *s,unsigned index){
    if(!s||!s->ready||index>=s->node_count)return -2;
    unsigned parent=get16(s->records+index*P3D_SKELETON_NODE_BYTES+48);
    return parent==65535u?-1:(int)parent;
}
const unsigned char *p3dOriginalSkeletonMatrixBytes(const P3DOriginalSkeleton *s,unsigned index){
    if(!s||!s->ready||index>=s->node_count)return NULL;
    return s->records+index*P3D_SKELETON_NODE_BYTES;
}
int p3dOriginalSkeletonLoad(P3DOriginalSkeleton *out,const char *path,unsigned expected_model_id){
    FILE *f=NULL;
    unsigned char head[P3SK_HEADER_BYTES];
    unsigned model,n,roots,string_len,table_len,seen_roots=0;
    uint32_t expected_crc,crc=0xffffffffu;
    if(!out)return 0;
    p3dOriginalSkeletonClear(out);
    if(!path||expected_model_id>=738u)return 0;
    f=fopen(path,"rb");if(!f)return 0;
    if(fread(head,1,sizeof(head),f)!=sizeof(head) ||
       memcmp(head,"P3SK",4)!=0 || get16(head+4)!=1 ||
       get16(head+6)!=expected_model_id)goto fail;
    model=get16(head+6);
    n=get16(head+8);
    roots=get16(head+10);
    string_len=get32(head+12);
    expected_crc=get32(head+16);
    if(n<1||n>P3D_SKELETON_MAX_NODES||roots<1||roots>n||
       string_len<1||string_len>P3D_SKELETON_MAX_STRING_BYTES)goto fail;
    table_len=n*P3D_SKELETON_NODE_BYTES;
    if(fread(out->records,1,table_len,f)!=table_len ||
       fread(out->strings,1,string_len,f)!=string_len ||
       fgetc(f)!=EOF || ferror(f))goto fail;
    crc=crc_update(crc,out->records,table_len);
    crc=crc_update(crc,(const unsigned char *)out->strings,string_len);
    if((crc^0xffffffffu)!=expected_crc)goto fail;
    for(unsigned i=0;i<n;i++){
        const unsigned char *node=out->records+i*P3D_SKELETON_NODE_BYTES;
        unsigned parent=get16(node+48);
        unsigned kind=get16(node+50);
        uint32_t offset=get32(node+52);
        if(kind!=1|| (parent!=65535u && parent>=i) || offset>=string_len)goto fail;
        if(parent==65535u)seen_roots++;
        for(unsigned j=0;j<12;j++){
            uint32_t bits=get32(node+j*4);
            /* Reject NaN and infinity by IEEE float32 exponent bits,
             * without introducing a DS floating-point runtime dependency. */
            if((bits&0x7f800000u)==0x7f800000u)goto fail;
        }
        unsigned pos=offset;
        if(out->strings[pos]==0)goto fail;
        while(pos<string_len && out->strings[pos]){
            unsigned char c=(unsigned char)out->strings[pos];
            if(c<32||c>126||pos-offset>=96)goto fail;
            pos++;
        }
        if(pos==string_len)goto fail;
        /* Original C5 string suffix interning is allowed, but duplicate
         * names in one verified hierarchy remain invalid/ambiguous. */
        for(unsigned j=0;j<i;j++){
            unsigned old=get32(out->records+j*P3D_SKELETON_NODE_BYTES+52);
            if(strcmp(out->strings+old,out->strings+offset)==0)goto fail;
        }
    }
    if(seen_roots!=roots)goto fail;
    out->model_id=(uint16_t)model;
    out->node_count=(uint16_t)n;
    out->root_count=(uint16_t)roots;
    out->string_bytes=string_len;
    out->ready=1;
    fclose(f);
    return 1;
fail:
    fclose(f);
    p3dOriginalSkeletonClear(out);
    return 0;
}
/* C150: exact original node name attachment for source-verified tracks.
 * The loader already rejects duplicate names and invalid parent indices. */
int p3dOriginalSkeletonFindNode(const P3DOriginalSkeleton *s,const char *name){
    unsigned length=0;
    if(!s||!s->ready||!name||!name[0])return -1;
    /* Source node names are bounded to 96 bytes in P3SK. Never match an
     * arbitrary long or truncated caller string. */
    while(length<=96u && name[length])length++;
    if(length==0||length>96u)return -1;
    for(unsigned i=0;i<s->node_count;i++){
        const char *source=p3dOriginalSkeletonName(s,i);
        if(source && strcmp(source,name)==0)return (int)i;
    }
    return -1;
}
int p3dOriginalSkeletonIsAncestor(const P3DOriginalSkeleton *s,
                                  unsigned ancestor,unsigned descendant){
    if(!s||!s->ready||ancestor>=s->node_count||
       descendant>=s->node_count||ancestor==descendant)return 0;
    /* Even if memory is modified after loading, this bounded walk cannot
     * cycle indefinitely or read outside the source-validated node table. */
    unsigned current=descendant;
    for(unsigned depth=0;depth<s->node_count;depth++){
        int parent=p3dOriginalSkeletonParent(s,current);
        if(parent<0||parent>=(int)s->node_count)return 0;
        if((unsigned)parent==ancestor)return 1;
        if((unsigned)parent>=current)return 0;
        current=(unsigned)parent;
    }
    return 0;
}
