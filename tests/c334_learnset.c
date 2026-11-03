#include "learnset.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint32_t crc(const unsigned char *p,unsigned n){
 uint32_t c=~0u;
 for(unsigned i=0;i<n;i++){c^=p[i];for(int j=0;j<8;j++)c=(c>>1)^((c&1u)?0xedb88320u:0);}
 return ~c;
}
static void u16(unsigned char *p,unsigned n){p[0]=(unsigned char)n;p[1]=(unsigned char)(n>>8);}
static void u32(unsigned char *p,uint32_t n){u16(p,(unsigned)n);u16(p+2,(unsigned)(n>>16));}
static void write_file(const char *path,const unsigned char *b,size_t n){
 FILE *f=fopen(path,"wb");assert(f);assert(fwrite(b,1,n,f)==n);assert(fclose(f)==0);
}
static unsigned fixture(unsigned char b[1044],unsigned count){
 unsigned size=16+count*4+4;
 memset(b,0,1044);memcpy(b,"P3SL",4);b[4]=1;
 u16(b+6,25);u16(b+8,2);u16(b+10,count);
 for(unsigned i=0;i<count;i++){
   u16(b+16+4*i,(i*11u)%559u);
   b[18+4*i]=(unsigned char)(1u+(i%5u));
   b[19+4*i]=(unsigned char)(i%5u==0?1+(i%100u):0);
 }
 u32(b+size-4,crc(b,size-4));return size;
}
int main(int argc,char **argv){
 unsigned char b[1044];P3DLearnset l;char path[80];
 assert(argc==2);
 assert(p3dLearnsetPath(path,25,2)&&!strcmp(path,"nitro:/learnsets/s025-f002.p3sl"));
 assert(!p3dLearnsetPath(path,649,0)&&!p3dLearnsetPath(path,25,1000));
 unsigned len=fixture(b,9);
 write_file(argv[1],b,len);
 assert(p3dLearnsetLoad(argv[1],25,2,&l));
 assert(l.ready&&l.species==25&&l.form==2&&l.count==9);
 assert(l.entries[0].method==1&&l.entries[0].level==1);
 assert(l.entries[1].method==2&&l.entries[1].level==0);
 assert(p3dLearnsetPageCount(&l)==3);
 assert(p3dLearnsetStep(&l,0,-1)==0);
 assert(p3dLearnsetStep(&l,0,1)==1);
 assert(p3dLearnsetStep(&l,1,1)==2);
 assert(p3dLearnsetStep(&l,2,1)==2);
 assert(p3dLearnsetStep(&l,2,-1)==1);
 assert(!strcmp(p3dLearnsetMethodName(1),"Level"));
 assert(!strcmp(p3dLearnsetMethodName(3),"Egg"));
 assert(!p3dLearnsetLoad(argv[1],25,0,&l)&&!l.ready);
 assert(!p3dLearnsetLoad("missing-c334-source.p3sl",25,2,&l)&&!l.ready);
 assert(!p3dLearnsetLoad(argv[1],-1,2,&l)&&!l.ready);
 write_file(argv[1],b,len-1);assert(!p3dLearnsetLoad(argv[1],25,2,&l)&&!l.ready);
 b[len]=0;write_file(argv[1],b,len+1);assert(!p3dLearnsetLoad(argv[1],25,2,&l));
 #define BAD(change) do{fixture(b,9);change;u32(b+len-4,crc(b,len-4));write_file(argv[1],b,len);assert(!p3dLearnsetLoad(argv[1],25,2,&l)&&!l.ready);}while(0)
 BAD(b[4]=2);
 BAD(b[5]=1);
 BAD(b[12]=1);
 BAD(u16(b+6,24));
 BAD(u16(b+8,3));
 BAD(u16(b+10,257)); /* false count, CRC still valid at old end */
 BAD(u16(b+16,559)); /* wrong Move Dex index */
 BAD(b[18]=0); /* unknown method */
 BAD(b[18]=6);
 BAD(b[19]=0); /* level-up with no level */
 BAD(b[19]=101);
 BAD(b[23]=3); /* non-level method with a level */
 BAD(memcpy(b+20,b+16,4)); /* exact duplicate 4-byte row */
 fixture(b,9);b[16]^=1;write_file(argv[1],b,len);
 assert(!p3dLearnsetLoad(argv[1],25,2,&l)); /* stale CRC */
 len=fixture(b,0);write_file(argv[1],b,len);
 assert(p3dLearnsetLoad(argv[1],25,2,&l)&&l.ready&&l.count==0);
 assert(!p3dLearnsetPageCount(&l) && !p3dLearnsetStep(&l,0,1));
 len=fixture(b,256);write_file(argv[1],b,len);
 assert(p3dLearnsetLoad(argv[1],25,2,&l)&&l.count==256);
 assert(p3dLearnsetPageCount(&l)==64);
 assert(p3dLearnsetStep(&l,62,1)==63&&p3dLearnsetStep(&l,63,1)==63);
 len=fixture(b,256);
 b[10]=0;b[11]=1; /* 256 already */
 (void)len;
 puts("C334 P3SL original-source optional learnset transport and 64-page navigation: PASS (synthetic data)");
 return 0;
}
