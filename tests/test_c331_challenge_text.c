#include "challenge_text.h"
#include "dex_text.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void run_complete_quiz(void){
 P3DChallenge quiz,before;
 P3DChallengeText text;
 int seen[649]={0};
 assert(p3dChallengeBegin(&quiz,P3D_CHALLENGE_TEXT_MODE,123,50));
 assert(quiz.stage==P3D_CHALLENGE_QUESTION);
 for(int n=0;n<P3D_CHALLENGE_QUESTIONS;n++){
  char line1[29],line2[29],expected[32];
  assert(quiz.question==n && quiz.clue_page==0);
  assert(p3dChallengeTextLoad(&text,&quiz));
  assert(text.ready && text.question==n && text.pokemon==quiz.pokemon);
  assert(!seen[quiz.pokemon]);seen[quiz.pokemon]=1;
  assert(text.pages==4 && text.correct==quiz.correct);
  assert(text.choices[quiz.correct]==quiz.pokemon);
  for(int i=0;i<P3D_CHALLENGE_OPTIONS;i++){
   snprintf(expected,sizeof expected,"Synthetic %03d",quiz.choices[i]);
   assert(!strcmp(text.names[i],expected));
  }
  p3dChallengeClue(text.clue,0,line1,line2);
  assert(strlen(line1)==28 && strlen(line2)==28);
  for(int page=1;page<4;page++){
   assert(p3dChallengeTextPageStep(&quiz,1));
   assert(quiz.clue_page==page);
  }
  assert(!p3dChallengeTextPageStep(&quiz,1));
  assert(p3dChallengeTextPageStep(&quiz,-1));
  assert(quiz.clue_page==2);
  assert(!p3dChallengeTextPageStep(&quiz,0));
  before=quiz;
  quiz.pokemon=(quiz.pokemon+1)%649;
  assert(p3dChallengeTextAnswer(&quiz,quiz.correct)==-1);
  quiz=before;
  quiz.choices[(quiz.correct+1)%4]=quiz.pokemon;
  assert(p3dChallengeTextAnswer(&quiz,quiz.correct)==-1);
  quiz=before;
  assert(p3dChallengeTextAnswer(&quiz,-1)==-1);
  assert(!memcmp(&quiz,&before,sizeof quiz));
  int choice=(n%2==0)?quiz.correct:(quiz.correct+1)%4;
  assert(p3dChallengeTextAnswer(&quiz,choice)==(n%2==0));
  assert(quiz.stage==P3D_CHALLENGE_REVIEW);
  assert(p3dChallengeTextLoad(&text,&quiz));
  before=quiz;
  assert(p3dChallengeTextAnswer(&quiz,quiz.correct)==-1);
  assert(!memcmp(&quiz,&before,sizeof quiz));
  assert(!p3dChallengeTextPageStep(&quiz,1));
  assert(p3dChallengeTextContinue(&quiz));
 }
 assert(quiz.stage==P3D_CHALLENGE_RESULTS && quiz.score==5);
 assert(!p3dChallengeTextLoad(&text,&quiz));
 assert(p3dChallengeTextAnswer(&quiz,0)==-1);
}
int main(int argc,char **argv){
 P3DChallenge quiz,before;
 P3DChallengeText text;
 assert(argc==4);
 assert(p3dChallengeBegin(&quiz,P3D_CHALLENGE_TEXT_MODE,123,50));
 /* Without an original catalog, a player cannot submit a fake text answer. */
 before=quiz;
 assert(!p3dChallengeTextLoad(&text,&quiz));
 assert(p3dChallengeTextAnswer(&quiz,quiz.correct)==-1);
 assert(!memcmp(&quiz,&before,sizeof quiz));
 assert(p3dDexTextInit(argv[1]));
 run_complete_quiz();
 assert(p3dChallengeBegin(&quiz,P3D_CHALLENGE_TEXT_MODE,124,50));
 assert(p3dChallengeTextLoad(&text,&quiz));
 assert(!p3dChallengeTextLoad(NULL,&quiz));
 assert(!p3dChallengeTextLoad(&text,NULL));
 assert(!text.ready && !text.clue[0]);
 assert(p3dChallengeTextAnswer(NULL,0)==-1);
 assert(!p3dChallengeTextPageStep(NULL,1));
 /* A missing catalog during REVIEW cannot commit the next question. */
 assert(p3dChallengeBegin(&quiz,P3D_CHALLENGE_TEXT_MODE,124,50));
 assert(p3dChallengeTextAnswer(&quiz,quiz.correct)==1);
 before=quiz;
 p3dDexTextClose();
 assert(!p3dChallengeTextContinue(&quiz));
 assert(!memcmp(&quiz,&before,sizeof quiz));
 assert(p3dDexTextInit(argv[1]));
 assert(p3dChallengeTextContinue(&quiz));
 assert(quiz.stage==P3D_CHALLENGE_QUESTION && quiz.question==1);
 assert(p3dDexTextInit(argv[2]));
 before=quiz;
 memset(&text,0x6f,sizeof text);
 assert(!p3dChallengeTextLoad(&text,&quiz));
 assert(!text.ready && !text.names[0][0] && !text.clue[0]);
 assert(p3dChallengeTextAnswer(&quiz,quiz.correct)==-1);
 assert(!memcmp(&quiz,&before,sizeof quiz));
 assert(p3dDexTextInit(argv[3]));
 assert(!p3dChallengeTextLoad(&text,&quiz));
 assert(p3dChallengeTextAnswer(&quiz,quiz.correct)==-1);
 assert(!memcmp(&quiz,&before,sizeof quiz));
 assert(p3dChallengeBegin(&quiz,0,1,0));
 assert(!p3dChallengeTextLoad(&text,&quiz));
 p3dDexTextClose();
 puts("C332 source-backed Challenge review/next-question atomic continuation: PASS");
 return 0;
}
