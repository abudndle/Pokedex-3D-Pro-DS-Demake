#include "challenge.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 P3DChallenge q;int seen[649]={0};char a[29],b[29];
 assert(p3dChallengeAvailableModes(49)==6);
 assert(p3dChallengeAvailableModes(50)==7);
 assert(!p3dChallengeBegin(&q,6,1,0));
 assert(p3dChallengeBegin(&q,0,1,0));
 for(int i=0;i<10;i++){
   assert(q.stage==P3D_CHALLENGE_QUESTION);
   assert(q.pokemon>=493&&q.pokemon<=648);
   assert(!seen[q.pokemon]);seen[q.pokemon]=1;
   assert(q.choices[q.correct]==q.pokemon);
   for(int j=0;j<4;j++){assert(q.choices[j]>=493&&q.choices[j]<=648);for(int k=0;k<j;k++)assert(q.choices[j]!=q.choices[k]);}
   assert(p3dChallengeAnswer(&q,q.correct)==1);
   assert(q.stage==P3D_CHALLENGE_REVIEW && q.question==i);
   assert(p3dChallengeContinue(&q));
 }
 assert(q.stage==P3D_CHALLENGE_RESULTS&&q.score==10);
 p3dChallengeClue("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",0,a,b);
 assert(a[28]==0);assert(b[8]==0);
 puts("Challenge quiz rules: PASS");return 0;
}
