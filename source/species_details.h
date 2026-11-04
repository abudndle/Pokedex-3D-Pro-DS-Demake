#ifndef P3D_SPECIES_DETAILS_H
#define P3D_SPECIES_DETAILS_H
#include <stdint.h>
#define P3D_DETAIL_RECORD_SIZE 64u
#define P3D_DETAIL_NATIONAL_SPECIES 649
#define P3D_DETAIL_MOVE_INDEX_COUNT 559
#define P3D_DETAIL_MAX_FORM 999
#define P3D_DETAIL_STATS 1u
#define P3D_DETAIL_ABILITIES 2u
#define P3D_DETAIL_EVOLUTIONS 4u
#define P3D_DETAIL_MOVES 8u
#define P3D_DETAIL_TABS 4
/* Source-verified optional metadata transport. A valid CRC proves byte
 * integrity only, NOT original Nintendo provenance: private sidecars must
 * be independently cross-checked against licensed source exports. */
typedef struct {
    uint16_t species,form,ability_ids[3],evolutions[2],move_indices[4];
    uint8_t fields,stats[6],abilities_count,evolutions_count,moves_count;
} P3DSpeciesDetails;
void p3dSpeciesDetailsClear(P3DSpeciesDetails *details);
int p3dSpeciesDetailsValid(const P3DSpeciesDetails *details);
int p3dSpeciesDetailsLoad(const char *path,int species,int form,P3DSpeciesDetails *out);
/* Only the explicitly enumerated optional NitroFS path is attempted. */
int p3dSpeciesDetailPath(char path[80],int species,int form);
const char *p3dSpeciesDetailTabName(int tab);
#define P3D_EVOLUTION_ROW_TOP 88
#define P3D_EVOLUTION_ROW_STEP 16
/* Canonical P3SD targets have no target-form field; follow into base form.
 * Failures preserve all navigation outputs, including stale source records. */
int p3dSpeciesEvolutionTouch(const P3DSpeciesDetails *details,int x,int y,
                               int *species,int *selected_species,int *form);
#endif
