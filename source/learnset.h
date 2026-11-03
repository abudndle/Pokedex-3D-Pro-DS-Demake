#ifndef P3D_LEARNSET_H
#define P3D_LEARNSET_H
#include <stdint.h>
#define P3D_LEARNSET_MAX_ROWS 256u
#define P3D_LEARNSET_PAGE_ROWS 4u
#define P3D_LEARNSET_SPECIES 649u
#define P3D_LEARNSET_MAX_FORM 999u
#define P3D_LEARNSET_MOVE_COUNT 559u
/* Optional private P3SL transport. A valid CRC proves transport integrity
 * only, NOT original 3DS provenance or complete learnset recovery.
 * No original Nintendo data is bundled with this homebrew source. */
typedef enum {
 P3D_LEARN_LEVEL=1,
 P3D_LEARN_TM=2,
 P3D_LEARN_EGG=3,
 P3D_LEARN_TUTOR=4,
 P3D_LEARN_EVENT=5
} P3DLearnMethod;
typedef struct {
 uint16_t move_index; /* 0-based index of verified original P3DM name record */
 uint8_t method, level; /* level 1..100 iff method==P3D_LEARN_LEVEL */
} P3DLearnsetRow;
typedef struct {
 uint16_t species,form,count;
 uint8_t ready;
 P3DLearnsetRow entries[P3D_LEARNSET_MAX_ROWS];
} P3DLearnset;
void p3dLearnsetClear(P3DLearnset *out);
int p3dLearnsetPath(char path[80],int species,int form);
int p3dLearnsetLoad(const char *path,int species,int form,P3DLearnset *out);
unsigned p3dLearnsetPageCount(const P3DLearnset *set);
unsigned p3dLearnsetStep(const P3DLearnset *set,unsigned page,int direction);
const char *p3dLearnsetMethodName(int method);
#endif
