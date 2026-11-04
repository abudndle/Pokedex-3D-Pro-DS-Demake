#include "resume_state.h"
#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
static uint32_t crc(const unsigned char *p,unsigned n){
 uint32_t c=~0u;for(unsigned i=0;i<n;i++){c^=p[i];for(int j=0;j<8;j++)c=(c>>1)^((c&1u)?0xedb88320u:0);}return ~c;
}
static void w32(unsigned char *p,uint32_t n){for(int i=0;i<4;i++)p[i]=(unsigned char)(n>>(i*8));}
static void write_file(const char *path,const unsigned char *b,unsigned size){
 FILE *f=fopen(path,"wb");assert(f);assert(fwrite(b,1,size,f)==size);assert(!fclose(f));
}
int main(int argc,char **argv){
 assert(argc==3);char path[300];P3DResumeState restored,s;
 if(!strcmp(argv[2],"verify")){
  assert(p3dResumeLoad(argv[1],&restored));
  assert(restored.album_view_active==1&&restored.album_photo_id==9999);
  assert(restored.album_photo_checksum==0&&restored.album_photo_bytes==2097152u);
  puts("C356 exact photo ID/CRC/size across process restart: PASS");return 0;
 }
 if(!strcmp(argv[2],"recover")){
  snprintf(path,sizeof(path),"%s_resume_A.sav",argv[1]);
  unsigned char bad[97]={0};
  FILE *f=fopen(path,"rb");assert(f);assert(fread(bad,1,96,f)==96);assert(!fclose(f));
  bad[88]=1;w32(bad+92,crc(bad,92));write_file(path,bad,96);
  assert(p3dResumeLoad(argv[1],&s));
  assert(s.album_photo_id==8&&s.album_photo_checksum==0x12345678u&&s.album_photo_bytes==69);
  bad[88]=0;w32(bad+92,crc(bad,92));write_file(path,bad,95);
  assert(p3dResumeLoad(argv[1],&s)&&s.album_photo_id==8);
  write_file(path,bad,97);assert(p3dResumeLoad(argv[1],&s)&&s.album_photo_id==8);
  bad[4]=8;w32(bad+92,crc(bad,92));write_file(path,bad,96);
  assert(p3dResumeLoad(argv[1],&s)&&s.album_photo_id==8);
  s.album_view_active=0;s.album_photo_id=0;s.album_photo_checksum=0;s.album_photo_bytes=0;
  assert(p3dResumeStore(argv[1],&s));assert(p3dResumeLoad(argv[1],&restored));
  assert(!restored.album_view_active&&!restored.album_photo_id&&!restored.album_photo_bytes);
  s.page=P3D_PAGE_DEX;s.dex_detail_tab=1;
  assert(p3dResumeStore(argv[1],&s));assert(p3dResumeLoad(argv[1],&restored));
  assert(restored.dex_detail_tab==1&&!restored.album_view_active);
  s.dex_detail_tab=4;s.dex_learnset_valid=1;s.dex_learnset_page=63;s.dex_learnset_checksum=17;
  assert(p3dResumeStore(argv[1],&s));assert(p3dResumeLoad(argv[1],&restored));
  assert(restored.dex_learnset_valid&&restored.dex_learnset_page==63&&!restored.album_view_active);
  puts("C356 torn/invalid slot fallback and legacy v3/v5/v6 transitions: PASS");return 0;
 }
 assert(!strcmp(argv[2],"write"));
 unsigned char b[96]={0};memcpy(b,"P3RV",4);b[4]=7;b[8]=1;
 b[13]=P3D_PAGE_ALBUM;b[76]=1;b[78]=8;
 w32(b+80,0x12345678u);w32(b+84,69);w32(b+92,crc(b,92));
 snprintf(path,sizeof(path),"%s_resume_A.sav",argv[1]);
 write_file(path,b,96);
 assert(p3dResumeLoad(argv[1],&restored));
 assert(restored.page==P3D_PAGE_ALBUM);
 assert(restored.album_view_active&&restored.album_photo_id==8);
 assert(restored.album_photo_checksum==0x12345678u&&restored.album_photo_bytes==69);
 assert(p3dResumeStore(argv[1],&restored));
 restored.album_photo_id=9999;restored.album_photo_checksum=0;restored.album_photo_bytes=2097152u;
 assert(p3dResumeStore(argv[1],&restored));
 s=restored;s.album_photo_id=10000;assert(!p3dResumeStore(argv[1],&s));
 s=restored;s.album_photo_bytes=0;assert(!p3dResumeStore(argv[1],&s));
 s=restored;s.album_photo_bytes=2097153u;assert(!p3dResumeStore(argv[1],&s));
 s=restored;s.home=1;assert(!p3dResumeStore(argv[1],&s));
 s=restored;s.page=P3D_PAGE_DEX;assert(!p3dResumeStore(argv[1],&s));
 s=restored;s.album_view_active=0;assert(!p3dResumeStore(argv[1],&s));
 s=restored;s.album_view_active=2;assert(!p3dResumeStore(argv[1],&s));
 puts("C356 exact-photo v7 checkpoint: PASS");
 return 0;
}
