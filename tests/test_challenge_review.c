#include "challenge.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void quiz_run(int mode){
 P3DChallenge q;
 int first,last,seen[649]={0};
 assert(p3dChallengeRange(mode,&first,&last));
 assert(p3dChallengeBegin(&q,mode,0,50));
 assert(!p3dChallengeContinue(&q));
 for(int i=0;i<P3D_CHALLENGE_QUESTIONS;i++){
  P3DChallenge before;
  int choices[P3D_CHALLENGE_OPTIONS];
  int pokemon=q.pokemon,correct=q.correct,score=q.score;
  int choice=(i%2)?(correct+1)%P3D_CHALLENGE_OPTIONS:correct;
  assert(q.stage==P3D_CHALLENGE_QUESTION && q.question==i);
  assert(pokemon>=first && pokemon<=last && !seen[pokemon]);
  seen[pokemon]=1;
  memcpy(choices,q.choices,sizeof choices);
  before=q;
  assert(p3dChallengeAnswer(&q,-1)==-1);
  assert(p3dChallengeAnswer(&q,P3D_CHALLENGE_OPTIONS)==-1);
  assert(!memcmp(&before,&q,sizeof q));
  assert(p3dChallengeAnswer(&q,choice)==(i%2==0));
  assert(q.stage==P3D_CHALLENGE_REVIEW && q.question==i);
  assert(q.selected==choice && q.correct==correct && q.pokemon==pokemon);
  assert(!memcmp(choices,q.choices,sizeof choices));
  assert(q.score==score+(i%2==0));
  before=q;
  /* Repeated submissions, including a corrected answer, cannot rescore. */
  assert(p3dChallengeAnswer(&q,correct)==-1);
  assert(p3dChallengeAnswer(&q,choice)==-1);
  assert(!memcmp(&before,&q,sizeof q));
  assert(p3dChallengeContinue(&q));
  assert(q.question==i+1);
  if(i+1<P3D_CHALLENGE_QUESTIONS){
   assert(q.stage==P3D_CHALLENGE_QUESTION && q.selected==0);
   assert(!p3dChallengeContinue(&q));
  }
 }
 assert(q.stage==P3D_CHALLENGE_RESULTS && q.score==5);
 assert(!p3dChallengeContinue(&q));
 assert(p3dChallengeAnswer(&q,0)==-1);
 assert(p3dChallengeBegin(&q,mode,123,50));
 assert(q.score==0 && q.question==0 && q.mode_cursor==mode);
 p3dChallengeReset(&q);
 assert(q.stage==P3D_CHALLENGE_PICKER && !p3dChallengeContinue(&q));
 assert(p3dChallengeAnswer(&q,0)==-1);
}
int main(void){
 for(int mode=0;mode<P3D_CHALLENGE_MODES;mode++)quiz_run(mode);
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
 assert(p3dChallengeTouchContinue(8,144));
 assert(p3dChallengeTouchContinue(247,167));
 assert(!p3dChallengeTouchContinue(7,144));
 assert(!p3dChallengeTouchContinue(248,144));
 assert(!p3dChallengeTouchContinue(8,143));
 assert(!p3dChallengeTouchContinue(8,168));
 assert(!p3dChallengeTouchContinue(-1,-1));
 puts("Challenge answer review, exactly-once scoring and touch bounds: PASS");
}
