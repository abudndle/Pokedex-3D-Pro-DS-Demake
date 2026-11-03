#ifndef P3D_CHALLENGE_H
#define P3D_CHALLENGE_H
#include <stdint.h>
#define P3D_CHALLENGE_INITIAL_MODES 6
#define P3D_CHALLENGE_MODES 7
#define P3D_CHALLENGE_TEXT_MODE 6
#define P3D_CHALLENGE_TEXT_UNLOCK 50
#define P3D_CHALLENGE_QUESTIONS 10
#define P3D_CHALLENGE_OPTIONS 4
typedef enum { P3D_CHALLENGE_PICKER=0, P3D_CHALLENGE_QUESTION=1, P3D_CHALLENGE_RESULTS=2, P3D_CHALLENGE_REVIEW=3 } P3DChallengeStage;
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
/* Start a new round from the next session seed. A successful start advances
 * the caller seed so replaying the same mode does not reset the questions.
 * Invalid requests leave the seed unchanged. */
int p3dChallengeBeginSession(P3DChallenge *quiz,int mode,uint32_t *next_seed,int cumulative_answers);
/* Answer once and retain the source-backed question for review.
 * Returns correct(1), incorrect(0), or rejected(-1). */
int p3dChallengeAnswer(P3DChallenge *quiz,int choice);
/* Move from review to next question or final results. Does not score. */
int p3dChallengeContinue(P3DChallenge *quiz);
/* Fallback text UI only: console rows 11,14,17,20.
 * Original bitmap artwork touch geometry is NOT inferred. */
int p3dChallengeTouchChoice(int x,int y);
/* Fallback review continuation text on console row 19. */
int p3dChallengeTouchContinue(int x,int y);
#endif
