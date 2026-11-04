#include "resume_state.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
static uint32_t crc(const unsigned char *p,unsigned n){
 uint32_t c=~0u;for(unsigned i=0;i<n;i++){c^=p[i];for(int k=0;k<8;k++)c=(c>>1)^((c&1u)?0xedb88320u:0);}return ~c;
}
static void w32(unsigned char *p,uint32_t n){for(int i=0;i<4;i++)p[i]=(unsigned char)(n>>(8*i));}
int main(int argc,char **argv){
 assert(argc==3);
 char path[300];unsigned char b[96]={0};P3DResumeState s;
 if(!strcmp(argv[2],"verify")){
  assert(p3dResumeLoad(argv[1],&s));
  assert(s.dex_learnset_valid==1&&s.dex_learnset_page==63&&s.dex_learnset_checksum==0xabcdef01u);
  puts("C334 exact page/checksum across process restart: PASS");return 0;
 }
 if(!strcmp(argv[2],"torn")){
  snprintf(path,sizeof(path),"%s_resume_A.sav",argv[1]);
  FILE *f=fopen(path,"wb");assert(f);assert(fwrite("P3RV",1,4,f)==4);assert(!fclose(f));
  assert(p3dResumeLoad(argv[1],&s));
  assert(s.dex_learnset_valid&&s.dex_learnset_page==3&&s.dex_learnset_checksum==0x12345678u);
  s.dex_learnset_valid=0;s.dex_learnset_page=0;s.dex_learnset_checksum=0;s.dex_detail_tab=1;
  assert(p3dResumeStore(argv[1],&s));assert(p3dResumeLoad(argv[1],&s));
  assert(!s.dex_learnset_valid&&s.dex_detail_tab==1);
  s.dex_detail_tab=0;assert(p3dResumeStore(argv[1],&s));
  assert(p3dResumeLoad(argv[1],&s)&&!s.dex_learnset_valid&&!s.dex_detail_tab);
  puts("C334 torn v6 fallback, legacy v5 and inactive v3 transitions: PASS");return 0;
 }
 assert(!strcmp(argv[2],"write"));
 snprintf(path,sizeof(path),"%s_resume_A.sav",argv[1]);
 memcpy(b,"P3RV",4);b[4]=6;b[8]=1;b[13]=P3D_PAGE_DEX;
 b[16]=25;b[20]=25;b[76]=4;b[77]=3;
 w32(b+80,0x12345678u);w32(b+92,crc(b,92));
 FILE *f=fopen(path,"wb");assert(f);assert(fwrite(b,1,96,f)==96);assert(!fclose(f));
 assert(p3dResumeLoad(argv[1],&s));
 assert(s.dex_detail_tab==4 && s.dex==25);
 assert(s.dex_learnset_valid==1&&s.dex_learnset_page==3&&s.dex_learnset_checksum==0x12345678u);
 assert(p3dResumeStore(argv[1],&s)); /* B retains initial valid checkpoint */
 s.dex_learnset_page=63;s.dex_learnset_checksum=0xabcdef01u;
 assert(p3dResumeStore(argv[1],&s)); /* newest A, corruption target */
 P3DResumeState loaded;assert(p3dResumeLoad(argv[1],&loaded));
 assert(loaded.dex_learnset_page==63&&loaded.dex_learnset_checksum==0xabcdef01u);
 s.dex_learnset_page=64;assert(!p3dResumeStore(argv[1],&s));s.dex_learnset_page=0;
 s.dex_detail_tab=1;assert(!p3dResumeStore(argv[1],&s));s.dex_detail_tab=4;
 s.home=1;assert(!p3dResumeStore(argv[1],&s));s.home=0;
 s.dex_learnset_valid=0;assert(!p3dResumeStore(argv[1],&s));
 puts("C334 learnset v6 checkpoint: PASS");
 return 0;
}
