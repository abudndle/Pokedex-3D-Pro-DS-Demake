#include "resume_state.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static uint32_t crc32(const unsigned char *p,unsigned n){
 uint32_t c=~0u;
 for(unsigned i=0;i<n;i++){c^=p[i];for(int k=0;k<8;k++)c=(c>>1)^((c&1u)?0xedb88320u:0);}
 return ~c;
}
static void u32(unsigned char *p,uint32_t v){for(int i=0;i<4;i++)p[i]=(unsigned char)(v>>(i*8));}
static void path(char out[300],const char *base,int slot){
 int n=snprintf(out,300,"%s_resume_%c.sav",base,slot?'B':'A');
 assert(n>0&&n<300);
}
static void write_file(const char *name,const unsigned char *b,unsigned size){
 FILE *f=fopen(name,"wb");assert(f);assert(fwrite(b,1,size,f)==size);assert(fclose(f)==0);
}
static void setup(P3DResumeState *s,unsigned page){
 memset(s,0,sizeof(*s));
 s->page=P3D_PAGE_DEX;s->dex=25;s->selected_dex=25;
 s->dex_detail_tab=4;s->dex_learnset_page=(uint8_t)page;
}
int main(int argc,char **argv){
 P3DResumeState s,out;
 char a[300],b[300];unsigned char bytes[96];FILE *f;
 assert(argc==3);path(a,argv[2],0);path(b,argv[2],1);
 if(!strcmp(argv[1],"first")){
  setup(&s,0);assert(p3dResumeStore(argv[2],&s));
  f=fopen(a,"rb");assert(f);
  assert(fread(bytes,1,96,f)==96&&fgetc(f)==EOF);assert(fclose(f)==0);
  assert(bytes[4]==5&&bytes[76]==4&&bytes[77]==0);
 }else if(!strcmp(argv[1],"paged")){
  assert(p3dResumeLoad(argv[2],&s)&&s.dex_detail_tab==4&&!s.dex_learnset_page);
  s.dex_learnset_page=63;assert(p3dResumeStore(argv[2],&s));
  f=fopen(b,"rb");assert(f);
  assert(fread(bytes,1,96,f)==96&&fgetc(f)==EOF);assert(fclose(f)==0);
  assert(bytes[4]==6&&bytes[76]==4&&bytes[77]==63);
 }else if(!strcmp(argv[1],"verify")){
  assert(p3dResumeLoad(argv[2],&s));
  assert(s.dex_detail_tab==4 && s.dex_learnset_page==63 && s.dex==25);
  setup(&out,64);assert(!p3dResumeStore(argv[2],&out));
  setup(&out,1);out.dex_detail_tab=3;assert(!p3dResumeStore(argv[2],&out));
  setup(&out,1);out.home=1;assert(!p3dResumeStore(argv[2],&out));
  setup(&out,1);out.page=P3D_PAGE_SEARCH;assert(!p3dResumeStore(argv[2],&out));
 }else if(!strcmp(argv[1],"corrupt")){
  f=fopen(b,"rb");assert(f);
  assert(fread(bytes,1,96,f)==96);assert(fclose(f)==0);
  bytes[78]=1;u32(bytes+92,crc32(bytes,92));write_file(b,bytes,96);
 }else if(!strcmp(argv[1],"fallback")){
  assert(p3dResumeLoad(argv[2],&s));
  assert(s.dex_detail_tab==4 && s.dex_learnset_page==0);
  setup(&out,1);assert(p3dResumeStore(argv[2],&out));
 }else if(!strcmp(argv[1],"verify-last")){
  assert(p3dResumeLoad(argv[2],&s)&&s.dex_learnset_page==1);
  setup(&out,0);assert(p3dResumeStore(argv[2],&out));
  assert(p3dResumeLoad(argv[2],&s)&&!s.dex_learnset_page);
 }else assert(!"bad C334 test stage");
 puts("C334 exact paged learnset resume/CRC/v1-v5 compatibility: PASS");
}
