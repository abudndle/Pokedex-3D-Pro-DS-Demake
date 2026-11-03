#include "challenge_text.h"
#include "dex_text.h"
#include <string.h>

/* C331 uses only recovered P3DX text records at runtime. No catalog,
 * missing description/option name, corrupt question, or stale selection
 * may silently turn the unlocked text Challenge into numbered guesswork. */
int p3dChallengeTextLoad(P3DChallengeText *out,const P3DChallenge *quiz){
 P3DChallengeText candidate;
 P3DDexText entry;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!quiz || quiz->mode!=P3D_CHALLENGE_TEXT_MODE ||
    (quiz->stage!=P3D_CHALLENGE_QUESTION &&
     quiz->stage!=P3D_CHALLENGE_REVIEW) ||
    quiz->question<0 || quiz->question>=P3D_CHALLENGE_QUESTIONS ||
    quiz->pokemon<0 || quiz->pokemon>=P3D_NATIONAL_SPECIES_COUNT ||
    quiz->correct<0 || quiz->correct>=P3D_CHALLENGE_OPTIONS ||
    quiz->choices[quiz->correct]!=quiz->pokemon)return 0;
 for(int i=0;i<P3D_CHALLENGE_OPTIONS;i++){
  if(quiz->choices[i]<0 || quiz->choices[i]>=P3D_NATIONAL_SPECIES_COUNT)return 0;
  for(int j=0;j<i;j++)if(quiz->choices[j]==quiz->choices[i])return 0;
 }
 if(!p3dDexTextRead(quiz->pokemon,&entry) || !entry.description[0])
    return 0;
 memset(&candidate,0,sizeof candidate);
 memcpy(candidate.clue,entry.description,sizeof candidate.clue);
 candidate.pages=p3dChallengeCluePages(candidate.clue);
 if(candidate.pages<1 || quiz->clue_page<0 || quiz->clue_page>=candidate.pages)
    return 0;
 for(int i=0;i<P3D_CHALLENGE_OPTIONS;i++){
  if(!p3dDexTextRead(quiz->choices[i],&entry)||!entry.name[0])
    return 0;
  memcpy(candidate.names[i],entry.name,sizeof candidate.names[i]);
  candidate.choices[i]=quiz->choices[i];
 }
 candidate.pokemon=quiz->pokemon;
 candidate.question=quiz->question;
 candidate.correct=quiz->correct;
 candidate.ready=1;
 *out=candidate;
 return 1;
}

int p3dChallengeTextAnswer(P3DChallenge *quiz,int choice){
 P3DChallengeText current;
 if(!quiz||quiz->stage!=P3D_CHALLENGE_QUESTION||
    !p3dChallengeTextLoad(&current,quiz))return -1;
 /* Reload the actual source entries for this exact current question
  * before scoring. No cached text from a prior round authorizes answers. */
 return p3dChallengeAnswer(quiz,choice);
}

int p3dChallengeTextPageStep(P3DChallenge *quiz,int direction){
 P3DChallengeText current;
 if(!quiz||quiz->stage!=P3D_CHALLENGE_QUESTION||
    (direction!=1 && direction!=-1)||
    !p3dChallengeTextLoad(&current,quiz))return 0;
 if((direction>0 && quiz->clue_page>=current.pages-1)||
    (direction<0 && quiz->clue_page<=0))return 0;
 quiz->clue_page+=direction;
 return 1;
}
