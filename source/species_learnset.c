#include "species_learnset.h"
#include "species_details.h"
#include <stdio.h>
#include <string.h>
static unsigned r16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
static uint32_t r32(const unsigned char *p){return (uint32_t)r16(p)|((uint32_t)r16(p+2)<<16);}
static uint32_t crc(const unsigned char *p,unsigned n,uint32_t c){
    for(unsigned i=0;i<n;i++){
        c^=p[i];
        for(int k=0;k<8;k++)c=(c>>1)^((c&1u)?0xedb88320u:0);
    }
    return c;
}
int p3dLearnsetPath(char path[80],int species,int form){
    if(!path||species<0||species>=P3D_DETAIL_NATIONAL_SPECIES||
       form<0||form>P3D_DETAIL_MAX_FORM)return 0;
    int n=snprintf(path,80,"nitro:/learnsets/s%03d-f%03d.p3sl",species,form);
    return n>0&&n<80;
}
int p3dLearnsetLoad(const char *path,int species,int form,P3DLearnset *out){
    unsigned char b[16+P3D_LEARNSET_MAX*6u];
    P3DLearnset candidate={0};
    FILE *f;unsigned size,count;int ok;
    if(!out)return 0;
    memset(out,0,sizeof(*out));
    if(!path||species<0||species>=P3D_DETAIL_NATIONAL_SPECIES||
       form<0||form>P3D_DETAIL_MAX_FORM)return 0;
    f=fopen(path,"rb");if(!f)return 0;
    size=(unsigned)fread(b,1,sizeof(b),f);
    ok=!ferror(f)&&fgetc(f)==EOF&&!ferror(f);
    if(fclose(f)!=0)ok=0;
    if(!ok||size<16||memcmp(b,"P3SL",4)||b[4]!=1||b[5]!=1||
       r16(b+6)!=(unsigned)species||r16(b+8)!=(unsigned)form)return 0;
    count=r16(b+10);
    if(count>P3D_LEARNSET_MAX||size!=16+count*6u||
       r32(b+12)!=~crc(b+16,count*6u,crc(b,12,~0u)))return 0;
    /* Validate every row before publishing; incomplete files never expose
     * even their first four otherwise-valid entries to the renderer. */
    for(unsigned i=0;i<count;i++){
        const unsigned char *p=b+16+i*6u;
        P3DLearnsetRow *row=&candidate.rows[i];
        row->move=(uint16_t)r16(p);row->method=p[2];row->level=p[3];
        if(row->move>=P3D_DETAIL_MOVE_INDEX_COUNT||row->method<1||row->method>5||
           r16(p+4)!=0|| (row->method==1?(row->level<1||row->level>100):row->level!=0))
            return 0;
        for(unsigned j=0;j<i;j++){
            const P3DLearnsetRow *prior=&candidate.rows[j];
            if(prior->move==row->move&&prior->method==row->method&&prior->level==row->level)
                return 0;
        }
    }
    candidate.species=(uint16_t)species;candidate.form=(uint16_t)form;
    candidate.count=(uint16_t)count;candidate.checksum=r32(b+12);candidate.ready=1;
    *out=candidate;
    return 1;
}
unsigned p3dLearnsetPage(const P3DLearnset *set,unsigned page,int direction){
    if(!set||!set->ready||!set->count||set->count>P3D_LEARNSET_MAX)return 0;
    unsigned last=(set->count-1u)/P3D_LEARNSET_PAGE_ROWS;
    if(page>last)page=last;
    if(direction<0)return page?page-1:0;
    if(direction>0)return page<last?page+1:last;
    return page;
}
unsigned p3dLearnsetRestorePage(const P3DLearnset *set,unsigned page,uint32_t checksum){
    if(!set||!set->ready||set->checksum!=checksum||
       page>=P3D_LEARNSET_MAX/P3D_LEARNSET_PAGE_ROWS)return 0;
    /* Changed or shortened sources must reset instead of resuming an
     * unrelated row. A normal navigation clamp is deliberately separate. */
    return p3dLearnsetPage(set,page,0)==page?page:0;
}
const char *p3dLearnsetMethod(unsigned method){
    switch(method){
    case 1:return "LV";case 2:return "TM";case 3:return "EGG";
    case 4:return "TUTOR";case 5:return "EVOLVE";default:return "?";
    }
}
