#ifndef P3D_CHALLENGE_TEXT_H
#define P3D_CHALLENGE_TEXT_H
#include "challenge.h"
/* Source-backed answer options: never invent species names/descriptions. */
typedef struct {
 char clue[192];
 char names[P3D_CHALLENGE_OPTIONS][32];
 int choices[P3D_CHALLENGE_OPTIONS];
 int pokemon,question,correct,pages,ready;
} P3DChallengeText;
/* Clears the output on failure. Question and review stages may show text. */
int p3dChallengeTextLoad(P3DChallengeText *out,const P3DChallenge *quiz);
/* Text-mode submissions are rejected when original P3DX text is missing. */
int p3dChallengeTextAnswer(P3DChallenge *quiz,int choice);
/* Page a validated current text clue, without modifying scoring. */
int p3dChallengeTextPageStep(P3DChallenge *quiz,int direction);
/* Atomically validate current and next source-backed question on continue. */
int p3dChallengeTextContinue(P3DChallenge *quiz);
#endif
