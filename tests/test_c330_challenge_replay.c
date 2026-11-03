#include "challenge.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* The native game must not replay the same fixed ten-question sequence
 * every time the player restarts a Challenge mode. */
int main(void){
    P3DChallenge q, reference;
    uint32_t seed=0x13579BDFu;
    uint32_t original=seed, second;
    int first_pokemon, first_correct;
    int first_choices[P3D_CHALLENGE_OPTIONS];

    /* Failure must not consume randomness or change the current round. */
    assert(!p3dChallengeBeginSession(NULL,0,&seed,0));
    assert(!p3dChallengeBeginSession(&q,0,NULL,0));
    assert(!p3dChallengeBeginSession(&q,P3D_CHALLENGE_TEXT_MODE,&seed,0));
    assert(seed==original);

    assert(p3dChallengeBeginSession(&q,0,&seed,0));
    assert(q.stage==P3D_CHALLENGE_QUESTION && q.question==0 && q.score==0);
    assert(seed!=original && seed!=0);
    first_pokemon=q.pokemon;
    first_correct=q.correct;
    memcpy(first_choices,q.choices,sizeof first_choices);

    /* Seeded single-round behavior stays reproducible for offline tests. */
    assert(p3dChallengeBegin(&reference,0,original,0));
    assert(reference.pokemon==first_pokemon);
    assert(reference.correct==first_correct);
    assert(memcmp(reference.choices,first_choices,sizeof first_choices)==0);

    second=seed;
    assert(p3dChallengeBeginSession(&q,0,&seed,0));
    assert(q.stage==P3D_CHALLENGE_QUESTION && q.question==0 && q.score==0);
    assert(seed!=second && seed!=0);
    assert(q.pokemon!=first_pokemon || q.correct!=first_correct ||
           memcmp(q.choices,first_choices,sizeof first_choices)!=0);
    assert(p3dChallengeBegin(&reference,0,second,0));
    assert(q.pokemon==reference.pokemon && q.correct==reference.correct);
    assert(memcmp(q.choices,reference.choices,sizeof q.choices)==0);

    /* Zero seeds still enter the historical safe nonzero RNG state. */
    seed=0;
    assert(p3dChallengeBeginSession(&q,0,&seed,0));
    assert(seed!=0);
    puts("C330 Challenge replay advances session seed and preserves seeded tests: PASS");
    return 0;
}
