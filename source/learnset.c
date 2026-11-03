#include "learnset.h"
#include <stdio.h>
#include <string.h>
#define P3SL_HEADER 16u
#define P3SL_ROW 4u
#define P3SL_TRAILER 4u
#define P3SL_MAX_SIZE (P3SL_HEADER+P3D_LEARNSET_MAX_ROWS*P3SL_ROW+P3SL_TRAILER)
static unsigned r16(const unsigned char *b){return (unsigned)b[0]|((unsigned)b[1]<<8);}
static uint32_t r32(const unsigned char *b){
 return (uint32_t)r16(b)|((uint32_t)r16(b+2)<<16);
}
static uint32_t checksum(const unsigned char *p,unsigned n){
 uint32_t c=0xffffffffu;
 for(unsigned i=0;i<n;i++){
  c^=p[i];
  for(int k=0;k<8;k++)c=(c>>1)^((c&1u)?0xedb88320u:0);
 }
 return ~c;
}
void p3dLearnsetClear(P3DLearnset *out){if(out)memset(out,0,sizeof(*out));}
int p3dLearnsetPath(char path[80],int species,int form){
 int n;
 if(!path||species<0||(unsigned)species>=P3D_LEARNSET_SPECIES||
    form<0||(unsigned)form>P3D_LEARNSET_MAX_FORM)return 0;
 n=snprintf(path,80,"nitro:/learnsets/s%03d-f%03d.p3sl",species,form);
 return n>0&&n<80;
}
int p3dLearnsetLoad(const char *path,int species,int form,P3DLearnset *out){
 unsigned char bytes[P3SL_MAX_SIZE];
 P3DLearnset candidate;
 FILE *f;
 size_t len;
 unsigned count;
 if(!out)return 0;
 p3dLearnsetClear(out);
 if(!path||!*path||species<0||(unsigned)species>=P3D_LEARNSET_SPECIES||
    form<0||(unsigned)form>P3D_LEARNSET_MAX_FORM)return 0;
 f=fopen(path,"rb");if(!f)return 0;
 len=fread(bytes,1,sizeof(bytes),f);
 int exact=fgetc(f)==EOF && !ferror(f);
 if(fclose(f)!=0)exact=0;
 if(!exact||len<P3SL_HEADER+P3SL_TRAILER||
    memcmp(bytes,"P3SL",4)!=0||bytes[4]!=1||bytes[5]!=0||
    r16(bytes+6)!=(unsigned)species||r16(bytes+8)!=(unsigned)form||
    r32(bytes+12)!=0)return 0;
 count=r16(bytes+10);
 if(count>P3D_LEARNSET_MAX_ROWS ||
    len!=P3SL_HEADER+count*P3SL_ROW+P3SL_TRAILER ||
    r32(bytes+len-4)!=checksum(bytes,(unsigned)len-4))return 0;
 p3dLearnsetClear(&candidate);
 candidate.species=(uint16_t)species;
 candidate.form=(uint16_t)form;
 candidate.count=(uint16_t)count;
 for(unsigned i=0;i<count;i++){
   const unsigned char *p=bytes+P3SL_HEADER+i*P3SL_ROW;
   P3DLearnsetRow *row=&candidate.entries[i];
   row->move_index=(uint16_t)r16(p);
   row->method=p[2];
   row->level=p[3];
   if(row->move_index>=P3D_LEARNSET_MOVE_COUNT||
      row->method<P3D_LEARN_LEVEL||row->method>P3D_LEARN_EVENT||
      (row->method==P3D_LEARN_LEVEL &&
       (row->level<1||row->level>100))||
      (row->method!=P3D_LEARN_LEVEL && row->level!=0))return 0;
   /* Multiple methods for a move are valid; identical method/level/move
    * triples are not (cannot convey any distinct source identity). */
   for(unsigned j=0;j<i;j++){
      P3DLearnsetRow *previous=&candidate.entries[j];
      if(previous->move_index==row->move_index &&
         previous->method==row->method &&
         previous->level==row->level)return 0;
   }
 }
 candidate.ready=1;
 *out=candidate;
 return 1;
}
unsigned p3dLearnsetPageCount(const P3DLearnset *set){
 if(!set||!set->ready)return 0;
 return (set->count+P3D_LEARNSET_PAGE_ROWS-1u)/P3D_LEARNSET_PAGE_ROWS;
}
unsigned p3dLearnsetStep(const P3DLearnset *set,unsigned page,int direction){
 unsigned count=p3dLearnsetPageCount(set);
 if(!count)return 0;
 if(page>=count)page=count-1u;
 if(direction<0 && page>0)page--;
 else if(direction>0 && page+1u<count)page++;
 return page;
}
const char *p3dLearnsetMethodName(int method){
 switch(method){
 case P3D_LEARN_LEVEL:return "Level";
 case P3D_LEARN_TM:return "TM";
 case P3D_LEARN_EGG:return "Egg";
 case P3D_LEARN_TUTOR:return "Tutor";
 case P3D_LEARN_EVENT:return "Event";
 default:return "Unknown";
 }
}
