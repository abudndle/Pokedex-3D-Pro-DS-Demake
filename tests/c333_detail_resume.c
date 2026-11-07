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
static void put32(unsigned char *p,uint32_t v){for(int i=0;i<4;i++)p[i]=(unsigned char)(v>>(i*8));}
static void filename(char dest[300],const char *base,int slot){
 int n=snprintf(dest,300,"%s_resume_%c.sav",base,slot?'B':'A');assert(n>0&&n<300);
}
static void write_file(const char *path,const unsigned char *b,unsigned size){
 FILE *f=fopen(path,"wb");assert(f);assert(fwrite(b,1,size,f)==size);assert(fclose(f)==0);
}
static void fixture(P3DResumeState *s,int tab){
 memset(s,0,sizeof(*s));
 s->home=0;s->page=P3D_PAGE_DEX;s->dex=25;s->selected_dex=25;
 s->selected_form=2;s->dex_detail_tab=(uint8_t)tab;
}
int main(int argc,char **argv){
 assert(argc==3);
 P3DResumeState s,restored;
 char name[300];unsigned char b[96];
 filename(name,argv[2],1);
 if(!strcmp(argv[1],"first")){
  fixture(&s,1);
  assert(p3dResumeStateValid(&s));
  assert(p3dResumeStore(argv[2],&s));
 }else if(!strcmp(argv[1],"second")){
  assert(p3dResumeLoad(argv[2],&s));assert(s.dex_detail_tab==1);
  s.dex_detail_tab=3;assert(p3dResumeStore(argv[2],&s));
  FILE *f=fopen(name,"rb");assert(f);
  assert(fread(b,1,96,f)==96&&fgetc(f)==EOF);assert(fclose(f)==0);
  assert(!memcmp(b,"P3RV",4)&&b[4]==5 && b[76]==3);
 }else if(!strcmp(argv[1],"verify")){
  assert(p3dResumeLoad(argv[2],&restored));
  assert(restored.dex==25 && restored.selected_form==2 && restored.dex_detail_tab==3);
 }else if(!strcmp(argv[1],"corrupt")){
  FILE *f=fopen(name,"rb");assert(f);
  assert(fread(b,1,96,f)==96);assert(fclose(f)==0);
  b[77]=1;put32(b+92,crc32(b,92));write_file(name,b,96);
 }else if(!strcmp(argv[1],"fallback")){
  assert(p3dResumeLoad(argv[2],&s));
  assert(s.dex_detail_tab==1 && s.selected_form==2);
  fixture(&s,6);assert(!p3dResumeStore(argv[2],&s));
  fixture(&s,1);s.home=1;assert(!p3dResumeStore(argv[2],&s));
  fixture(&s,4);s.page=P3D_PAGE_SEARCH;assert(!p3dResumeStore(argv[2],&s));
  fixture(&s,2);s.quiz_active=1;assert(!p3dResumeStore(argv[2],&s));
 }else if(!strcmp(argv[1],"close")){
  fixture(&s,0);assert(p3dResumeStore(argv[2],&s));
  assert(p3dResumeLoad(argv[2],&restored)&&!restored.dex_detail_tab);
  filename(name,argv[2],1); /* newest B after valid A fallback */
  FILE *f=fopen(name,"rb");assert(f);
  assert(fread(b,1,80,f)==80 && fgetc(f)==EOF);assert(fclose(f)==0);
  assert(b[4]==3);
 }else assert(!"bad C333 detail test mode");
 puts("C333 persistent exact Pokédex detail tab: PASS");
}
