#include "resume_state.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void path(char dest[300],const char *base,char slot){
 int n=snprintf(dest,300,"%s_resume_%c.sav",base,slot);
 assert(n>0 && n<300);
}
static uint32_t crc32(const unsigned char *b,unsigned n){
 uint32_t c=~0u;
 for(unsigned i=0;i<n;i++){c^=b[i];for(int j=0;j<8;j++)c=(c>>1)^((c&1u)?0xedb88320u:0);}
 return ~c;
}
static void put32(unsigned char *b,uint32_t x){
 for(int i=0;i<4;i++)b[i]=(unsigned char)(x>>(8*i));
}
static void write_bytes(const char *name,const unsigned char *data,unsigned length){
 FILE *f=fopen(name,"wb");assert(f);
 assert(fwrite(data,1,length,f)==length);assert(fclose(f)==0);
}
static void start(P3DResumeState *state){
 memset(state,0,sizeof(*state));
 state->home=0;state->page=P3D_PAGE_CHALLENGE;
 state->dex=25;state->selected_dex=25;
 state->challenge_mode=1;state->quiz_active=1;
 assert(p3dChallengeBegin(&state->quiz,1,0x12345678u,0));
 state->challenge_answer_total=8;
 state->challenge_correct_total=5;
}
static void verify_quiz(const P3DResumeState *state,int review){
 P3DChallenge original;
 assert(p3dChallengeBegin(&original,1,0x12345678u,0));
 if(review)assert(p3dChallengeAnswer(&original,original.correct)==1);
 assert(state->quiz_active==1 && state->page==P3D_PAGE_CHALLENGE);
 assert(memcmp(&state->quiz,&original,sizeof original)==0);
 assert(state->quiz.stage==(review?P3D_CHALLENGE_REVIEW:P3D_CHALLENGE_QUESTION));
 assert(state->challenge_answer_total==(unsigned)(review?9:8));
 assert(state->challenge_correct_total==(unsigned)(review?6:5));
}
int main(int argc,char **argv){
 P3DResumeState state,loaded,orig;
 char a[300],b[300],legacy[300],legacy_a[300];
 FILE *f;
 assert(argc==3);
 path(a,argv[2],'A');path(b,argv[2],'B');
 if(!strcmp(argv[1],"first")){
  start(&state);assert(p3dResumeStateValid(&state));
  assert(p3dResumeStore(argv[2],&state));
  unsigned char bytes[144];
  f=fopen(a,"rb");assert(f);
  assert(fread(bytes,1,144,f)==144 && fgetc(f)==EOF);
  assert(fclose(f)==0);
  assert(!memcmp(bytes,"P3RV",4) && bytes[4]==4);
 }else if(!strcmp(argv[1],"check-first")){
  assert(p3dResumeLoad(argv[2],&loaded));verify_quiz(&loaded,0);
  assert(p3dResumeApply(&loaded,p3dCapabilities(0,1,0),
            &(int){0},&(P3DMenu){0},&(int){0}));
 }else if(!strcmp(argv[1],"review")){
  assert(p3dResumeLoad(argv[2],&state));verify_quiz(&state,0);
  assert(p3dChallengeAnswer(&state.quiz,state.quiz.correct)==1);
  state.challenge_correct_total++;state.challenge_answer_total++;
  assert(p3dResumeStore(argv[2],&state));
 }else if(!strcmp(argv[1],"check-review")){
  assert(p3dResumeLoad(argv[2],&loaded));verify_quiz(&loaded,1);
  orig=loaded;
  assert(p3dChallengeAnswer(&loaded.quiz,loaded.quiz.correct)==-1);
  assert(memcmp(&loaded,&orig,sizeof loaded)==0);
  assert(p3dChallengeContinue(&loaded.quiz));
  assert(loaded.quiz.stage==P3D_CHALLENGE_QUESTION);
  assert(loaded.quiz.question==1 && loaded.quiz.score==1);
 }else if(!strcmp(argv[1],"corrupt")){
  unsigned char bytes[144];
  f=fopen(b,"rb");assert(f);
  assert(fread(bytes,1,144,f)==144 && fgetc(f)==EOF);
  assert(fclose(f)==0);
  /* Even a valid CRC must not authorize duplicated option identities. */
  bytes[86]=bytes[88];bytes[87]=bytes[89];
  put32(bytes+140,crc32(bytes,140));
  write_bytes(b,bytes,144);
 }else if(!strcmp(argv[1],"check-fallback")){
  assert(p3dResumeLoad(argv[2],&loaded));verify_quiz(&loaded,0);
  start(&state);
  state.quiz.stage=P3D_CHALLENGE_RESULTS;
  assert(!p3dResumeStore(argv[2],&state));
  start(&state);
  state.quiz.choices[0]=state.quiz.choices[1];
  assert(!p3dResumeStore(argv[2],&state));
  start(&state);
  state.quiz.asked[1]=11; /* future questions must not be fabricated */
  assert(!p3dResumeStore(argv[2],&state));
  start(&state);
  state.home=1;assert(!p3dResumeStore(argv[2],&state));
  start(&state);
  state.challenge_correct_total=9;assert(!p3dResumeStore(argv[2],&state));
  start(&state);
  state.quiz.question=10;assert(!p3dResumeStore(argv[2],&state));
  start(&state);
  state.quiz.pokemon=649;assert(!p3dResumeStore(argv[2],&state));
  start(&state);
  state.quiz_active=0;
  memset(&state.quiz,0,sizeof state.quiz);
  state.challenge_answer_total=0;state.challenge_correct_total=0;
  assert(p3dResumeStore(argv[2],&state));
  snprintf(legacy,sizeof legacy,"%s_v3",argv[2]);
  assert(p3dResumeStore(legacy,&state));
  path(legacy_a,legacy,'A');
  f=fopen(legacy_a,"rb");assert(f);
  unsigned char bytes[80];
  assert(fread(bytes,1,80,f)==80 && fgetc(f)==EOF);
  assert(fclose(f)==0 && bytes[4]==3);
  assert(p3dResumeLoad(legacy,&loaded)&&!loaded.quiz_active);
 }
 else assert(!"unknown C332 test mode");
 puts("C332 exact active Challenge P3RV v4 cross-process checkpoint: PASS");
 return 0;
}
