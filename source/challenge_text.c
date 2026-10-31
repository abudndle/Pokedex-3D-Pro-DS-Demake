#include "challenge_text.h"
#include <string.h>
int p3dChallengeTextLoad(P3DChallengeText *text,const P3DChallenge *quiz){
 P3DDexText option;
 if(!text)return 0;
 memset(text,0,sizeof(*text));
 if(!quiz||quiz->stage!=P3D_CHALLENGE_QUESTION||quiz->mode!=P3D_CHALLENGE_TEXT_MODE)return 0;
 if(!p3dDexInfoLoad(&text->clue,quiz->pokemon)||!text->clue.text.description[0])goto missing;
 for(int i=0;i<P3D_CHALLENGE_OPTIONS;i++){
  if(!p3dDexTextRead(quiz->choices[i],&option)||!option.name[0])goto missing;
  memcpy(text->names[i],option.name,sizeof(text->names[i]));
  text->choices[i]=quiz->choices[i];
 }
 text->ready=1;return 1;
missing:
 memset(text,0,sizeof(*text));return 0;
}
int p3dChallengeTextAnswer(P3DChallengeText *text,P3DChallenge *quiz,int choice){
 int result;
 if(!text||!text->ready||!quiz||quiz->mode!=P3D_CHALLENGE_TEXT_MODE||
    quiz->stage!=P3D_CHALLENGE_QUESTION||text->clue.index!=quiz->pokemon)return -1;
 for(int i=0;i<P3D_CHALLENGE_OPTIONS;i++)if(text->choices[i]!=quiz->choices[i])return -1;
 result=p3dChallengeAnswer(quiz,choice);
 if(result>=0)text->ready=0;
 return result;
}
