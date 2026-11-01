#include "resume_state.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint32_t crc(const unsigned char *b,unsigned count){
 uint32_t c=0xffffffffu;
 for(unsigned i=0;i<count;i++){c^=b[i];for(unsigned k=0;k<8;k++)c=(c>>1)^((c&1u)?0xedb88320u:0);}
 return c^0xffffffffu;
}
static void u32(unsigned char *p,uint32_t v){
 for(unsigned i=0;i<4;i++)p[i]=(unsigned char)(v>>(8*i));
}
static void path(char *out,size_t n,const char *base,char slot){
 int len=snprintf(out,n,"%s_resume_%c.sav",base,slot);
 assert(len>0&&(size_t)len<n);
}
static void read80(const char *name,unsigned char b[80]){
 FILE *f=fopen(name,"rb");assert(f);
 assert(fread(b,1,80,f)==80);assert(fgetc(f)==EOF);assert(fclose(f)==0);
}
static void write_n(const char *name,const unsigned char *b,size_t n){
 FILE *f=fopen(name,"wb");assert(f);
 assert(fwrite(b,1,n,f)==n);assert(fclose(f)==0);
}
static void expect(const char *base,unsigned species){
 P3DResumeState state;assert(p3dResumeLoad(base,&state));
 assert(state.dex==species);
}
int main(int argc,char **argv){
 P3DResumeState s={0},loaded;
 unsigned char a[80],b[80],scratch[80];
 char pa[512],pb[512];
 assert(argc==2);
 path(pa,sizeof(pa),argv[1],'A');path(pb,sizeof(pb),argv[1],'B');
 s.home=0;s.page=P3D_PAGE_DEX;s.dex=25;s.selected_dex=25;
 assert(p3dResumeStore(argv[1],&s));
 s.dex=150;s.selected_dex=150;
 assert(p3dResumeStore(argv[1],&s));
 read80(pa,a);read80(pb,b);expect(argv[1],150);
 /* Interrupted newest-slot write: zero bytes or partial record -> backup. */
 write_n(pb,b,0);expect(argv[1],25);
 write_n(pb,b,31);expect(argv[1],25);
 write_n(pb,b,79);expect(argv[1],25);
 /* Oversized record with valid prefix must be rejected. */
 write_n(pb,b,80);{FILE *f=fopen(pb,"ab");assert(f);
 assert(fputc(0,f)!=EOF);assert(fclose(f)==0);}expect(argv[1],25);
 /* Newest payload CRC corruption -> valid older snapshot. */
 memcpy(scratch,b,80);scratch[16]^=1;
 write_n(pb,scratch,80);expect(argv[1],25);
 /* Corrupt reserved field even with an otherwise correct CRC. */
 memcpy(scratch,b,80);scratch[63]=1;u32(scratch+76,crc(scratch,76));
 write_n(pb,scratch,80);expect(argv[1],25);
 /* A restored write must replace the bad slot, retaining the valid backup. */
 s.dex=386;s.selected_dex=386;
 assert(p3dResumeStore(argv[1],&s));expect(argv[1],386);
 read80(pb,scratch);assert(scratch[4]==3);
 /* Wrapped sequence: A=UINT32_MAX and B=0; B is newer. */
 memcpy(a,scratch,80);memcpy(b,scratch,80);
 u32(a+8,UINT32_MAX);u32(a+76,crc(a,76));a[16]=25;a[17]=0;
 u32(a+76,crc(a,76));
 u32(b+8,0);u32(b+76,crc(b,76));
 write_n(pa,a,80);write_n(pb,b,80);expect(argv[1],386);
 /* Next commit after rollover must remain newest, even after another load. */
 s.dex=487;s.selected_dex=487;
 assert(p3dResumeStore(argv[1],&s));expect(argv[1],487);
 assert(p3dResumeLoad(argv[1],&loaded)&&loaded.dex==487);
 /* Both slots damaged must fail rather than silently select corrupt data. */
 read80(pa,a);read80(pb,b);a[0]=0;b[0]=0;
 write_n(pa,a,80);write_n(pb,b,80);
 assert(!p3dResumeLoad(argv[1],&loaded));
 puts("C123: interrupted writes, CRC/reserved validation and sequence rollover: PASS");
 return 0;
}
