#ifndef P3D_CHALLENGE_TEXT_H
#define P3D_CHALLENGE_TEXT_H
#include "challenge.h"
#include "dex_info.h"
typedef struct { P3DDexInfo clue; char names[P3D_CHALLENGE_OPTIONS][32]; int choices[P3D_CHALLENGE_OPTIONS]; int ready; } P3DChallengeText;
/* Requires a complete description and all four original option names.
 * Failure clears previous text. Never mutates quiz scoring or progression. */
/* Only a currently loaded, complete question can be scored. */
int p3dChallengeTextAnswer(P3DChallengeText *text,P3DChallenge *quiz,int choice);
int p3dChallengeTextLoad(P3DChallengeText *text,const P3DChallenge *quiz);
#endif
