#include "challenge_text.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
 P3DChallenge q,before;
 P3DChallengeText text;
 assert(argc==3);
 assert(!p3dChallengeBegin(&q,P3D_CHALLENGE_TEXT_MODE,123,49));
 assert(p3dChallengeBegin(&q,P3D_CHALLENGE_TEXT_MODE,123,50));
 assert(!p3dChallengeTextLoad(&text,&q));
 before=q;
 assert(p3dChallengeTextAnswer(&text,&q,q.correct)==-1);
 assert(!memcmp(&q,&before,sizeof q));
 assert(p3dDexTextInit(argv[1]));
 for(int question=0;question<P3D_CHALLENGE_QUESTIONS;question++){
  char first[29],second[29];
  assert(p3dChallengeTextLoad(&text,&q));
  assert(text.ready && text.clue.index==q.pokemon && text.clue.page==0);
  assert(text.clue.pages==4);
  for(int i=0;i<4;i++){
   char expected[32];snprintf(expected,sizeof expected,"Synthetic %03d",q.choices[i]);
   assert(!strcmp(text.names[i],expected));
  }
  p3dDexInfoLines(&text.clue,first,second);
  assert(strlen(first)==28 && strlen(second)==28);
  assert(p3dDexInfoStep(&text.clue,1));
  /* A stale question or changed options cannot use cached original text. */
  before=q;q.pokemon=(q.pokemon+1)%649;
  assert(p3dChallengeTextAnswer(&text,&q,q.correct)==-1);q=before;
  q.choices[0]=(q.choices[0]+1)%649;
  assert(p3dChallengeTextAnswer(&text,&q,q.correct)==-1);q=before;
  assert(p3dChallengeTextAnswer(&text,&q,-1)==-1);
  assert(text.ready);
  int choice=question%2?(q.correct+1)%4:q.correct;
  assert(p3dChallengeTextAnswer(&text,&q,choice)==(question%2==0));
  assert(!text.ready);
  before=q;
  assert(p3dChallengeTextAnswer(&text,&q,choice)==-1);
  assert(!memcmp(&q,&before,sizeof q));
 }
 assert(q.stage==P3D_CHALLENGE_RESULTS && q.score==5);
 assert(!p3dChallengeTextLoad(&text,&q));
 assert(p3dChallengeBegin(&q,P3D_CHALLENGE_TEXT_MODE,456,50));
 assert(p3dChallengeTextLoad(&text,&q));
 assert(p3dDexTextInit(argv[2]));
 assert(!p3dChallengeTextLoad(&text,&q));
 assert(!text.ready && !text.names[0][0] && !text.clue.text.description[0]);
 before=q;
 assert(p3dChallengeTextAnswer(&text,&q,q.correct)==-1);
 assert(!memcmp(&q,&before,sizeof q));
 assert(!p3dChallengeTextLoad(NULL,&q));
 assert(!p3dChallengeTextLoad(&text,NULL));
 assert(p3dChallengeTextAnswer(NULL,&q,0)==-1);
 assert(p3dChallengeTextAnswer(&text,NULL,0)==-1);
 assert(p3dChallengeBegin(&q,0,1,0));
 assert(!p3dChallengeTextLoad(&text,&q));
 p3dDexTextClose();
 puts("Text Challenge original clue/options, paging and scoring prerequisites: PASS");
}
