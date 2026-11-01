#include "source_track_bindings.h"
#include <stdio.h>
#include <string.h>
#define P3TB_HEADER_BYTES 20u
static unsigned get16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
static uint32_t get32(const unsigned char *p){return (uint32_t)get16(p)|((uint32_t)get16(p+2)<<16);}
static uint32_t crc_update(uint32_t crc,const unsigned char *p,unsigned n){
    for(unsigned i=0;i<n;i++){
        crc^=p[i];
        for(unsigned k=0;k<8;k++)crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
    }
    return crc;
}
void p3dSourceTrackBindingsClear(P3DSourceTrackBindings *out){
    if(out)memset(out,0,sizeof(*out));
}
int p3dSourceTrackBindingsLoad(P3DSourceTrackBindings *out,
    const P3DOriginalSkeleton *rig,const char *path,unsigned expected_model_id){
    FILE *f=NULL;
    unsigned char head[P3TB_HEADER_BYTES],record[P3D_TRACK_BINDING_RECORD_BYTES];
    unsigned count,prev=0;
    uint32_t crc=0xffffffffu,rig_crc=0xffffffffu;
    if(!out)return 0;
    p3dSourceTrackBindingsClear(out);
    if(!rig||!rig->ready||!path||expected_model_id>=738u||
       rig->model_id!=expected_model_id||rig->node_count<1||
       rig->node_count>P3D_SKELETON_MAX_NODES||
       rig->string_bytes>P3D_SKELETON_MAX_STRING_BYTES)return 0;
    f=fopen(path,"rb");if(!f)return 0;
    if(fread(head,1,sizeof(head),f)!=sizeof(head)||
       memcmp(head,"P3TB",4)!=0||get16(head+4)!=1||
       get16(head+6)!=expected_model_id||get16(head+10)!=0)goto fail;
    count=get16(head+8);
    if(count<1||count>rig->node_count)goto fail;
    rig_crc=crc_update(rig_crc,rig->records,
                       (unsigned)rig->node_count*P3D_SKELETON_NODE_BYTES);
    rig_crc=crc_update(rig_crc,(const unsigned char *)rig->strings,rig->string_bytes);
    if((rig_crc^0xffffffffu)!=get32(head+12))goto fail;
    for(unsigned i=0;i<count;i++){
        unsigned node,offset,first;
        const char *original;
        const unsigned char *source_record;
        const unsigned char *end;
        if(fread(record,1,sizeof(record),f)!=sizeof(record))goto fail;
        crc=crc_update(crc,record,sizeof(record));
        node=get16(record);offset=get16(record+2);first=get32(record+4);
        if(node>=rig->node_count||offset>=rig->string_bytes||
           (i && first<=prev))goto fail;
        source_record=rig->records+node*P3D_SKELETON_NODE_BYTES;
        if(get32(source_record+52)!=offset)goto fail;
        original=p3dOriginalSkeletonName(rig,node);
        end=(const unsigned char *)memchr(record+8,0,P3D_TRACK_BINDING_NAME_BYTES);
        if(!original||!end||end==record+8||
           (unsigned)(end-(record+8))>96u||
           strcmp(original,(const char *)record+8)!=0)goto fail;
        for(const unsigned char *p=end+1;p<record+sizeof(record);p++)
            if(*p)goto fail;
        for(unsigned j=0;j<i;j++)if(out->node[j]==node)goto fail;
        out->node[i]=(uint16_t)node;
        out->source_first_track[i]=first;
        prev=first;
    }
    if(fgetc(f)!=EOF||ferror(f)||(crc^0xffffffffu)!=get32(head+16))goto fail;
    fclose(f);
    out->model_id=(uint16_t)expected_model_id;
    out->count=(uint16_t)count;
    out->ready=1;
    return 1;
fail:
    fclose(f);
    p3dSourceTrackBindingsClear(out);
    return 0;
}
