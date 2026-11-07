#include "dex_description.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
static const char fixture[]=
 "AAAAAAAAAAAAAAA BBBBBBBBBBBBBBB CCCCCCCCCCCCCCC DDDDDDDDDDDDDDD "
 "EEEEEEEEEEEEEEE FFFFFFFFFFFFFFF GGGGGGGGGGGGGGG HHHHHHHHHHHHHHH "
 "IIIIIIIIIIIIIII JJJJJJJJJJJJJJJ KKKKKKKKKKKKKKK LLLLLLLLLLLLLLL";
static void all_printable_preserved(const char *source){
 P3DDescription d;char line[29],actual[192],expected[192];unsigned at=0,wanted=0;
 assert(p3dDescriptionSet(&d,source));
 for(unsigned i=0;source[i];i++)if((unsigned char)source[i]>32&&(unsigned char)source[i]!=127)expected[wanted++]=source[i];
 for(unsigned page=0;page<p3dDescriptionPages(&d);page++){
  for(unsigned row=0;row<4;row++)if(p3dDescriptionLine(&d,row,line)){
   assert(strlen(line)<=28);
   for(unsigned i=0;line[i];i++)if(line[i]!=' ')actual[at++]=line[i];
  }
  (void)p3dDescriptionStep(&d,1);
 }
 assert(at==wanted);assert(!memcmp(actual,expected,at));
}
int main(void){
 P3DDescription d;char line[29];assert(strlen(fixture)==191);
 /* Previously the native entry displayed only clipped description fragments. */
 assert(p3dDescriptionSet(&d,fixture));assert(d.ready);
 assert(p3dDescriptionPages(&d)==3);assert(d.count==12);
 for(unsigned page=0;page<3;page++){
  for(unsigned row=0;row<4;row++){
   assert(p3dDescriptionLine(&d,row,line));assert(strlen(line)==15);
   for(unsigned i=0;i<15;i++)assert(line[i]=='A'+(int)(page*4+row));
  }
  assert(p3dDescriptionStep(&d,1)==(page<2));
 }
 assert(d.page==2);assert(!p3dDescriptionStep(&d,INT_MAX));
 assert(p3dDescriptionStep(&d,INT_MIN));assert(d.page==1);
 assert(!p3dDescriptionStep(&d,0));assert(d.page==1);
 assert(p3dDescriptionTouch(&d,1,8,144));assert(d.page==0);
 assert(p3dDescriptionTouch(&d,1,127,151));assert(d.page==0);
 assert(p3dDescriptionTouch(&d,1,128,144));assert(d.page==1);
 assert(p3dDescriptionTouch(&d,1,247,151));assert(d.page==2);
 assert(p3dDescriptionTouch(&d,1,247,151));assert(d.page==2);
 const int misses[][2]={{7,144},{248,144},{128,143},{128,152},{-1,-1},{256,192}};
 for(unsigned i=0;i<sizeof(misses)/sizeof(misses[0]);i++)assert(!p3dDescriptionTouch(&d,1,misses[i][0],misses[i][1]));
 assert(!p3dDescriptionTouch(&d,0,128,144));assert(d.page==2);
 uint32_t checksum=d.checksum;
 assert(p3dDescriptionRestore(&d,1,1,checksum));assert(d.page==1);
 assert(!p3dDescriptionRestore(&d,1,3,checksum));assert(d.page==0);
 assert(!p3dDescriptionRestore(&d,1,UINT_MAX,checksum));assert(d.page==0);
 assert(!p3dDescriptionRestore(&d,2,1,checksum));assert(d.page==0);
 assert(!p3dDescriptionRestore(&d,0,1,checksum));assert(d.page==0);
 assert(!p3dDescriptionRestore(&d,1,1,checksum^1u));assert(d.page==0);
 line[0]='X';assert(!p3dDescriptionLine(&d,4,line));assert(!line[0]);
 all_printable_preserved(fixture);
 all_printable_preserved("abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!?.");
 all_printable_preserved(" one\t two\nthree\r\x1b[31m four\177 five ");
 all_printable_preserved("high bytes: \200\377 preserved");
 assert(p3dDescriptionSet(&d,"123456789"));assert(d.checksum==0xcbf43926u);
 assert(p3dDescriptionSet(&d," alpha  beta "));checksum=d.checksum;
 assert(!strcmp(d.text,"alpha beta"));
 assert(p3dDescriptionSet(&d,"alpha beta"));assert(d.checksum!=checksum);
 d.checksum=0;assert(p3dDescriptionRestore(&d,1,0,0));
 assert(!p3dDescriptionRestore(&d,1,0,checksum));
 char raw[192];memset(raw,'A',sizeof(raw));assert(!p3dDescriptionSet(&d,raw));
 assert(!d.ready&&!d.count&&!d.page&&!d.checksum&&!d.text[0]);
 P3DDescription cleared;memset(&cleared,0,sizeof(cleared));assert(!memcmp(&d,&cleared,sizeof(d)));
 assert(!p3dDescriptionSet(&d," \t\n\177"));assert(!p3dDescriptionPages(&d));
 assert(!p3dDescriptionSet(&d,""));assert(!p3dDescriptionSet(&d,NULL));
 assert(!p3dDescriptionSet(NULL,fixture));
 assert(!p3dDescriptionLine(NULL,0,line));assert(!line[0]);
 assert(!p3dDescriptionLine(&d,0,NULL));assert(!p3dDescriptionStep(NULL,1));
 assert(!p3dDescriptionTouch(NULL,1,128,144));assert(!p3dDescriptionRestore(NULL,1,0,0));
 assert(!p3dDescriptionRestore(&d,1,0,0));assert(!p3dDescriptionPages(NULL));
 p3dDescriptionClear(NULL);assert(p3dDescriptionSet(&d,fixture));p3dDescriptionClear(&d);
 assert(!d.ready&&!d.count&&!d.page&&!d.checksum&&!d.text[0]);
 memset(&cleared,0,sizeof(cleared));assert(!memcmp(&d,&cleared,sizeof(d)));
 puts("C403 complete description wrapping, paging, touch and source-bound restore: PASS");return 0;
}
