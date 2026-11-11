#ifndef P3D_SPECIES_LEARNSET_H
#define P3D_SPECIES_LEARNSET_H
#include <stdint.h>
#define P3D_LEARNSET_MAX 256u
#define P3D_LEARNSET_PAGE_ROWS 4u
#define P3D_LEARNSET_FIRST_ROW 12u
typedef struct {
    uint16_t move;
    uint8_t method,level;
} P3DLearnsetRow;
typedef struct {
    uint16_t species,form,count;
    uint32_t checksum;
    uint8_t ready;
    P3DLearnsetRow rows[P3D_LEARNSET_MAX];
} P3DLearnset;
/* P3SL validates transport integrity, not original-source authenticity.
 * Only privately source-verified complete records should be staged. */
int p3dLearnsetLoad(const char *path,int species,int form,P3DLearnset *out);
int p3dLearnsetPath(char path[80],int species,int form);
unsigned p3dLearnsetPage(const P3DLearnset *set,unsigned page,int direction);
unsigned p3dLearnsetRestorePage(const P3DLearnset *set,unsigned page,uint32_t checksum);
/* Text fallback only. Return a validated Move Dex index, or -1 for no hit. */
int p3dLearnsetTouchMove(const P3DLearnset *set,unsigned page,int visible,int x,int y);
const char *p3dLearnsetMethod(unsigned method);
#endif
