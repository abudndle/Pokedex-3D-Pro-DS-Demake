#include "resume_state.h"
#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
static void put16(unsigned char *p,unsigned n){
 p[0]=(unsigned char)n;p[1]=(unsigned char)(n>>8);
}
static void put32(unsigned char *p,uint32_t n){
 put16(p,n);put16(p+2,n>>16);
}
static uint32_t crc(const unsigned char *p,unsigned n){
 uint32_t v=0xffffffffu;
 for(unsigned i=0;i<n;i++){
   v^=p[i];
   for(int j=0;j<8;j++)v=(v>>1)^((v&1u)?0xedb88320u:0u);
 }
 return v^0xffffffffu;
}
static void write_bytes(const char *path,const unsigned char *b,size_t n){
 FILE *f=fopen(path,"wb");assert(f);
 assert(fwrite(b,1,n,f)==n);assert(fclose(f)==0);
}
int main(int argc,char **argv){
 P3DResumeState state={0},out;
 unsigned char file[80]={0},legacy[48]={0};
 char path[300],base2[300],legacy_name[320];
 FILE *f;
 assert(argc==2);
 state.page=P3D_PAGE_SEARCH;state.home=0;state.dex=487;
 state.selected_dex=487;state.highlight=5;state.search_letter='Q';
 memcpy(state.search_query,"QUAGSIRE",9);
 state.challenge_mode=5;state.type_attack=12;
 state.type_defend=7;state.type_defend2_plus_one=17;
 state.favorites_selected=2;state.search_scope=1;
 assert(p3dResumeStateValid(&state));
 assert(p3dResumeStore(argv[1],&state));
 assert(p3dResumeLoad(argv[1],&out));
 assert(memcmp(&state,&out,sizeof(state))==0);
 assert(snprintf(path,sizeof(path),"%s_resume_A.sav",argv[1])>0);
 f=fopen(path,"rb");assert(f);
 assert(fread(file,1,sizeof(file),f)==sizeof(file));
 assert(fgetc(f)==EOF);assert(fclose(f)==0);
 assert(!memcmp(file,"P3RV",4)&&file[4]==3);
 assert(!memcmp(file+44,"QUAGSIRE",8)&&file[57]=='Q');
 assert(file[58]==5&&file[59]==12&&file[60]==7&&file[61]==17);
 assert(crc(file,76)==(uint32_t)(file[76]|file[77]<<8|
                      file[78]<<16|file[79]<<24));
 /* Correct CRC cannot make structurally invalid query/source state valid. */
 file[44]='x';put32(file+76,crc(file,76));
 write_bytes(path,file,sizeof(file));
 assert(!p3dResumeLoad(argv[1],&out));
 file[44]='Q';file[63]=1;put32(file+76,crc(file,76));
 write_bytes(path,file,sizeof(file));
 assert(!p3dResumeLoad(argv[1],&out));
 file[63]=0;file[58]=7;put32(file+76,crc(file,76));
 write_bytes(path,file,sizeof(file));
 assert(!p3dResumeLoad(argv[1],&out));

 /* Native validation prevents invalid fields from being written. */
 state.challenge_mode=7;assert(!p3dResumeStore(argv[1],&state));
 state.challenge_mode=5;state.type_attack=17;
 assert(!p3dResumeStore(argv[1],&state));
 state.type_attack=12;state.type_defend2_plus_one=18;
 assert(!p3dResumeStore(argv[1],&state));
 state.type_defend2_plus_one=17;
 state.search_query[8]='b';assert(!p3dResumeStore(argv[1],&state));
 state.search_query[8]=0;
 memcpy(state.search_query,"ABCDEFGHIJKLM",13);
 assert(!p3dResumeStore(argv[1],&state));
 memset(state.search_query,0,13);
 memcpy(state.search_query,"QUAGSIRE",8);
 assert(p3dResumeStateValid(&state));

 /* A real C121 v2 48-byte checkpoint must load with safe v3 defaults
  * and upgrade in the alternate slot; the legacy record is preserved. */
 assert(snprintf(base2,sizeof(base2),"%s_v2",argv[1])>0);
 assert(snprintf(legacy_name,sizeof(legacy_name),"%s_resume_A.sav",base2)>0);
 memcpy(legacy,"P3RV",4);legacy[4]=2;
 put32(legacy+8,100);
 legacy[12]=0;legacy[13]=P3D_PAGE_TYPES;
 legacy[14]=2;legacy[15]=1;
 put16(legacy+16,34);put16(legacy+18,120);
 put16(legacy+20,34);put16(legacy+22,2);
 put16(legacy+24,1);
 legacy[26]=2;legacy[29]=3;legacy[30]=2;
 put32(legacy+44,crc(legacy,44));
 write_bytes(legacy_name,legacy,sizeof(legacy));
 assert(p3dResumeLoad(base2,&out));
 assert(out.page==P3D_PAGE_TYPES&&out.selected_form==1);
 assert(out.search_region==3 && out.search_scope==2);
 assert(out.challenge_mode==0 && out.type_attack==0);
 assert(out.search_query[0]==0 && out.search_letter==0);
 out.challenge_mode=3;out.type_attack=7;out.type_defend=8;
 out.type_defend2_plus_one=3;
 assert(p3dResumeStore(base2,&out));
 assert(p3dResumeLoad(base2,&out));
 assert(out.challenge_mode==3 && out.type_attack==7);
 assert(snprintf(path,sizeof(path),"%s_resume_B.sav",base2)>0);
 f=fopen(path,"rb");assert(f);
 assert(fread(file,1,80,f)==80);assert(fclose(f)==0);
 assert(file[4]==3);
 /* Corrupt newest, even with coherent CRC: previous v2 must recover. */
 file[62]=7;put32(file+76,crc(file,76));
 write_bytes(path,file,80);
 assert(p3dResumeLoad(base2,&out));
 assert(out.page==P3D_PAGE_TYPES&&out.selected_form==1);
 assert(out.challenge_mode==0 && out.type_attack==0);
 puts("C122: Search/Challenge/Type/Favorite checkpoint and v2/v3 migration: PASS");
 return 0;
}
