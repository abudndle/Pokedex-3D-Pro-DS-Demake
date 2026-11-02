#include "challenge.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* No original Nintendo input data; all seven existing synthetic modes. */
static void run_mode(int mode){
 P3DChallenge q;
 int first,last,seen[649]={0};
 assert(p3dChallengeRange(mode,&first,&last));
 assert(p3dChallengeBegin(&q,mode,0,50));
 assert(q.stage==P3D_CHALLENGE_QUESTION && q.mode_cursor==mode);
 assert(!p3dChallengeContinue(&q));
 for(int n=0;n<P3D_CHALLENGE_QUESTIONS;n++){
  P3DChallenge before;
  int pokemon=q.pokemon,correct=q.correct,score=q.score;
  int chosen=(n%2)?(correct+1)%P3D_CHALLENGE_OPTIONS:correct;
  int choices[P3D_CHALLENGE_OPTIONS];
  assert(q.stage==P3D_CHALLENGE_QUESTION && q.question==n);
  assert(pokemon>=first && pokemon<=last && !seen[pokemon]);
  seen[pokemon]=1;
  memcpy(choices,q.choices,sizeof choices);
  before=q;
  assert(p3dChallengeAnswer(&q,-1)==-1);
  assert(p3dChallengeAnswer(&q,P3D_CHALLENGE_OPTIONS)==-1);
  assert(memcmp(&q,&before,sizeof q)==0);
  assert(p3dChallengeAnswer(&q,chosen)==(n%2==0));
  assert(q.stage==P3D_CHALLENGE_REVIEW && q.question==n);
  assert(q.selected==chosen && q.pokemon==pokemon && q.correct==correct);
  assert(memcmp(choices,q.choices,sizeof choices)==0);
  assert(q.score==score+(n%2==0));
  before=q;
  assert(p3dChallengeAnswer(&q,correct)==-1);
  assert(p3dChallengeAnswer(&q,chosen)==-1);
  assert(memcmp(&q,&before,sizeof q)==0);
  assert(p3dChallengeContinue(&q));
  assert(q.question==n+1);
  if(n+1<P3D_CHALLENGE_QUESTIONS){
   assert(q.stage==P3D_CHALLENGE_QUESTION && q.selected==0);
   assert(!p3dChallengeContinue(&q));
  }else assert(q.stage==P3D_CHALLENGE_RESULTS);
 }
 assert(q.score==P3D_CHALLENGE_QUESTIONS/2);
 assert(!p3dChallengeContinue(&q));
 assert(p3dChallengeAnswer(&q,0)==-1);
 assert(p3dChallengeBegin(&q,mode,123,50));
 assert(q.mode_cursor==mode && q.score==0 && q.question==0);
 p3dChallengeReset(&q);
 assert(q.stage==P3D_CHALLENGE_PICKER);
 assert(!p3dChallengeContinue(&q));
 assert(p3dChallengeAnswer(&q,0)==-1);
}
int main(void){
 for(int mode=0;mode<P3D_CHALLENGE_MODES;mode++)run_mode(mode);
 assert(p3dChallengeAnswer(NULL,0)==-1);
 assert(!p3dChallengeContinue(NULL));
 for(int choice=0;choice<P3D_CHALLENGE_OPTIONS;choice++){
  int y=80+choice*24;
  assert(p3dChallengeTouchChoice(8,y)==choice);
  assert(p3dChallengeTouchChoice(247,y+23)==choice);
 }
 assert(p3dChallengeTouchChoice(7,80)==-1);
 assert(p3dChallengeTouchChoice(248,80)==-1);
 assert(p3dChallengeTouchChoice(8,79)==-1);
 assert(p3dChallengeTouchChoice(8,176)==-1);
 assert(p3dChallengeTouchChoice(-1,-1)==-1);
 assert(p3dChallengeTouchChoice(256,192)==-1);
 assert(p3dChallengeTouchContinue(8,144));
 assert(p3dChallengeTouchContinue(247,167));
 assert(!p3dChallengeTouchContinue(7,144));
 assert(!p3dChallengeTouchContinue(248,144));
 assert(!p3dChallengeTouchContinue(8,143));
 assert(!p3dChallengeTouchContinue(8,168));
 assert(!p3dChallengeTouchContinue(-1,-1));
 puts("C232 Challenge answer review, single scoring, and exact touch bounds: PASS");
 return 0;
}
