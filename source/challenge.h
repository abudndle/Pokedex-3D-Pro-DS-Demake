#ifndef P3D_CHALLENGE_H
#define P3D_CHALLENGE_H
#include <stdint.h>
#define P3D_CHALLENGE_INITIAL_MODES 6
#define P3D_CHALLENGE_MODES 7
#define P3D_CHALLENGE_TEXT_MODE 6
#define P3D_CHALLENGE_TEXT_UNLOCK 50
#define P3D_CHALLENGE_QUESTIONS 10
#define P3D_CHALLENGE_OPTIONS 4
typedef enum { P3D_CHALLENGE_PICKER=0, P3D_CHALLENGE_QUESTION=1, P3D_CHALLENGE_RESULTS=2 } P3DChallengeStage;
typedef struct {
 P3DChallengeStage stage;
 int mode_cursor,mode,question,score,selected,clue_page,correct,pokemon;
 int choices[P3D_CHALLENGE_OPTIONS],asked[P3D_CHALLENGE_QUESTIONS];
 uint32_t seed;
} P3DChallenge;
const char *p3dChallengeName(int mode);
int p3dChallengeRange(int mode,int *first,int *last);
int p3dChallengeAvailableModes(int cumulative_answers);
int p3dChallengeCluePages(const char *text);
void p3dChallengeClue(const char *text,int page,char line1[29],char line2[29]);
void p3dChallengeReset(P3DChallenge *quiz);
int p3dChallengeBegin(P3DChallenge *quiz,int mode,uint32_t seed,int cumulative_answers);
int p3dChallengeAnswer(P3DChallenge *quiz,int choice);
#endif
