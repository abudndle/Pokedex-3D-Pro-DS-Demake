#include "records.h"
#include <stddef.h>
#include <stdio.h>
#include <string.h>

/* Fixed-width 160-byte dual-slot P3RC v1 with CRC32 and revision counter.
 * Recovered from the user's C18 source, with no proprietary assets included.
 * Existing P3SV progress saves remain independent and compatible. */
#define P3RC_SIZE 160
#define P3RC_VERSION 1
#define P3RC_SEEN_AT 16
#define P3RC_RECENT_AT 100
#define P3RC_RUNS_AT 116
#define P3RC_BEST_AT 130
#define P3RC_ROUNDS_AT 140
#define P3RC_CRC_AT (P3RC_SIZE-4)
static void put16(unsigned char *b,unsigned v){b[0]=(unsigned char)v;b[1]=(unsigned char)(v>>8);}
static unsigned get16(const unsigned char *b){return (unsigned)b[0]|((unsigned)b[1]<<8);}
static void put32(unsigned char *b,uint32_t v){for(int i=0;i<4;i++)b[i]=(unsigned char)(v>>(8*i));}
static uint32_t get32(const unsigned char *b){return (uint32_t)b[0]|((uint32_t)b[1]<<8)|((uint32_t)b[2]<<16)|((uint32_t)b[3]<<24);}
static uint32_t crc32(const unsigned char *data,size_t size){
    uint32_t crc=0xffffffffu;
    for(size_t i=0;i<size;i++){
        crc^=data[i];
        for(int bit=0;bit<8;bit++)crc=(crc>>1)^((crc&1u)?0xedb88320u:0);
    }
    return ~crc;
}
void p3dRecordsReset(P3DRecords *r){
    if(!r)return;
    memset(r,0,sizeof(*r));
    for(int i=0;i<P3D_RECORD_RECENT;i++)r->recent[i]=P3D_RECORD_NO_SPECIES;
    for(int i=0;i<P3D_RECORD_CHALLENGES;i++)r->best[i]=0xffu;
}
int p3dRecordsSeen(const P3DRecords *r,int species){
    if(!r||species<0||species>=P3D_RECORD_SPECIES)return 0;
    return (r->viewed[species>>3]>>(species&7))&1;
}
int p3dRecordsValid(const P3DRecords *r){
    uint64_t runs=0;
    int seen_gap=0;
    if(!r||((r->viewed[P3D_RECORD_BYTES-1]>>1)&0x7fu))return 0;
    for(int i=0;i<P3D_RECORD_RECENT;i++){
        int id=r->recent[i];
        if(id==P3D_RECORD_NO_SPECIES){seen_gap=1;continue;}
        if(seen_gap||id>=P3D_RECORD_SPECIES||!p3dRecordsSeen(r,id))return 0;
        for(int j=0;j<i;j++)if(r->recent[j]==id)return 0;
    }
    for(int i=0;i<P3D_RECORD_CHALLENGES;i++){
        if((r->runs[i]==0 && r->best[i]!=0xffu)||
           (r->runs[i]>0 && r->best[i]>10))return 0;
        runs+=r->runs[i];
    }
    return runs<=r->rounds;
}
int p3dRecordsVisit(P3DRecords *r,int species){
    int pos=-1,changed=0;
    if(!r||species<0||species>=P3D_RECORD_SPECIES)return 0;
    if(!p3dRecordsSeen(r,species)){
        r->viewed[species>>3]|=(uint8_t)(1u<<(species&7));changed=1;
    }
    for(int i=0;i<P3D_RECORD_RECENT;i++)if(r->recent[i]==species){pos=i;break;}
    if(pos==0)return changed;
    if(pos<0)pos=P3D_RECORD_RECENT-1;
    for(int i=pos;i>0;i--)r->recent[i]=r->recent[i-1];
    r->recent[0]=(uint16_t)species;
    return 1;
}
int p3dRecordsCount(const P3DRecords *r,int first,int last){
    int n=0;
    if(!r||first<0||last>=P3D_RECORD_SPECIES||first>last)return -1;
    for(int i=first;i<=last;i++)n+=p3dRecordsSeen(r,i);
    return n;
}
int p3dRecordsTotal(const P3DRecords *r){return p3dRecordsCount(r,0,P3D_RECORD_SPECIES-1);}
int p3dRecordsComplete(P3DRecords *r,int mode,int score){
    if(!r||mode<0||mode>=P3D_RECORD_CHALLENGES||score<0||score>10)return 0;
    if(r->rounds==UINT32_MAX||r->runs[mode]==UINT16_MAX)return 0;
    r->rounds++;
    r->runs[mode]++;
    if(r->best[mode]==0xffu||score>r->best[mode])r->best[mode]=(uint8_t)score;
    return 1;
}
static void encode(unsigned char b[P3RC_SIZE],const P3DRecords *r,uint32_t seq){
    memset(b,0,P3RC_SIZE);
    memcpy(b,"P3RC",4);b[4]=P3RC_VERSION;put32(b+8,seq);
    memcpy(b+P3RC_SEEN_AT,r->viewed,P3D_RECORD_BYTES);
    for(int i=0;i<P3D_RECORD_RECENT;i++)put16(b+P3RC_RECENT_AT+i*2,r->recent[i]);
    for(int i=0;i<P3D_RECORD_CHALLENGES;i++)put16(b+P3RC_RUNS_AT+i*2,r->runs[i]);
    memcpy(b+P3RC_BEST_AT,r->best,P3D_RECORD_CHALLENGES);
    put32(b+P3RC_ROUNDS_AT,r->rounds);
    put32(b+P3RC_CRC_AT,crc32(b,P3RC_CRC_AT));
}
static int decode(const unsigned char b[P3RC_SIZE],P3DRecords *r,uint32_t *seq){
    if(memcmp(b,"P3RC",4)||b[4]!=P3RC_VERSION||
       get32(b+P3RC_CRC_AT)!=crc32(b,P3RC_CRC_AT))return 0;
    p3dRecordsReset(r);*seq=get32(b+8);
    memcpy(r->viewed,b+P3RC_SEEN_AT,P3D_RECORD_BYTES);
    for(int i=0;i<P3D_RECORD_RECENT;i++)r->recent[i]=(uint16_t)get16(b+P3RC_RECENT_AT+i*2);
    for(int i=0;i<P3D_RECORD_CHALLENGES;i++)r->runs[i]=(uint16_t)get16(b+P3RC_RUNS_AT+i*2);
    memcpy(r->best,b+P3RC_BEST_AT,P3D_RECORD_CHALLENGES);
    r->rounds=get32(b+P3RC_ROUNDS_AT);
    return p3dRecordsValid(r);
}
static int slotpath(char out[256],const char *base,int slot){
    int n;
    if(!base||!*base)return 0;
    n=snprintf(out,256,"%s_records_%c.sav",base,slot?'B':'A');
    return n>0&&n<256;
}
static int readslot(const char *base,int slot,P3DRecords *r,uint32_t *seq){
    char path[256];unsigned char b[P3RC_SIZE];FILE *f;int valid;
    if(!slotpath(path,base,slot)||(f=fopen(path,"rb"))==NULL)return 0;
    valid=fread(b,1,sizeof(b),f)==sizeof(b) && fgetc(f)==EOF;
    fclose(f);
    return valid && decode(b,r,seq);
}
static int newer(uint32_t a,uint32_t b){return (int32_t)(a-b)>0;}
int p3dRecordsLoad(const char *base,P3DRecords *out){
    P3DRecords a,b;uint32_t sa=0,sb=0;int va,vb;
    if(!out)return 0;
    va=readslot(base,0,&a,&sa);vb=readslot(base,1,&b,&sb);
    if(!va&&!vb)return 0;
    *out=va&&(!vb||!newer(sb,sa))?a:b;
    return 1;
}
int p3dRecordsStore(const char *base,const P3DRecords *r){
    P3DRecords a,b;uint32_t sa=0,sb=0,next=1;int va,vb,slot;
    unsigned char data[P3RC_SIZE];char path[256];FILE *f;
    if(!p3dRecordsValid(r))return 0;
    va=readslot(base,0,&a,&sa);vb=readslot(base,1,&b,&sb);
    if(va&&vb){int current=newer(sb,sa)?1:0;slot=1-current;next=(current?sb:sa)+1;}
    else if(va){slot=1;next=sa+1;}
    else if(vb){slot=0;next=sb+1;}
    else slot=0;
    if(!slotpath(path,base,slot))return 0;
    encode(data,r,next);f=fopen(path,"wb");if(!f)return 0;
    if(fwrite(data,1,sizeof(data),f)!=sizeof(data)){fclose(f);return 0;}
    if(fflush(f)!=0){fclose(f);return 0;}
    return fclose(f)==0;
}
