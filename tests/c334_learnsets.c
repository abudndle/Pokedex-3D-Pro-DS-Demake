#include "species_learnset.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
static uint32_t crc(const unsigned char *p,unsigned n,uint32_t c){
 for(unsigned i=0;i<n;i++){c^=p[i];for(int k=0;k<8;k++)c=(c>>1)^((c&1u)?0xedb88320u:0);}return c;
}
static void w16(unsigned char *p,unsigned n){p[0]=(unsigned char)n;p[1]=(unsigned char)(n>>8);}
static void seal(unsigned char *b,unsigned count){
 uint32_t c=~crc(b+16,count*6u,crc(b,12,~0u));
 for(int i=0;i<4;i++)b[12+i]=(unsigned char)(c>>(8*i));
}
static unsigned fixture(unsigned char *b,unsigned count){
 memset(b,0,1553);memcpy(b,"P3SL",4);b[4]=b[5]=1;
 w16(b+6,25);w16(b+8,2);w16(b+10,count);
 for(unsigned i=0;i<count;i++){w16(b+16+i*6,i);b[18+i*6]=1;b[19+i*6]=(unsigned char)(1+i%100);}
 seal(b,count);return 16+count*6;
}
static void put(const char *path,const unsigned char *b,unsigned size){
 FILE *f=fopen(path,"wb");assert(f);assert(fwrite(b,1,size,f)==size);assert(!fclose(f));
}
int main(int argc,char **argv){
 assert(argc==2);const char *path=argv[1];
 unsigned char b[1553],original[1553];P3DLearnset s;
 unsigned size=fixture(b,9);put(path,b,size);
 assert(p3dLearnsetLoad(path,25,2,&s));
 assert(s.ready&&s.count==9&&s.species==25&&s.form==2);
 assert(s.rows[8].move==8&&s.rows[8].level==9);
 assert(p3dLearnsetPage(&s,0,-1)==0);
 assert(p3dLearnsetPage(&s,0,1)==1);
 assert(p3dLearnsetPage(&s,1,1)==2);
 assert(p3dLearnsetPage(&s,2,1)==2);
 assert(p3dLearnsetPage(&s,2,-1)==1);
 assert(p3dLearnsetPage(&s,999,0)==2);
 uint32_t fingerprint=s.checksum;
 assert(p3dLearnsetRestorePage(&s,2,fingerprint)==2);
 assert(p3dLearnsetRestorePage(&s,3,fingerprint)==0);
 assert(p3dLearnsetRestorePage(&s,2,fingerprint^1u)==0);
 assert(!p3dLearnsetLoad(path,24,2,&s)&&!s.ready&&!s.count);
 assert(!p3dLearnsetLoad(path,25,0,&s)&&!s.ready);
 memcpy(original,b,sizeof(b));
 #define INVALID(change) do{memcpy(b,original,sizeof(b));change;seal(b,9);put(path,b,size);assert(!p3dLearnsetLoad(path,25,2,&s)&&!s.ready&&!s.count);}while(0)
 INVALID(b[4]=2);INVALID(b[5]=0);INVALID(b[5]=3);
 INVALID(w16(b+10,257));INVALID(w16(b+16,559));
 INVALID(b[18]=0);INVALID(b[18]=6);INVALID(b[19]=0);INVALID(b[19]=101);
 INVALID(b[18]=2); /* non-level method with a nonzero level */
 INVALID(b[20]=1); /* reserved */
 INVALID(memcpy(b+22,b+16,6)); /* exact duplicate */
 memcpy(b,original,sizeof(b));b[19]^=1;put(path,b,size);
 assert(!p3dLearnsetLoad(path,25,2,&s));
 memcpy(b,original,sizeof(b));put(path,b,size-1);
 assert(!p3dLearnsetLoad(path,25,2,&s));put(path,b,size+1);
 assert(!p3dLearnsetLoad(path,25,2,&s));
 size=fixture(b,256);put(path,b,size);
 assert(p3dLearnsetLoad(path,25,2,&s)&&s.count==256);
 assert(p3dLearnsetPage(&s,63,1)==63&&s.rows[255].move==255);
 put(path,b,size+1);assert(!p3dLearnsetLoad(path,25,2,&s));
 size=fixture(b,0);put(path,b,size);
 assert(p3dLearnsetLoad(path,25,2,&s)&&s.ready&&!s.count);
 assert(!p3dLearnsetPage(&s,999,1));
 size=fixture(b,5);
 for(unsigned i=0;i<5;i++){b[18+i*6]=(unsigned char)(i+1);b[19+i*6]=i?0:1;}
 /* Same move via a different source method is not a duplicate. */
 w16(b+22,0);seal(b,5);put(path,b,size);
 assert(p3dLearnsetLoad(path,25,2,&s));
 assert(!strcmp(p3dLearnsetMethod(s.rows[4].method),"EVOLVE"));
 assert(!p3dLearnsetLoad("missing-learnset.p3sl",25,2,&s)&&!s.ready);
 assert(!p3dLearnsetLoad(path,-1,2,&s));assert(!p3dLearnsetLoad(path,25,1000,&s));
 puts("C334 bounded P3SL, corruption, identity, complete rows and pagination: PASS (synthetic)");
 return 0;
}
