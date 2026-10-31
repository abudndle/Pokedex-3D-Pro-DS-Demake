#include "challenge.h"
#include <string.h>
static const char *s_modes[P3D_CHALLENGE_MODES]={"POKEMON: UNOVA","POKEMON: KANTO","POKEMON: JOHTO","POKEMON: HOENN","POKEMON: SINNOH","POKEMON: NATIONAL","POKEDEX TEST"};
static const int s_first[]={493,0,151,251,386,0,0};
static const int s_last[]={648,150,250,385,492,648,648};
const char *p3dChallengeName(int mode){return mode>=0&&mode<P3D_CHALLENGE_MODES?s_modes[mode]:"UNKNOWN";}
int p3dChallengeRange(int mode,int *first,int *last){
 if(mode<0||mode>=P3D_CHALLENGE_MODES)return 0;
 if(first)*first=s_first[mode];
 if(last)*last=s_last[mode];
 return 1;
}
int p3dChallengeAvailableModes(int cumulative_answers){return cumulative_answers>=P3D_CHALLENGE_TEXT_UNLOCK?P3D_CHALLENGE_MODES:P3D_CHALLENGE_INITIAL_MODES;}
int p3dChallengeCluePages(const char *description){size_t len=description?strlen(description):0;return len?(int)((len+55)/56):1;}
void p3dChallengeClue(const char *description,int page,char line1[29],char line2[29]){
 size_t start,total,n;
 if(!line1||!line2)return;
 line1[0]=line2[0]=0;
 if(!description||page<0)return;
 total=strlen(description);start=(size_t)page*56;
 if(start>=total)return;
 n=total-start;if(n>28)n=28;
 memcpy(line1,description+start,n);line1[n]=0;
 start+=n;if(start>=total)return;
 n=total-start;if(n>28)n=28;
 memcpy(line2,description+start,n);line2[n]=0;
}
static uint32_t next_random(P3DChallenge *q){uint32_t x=q->seed;x^=x<<13;x^=x>>17;x^=x<<5;q->seed=x;return x;}
static int random_range(P3DChallenge *q,int count){return (int)(next_random(q)%(uint32_t)count);}
static void make_question(P3DChallenge *q){
 int first=s_first[q->mode],last=s_last[q->mode],count=last-first+1,i,j,used,position;
 do{q->pokemon=first+random_range(q,count);used=0;for(i=0;i<q->question;i++)if(q->asked[i]==q->pokemon)used=1;}while(used);
 q->asked[q->question]=q->pokemon;q->correct=random_range(q,P3D_CHALLENGE_OPTIONS);
 for(i=0;i<P3D_CHALLENGE_OPTIONS;i++)q->choices[i]=-1;
 q->choices[q->correct]=q->pokemon;
 for(i=0;i<P3D_CHALLENGE_OPTIONS;i++){
  if(i==q->correct)continue;
  do{position=first+random_range(q,count);used=(position==q->pokemon);
   for(j=0;j<i;j++)if(q->choices[j]==position)used=1;
  }while(used);
  q->choices[i]=position;
 }
 q->selected=0;q->clue_page=0;
}
void p3dChallengeReset(P3DChallenge *q){if(!q)return;memset(q,0,sizeof(*q));q->stage=P3D_CHALLENGE_PICKER;}
int p3dChallengeBegin(P3DChallenge *q,int mode,uint32_t seed,int cumulative_answers){
 if(!q||mode<0||mode>=p3dChallengeAvailableModes(cumulative_answers))return 0;
 p3dChallengeReset(q);q->mode=mode;q->mode_cursor=mode;
 q->stage=P3D_CHALLENGE_QUESTION;q->seed=seed?seed:0xBA5EBA11u;
 make_question(q);return 1;
}
int p3dChallengeAnswer(P3DChallenge *q,int choice){
 int success;
 if(!q||q->stage!=P3D_CHALLENGE_QUESTION||choice<0||choice>=P3D_CHALLENGE_OPTIONS)return -1;
 success=(choice==q->correct);if(success)q->score++;q->question++;
 if(q->question==P3D_CHALLENGE_QUESTIONS)q->stage=P3D_CHALLENGE_RESULTS;
 else make_question(q);
 return success;
}
