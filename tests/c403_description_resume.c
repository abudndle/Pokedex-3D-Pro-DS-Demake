#include "resume_state.h"
#include "species_details.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* A description checkpoint must survive a process restart without dropping
 * its exact subview, page or source fingerprint. Malformed newer slots must
 * not displace the older intact checkpoint. Fixtures are synthetic only. */
static uint32_t crc32(const unsigned char *p,unsigned n){
 uint32_t c=~0u;
 for(unsigned i=0;i<n;i++){
  c^=p[i];for(int k=0;k<8;k++)c=(c>>1)^((c&1u)?0xedb88320u:0);
 }
 return ~c;
}
static void w32(unsigned char *p,uint32_t n){
 for(int i=0;i<4;i++)p[i]=(unsigned char)(n>>(i*8));
}
static void filename(char path[300],const char *base,char slot){
 int n=snprintf(path,300,"%s_resume_%c.sav",base,slot);assert(n>0&&n<300);
}
static void write_bytes(const char *path,const unsigned char *b,unsigned n){
 FILE *f=fopen(path,"wb");assert(f);assert(fwrite(b,1,n,f)==n);assert(!fclose(f));
}
static void read_bytes(const char *path,unsigned char b[97]){
 FILE *f=fopen(path,"rb");assert(f);
 assert(fread(b,1,96,f)==96&&fgetc(f)==EOF);assert(!fclose(f));b[96]=0;
}
static void fixture(P3DResumeState *s){
 memset(s,0,sizeof(*s));s->page=P3D_PAGE_DEX;
 s->dex=25;s->selected_dex=25;s->selected_form=2;
 s->dex_detail_tab=P3D_DETAIL_DESCRIPTION_TAB;
 s->dex_description_valid=1;s->dex_description_page=47;
 s->dex_description_checksum=0x12345678u;
}
int main(int argc,char **argv){
 assert(argc==3);P3DResumeState s,loaded;
 char path[300];unsigned char b[97],valid[97];
 if(!strcmp(argv[1],"write")){
  fixture(&s);
  assert(p3dResumeStore(argv[2],&s)); /* RED: legacy codec rejects tab5. */
  filename(path,argv[2],'A');read_bytes(path,b);
  assert(!memcmp(b,"P3RV",4)&&b[4]==8&&b[76]==5&&b[77]==1&&b[78]==47);
  assert(b[79]==0&&b[80]==0x78&&b[81]==0x56&&b[82]==0x34&&b[83]==0x12);
  assert(p3dResumeLoad(argv[2],&loaded));
  assert(loaded.dex_description_valid==1&&loaded.dex_description_page==47);
  assert(loaded.dex_description_checksum==0x12345678u);
 }else if(!strcmp(argv[1],"verify")){
  assert(p3dResumeLoad(argv[2],&loaded));
  assert(loaded.dex==25&&loaded.selected_form==2&&loaded.dex_detail_tab==5);
  assert(loaded.dex_description_valid==1&&loaded.dex_description_page==47&&
         loaded.dex_description_checksum==0x12345678u);
  loaded.dex_description_page=3;loaded.dex_description_checksum=0;
  assert(p3dResumeStore(argv[2],&loaded)); /* newest B, fingerprint zero is valid */
 }else if(!strcmp(argv[1],"corrupt")){
  assert(p3dResumeLoad(argv[2],&s));
  assert(s.dex_description_valid==1&&s.dex_description_page==3&&s.dex_description_checksum==0);
  filename(path,argv[2],'B');read_bytes(path,valid);
  /* CRC-correct malformed semantic fields must reject the whole newest slot. */
  const unsigned offsets[]={4,5,6,12,13,76,77,78,79,84,91};
  const unsigned values[] ={9,1,1, 1, 2, 4, 2,48, 1, 1, 1};
  for(unsigned i=0;i<sizeof(offsets)/sizeof(offsets[0]);i++){
   memcpy(b,valid,sizeof(b));b[offsets[i]]=(unsigned char)values[i];
   w32(b+92,crc32(b,92));write_bytes(path,b,96);
   assert(p3dResumeLoad(argv[2],&loaded));
   assert(loaded.dex_description_page==47&&loaded.dex_description_checksum==0x12345678u);
  }
  memcpy(b,valid,sizeof(b));b[77]=0;w32(b+92,crc32(b,92));write_bytes(path,b,96);
  assert(p3dResumeLoad(argv[2],&loaded)&&loaded.dex_description_page==47);
  memcpy(b,valid,sizeof(b));b[80]^=1;write_bytes(path,b,96);
  assert(p3dResumeLoad(argv[2],&loaded)&&loaded.dex_description_page==47);
  write_bytes(path,valid,95);assert(p3dResumeLoad(argv[2],&loaded)&&loaded.dex_description_page==47);
  write_bytes(path,valid,97);assert(p3dResumeLoad(argv[2],&loaded)&&loaded.dex_description_page==47);
  /* Preserve strict legacy v5 tab1..4 semantics after adding tab5. */
  memcpy(b,valid,sizeof(b));b[4]=5;b[77]=b[78]=0;
  memset(b+80,0,4);w32(b+92,crc32(b,92));write_bytes(path,b,96);
  assert(p3dResumeLoad(argv[2],&loaded)&&loaded.dex_description_page==47);
  write_bytes(path,valid,4); /* torn newest B */
 }else if(!strcmp(argv[1],"fallback")){
  assert(p3dResumeLoad(argv[2],&loaded)&&loaded.dex_description_page==47);
  fixture(&s);s.dex_description_valid=0;s.dex_description_page=0;s.dex_description_checksum=0;
  assert(p3dResumeStore(argv[2],&s));
  assert(p3dResumeLoad(argv[2],&loaded)&&loaded.dex_detail_tab==5&&!loaded.dex_description_valid);
  filename(path,argv[2],'B');read_bytes(path,b);assert(b[4]==8&&b[77]==0&&b[78]==0);
  fixture(&s);s.dex_description_page=48;assert(!p3dResumeStore(argv[2],&s));
  fixture(&s);s.dex_description_valid=2;assert(!p3dResumeStore(argv[2],&s));
  fixture(&s);s.dex_description_valid=0;assert(!p3dResumeStore(argv[2],&s));
  fixture(&s);s.dex_detail_tab=1;assert(!p3dResumeStore(argv[2],&s));
  fixture(&s);s.dex_detail_tab=0;s.dex_description_valid=0;
  s.dex_description_checksum=0;assert(!p3dResumeStore(argv[2],&s));
  fixture(&s);s.dex_detail_tab=0;s.dex_description_valid=0;
  s.dex_description_page=0;assert(!p3dResumeStore(argv[2],&s));
  fixture(&s);s.home=1;assert(!p3dResumeStore(argv[2],&s));
  fixture(&s);s.page=P3D_PAGE_ALBUM;assert(!p3dResumeStore(argv[2],&s));
  fixture(&s);s.dex_learnset_valid=1;assert(!p3dResumeStore(argv[2],&s));
  fixture(&s);s.album_view_active=1;assert(!p3dResumeStore(argv[2],&s));
  fixture(&s);s.dex_description_valid=0;s.dex_description_page=0;
  assert(!p3dResumeStore(argv[2],&s)); /* inactive flag cannot retain checksum */
 }else if(!strcmp(argv[1],"close")){
  memset(&s,0,sizeof(s));s.page=P3D_PAGE_DEX;s.dex_detail_tab=1;
  assert(p3dResumeStore(argv[2],&s));
  assert(p3dResumeLoad(argv[2],&loaded)&&loaded.dex_detail_tab==1);
  assert(!loaded.dex_description_valid&&!loaded.dex_description_page&&!loaded.dex_description_checksum);
  filename(path,argv[2],'A');read_bytes(path,b);assert(b[4]==5);
  s.dex_detail_tab=0;assert(p3dResumeStore(argv[2],&s));
  assert(p3dResumeLoad(argv[2],&loaded)&&!loaded.dex_detail_tab&&!loaded.dex_description_valid);
 }else assert(!"unknown C403 phase");
 puts("C403 exact Description v8 checkpoint, corruption and legacy transitions: PASS (synthetic)");
 return 0;
}
