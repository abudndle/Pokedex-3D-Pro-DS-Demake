#ifndef P3D_RECORDS_H
#define P3D_RECORDS_H
#include <stdint.h>
#define P3D_RECORD_SPECIES 649
#define P3D_RECORD_BYTES ((P3D_RECORD_SPECIES+7)/8)
#define P3D_RECORD_RECENT 8
#define P3D_RECORD_CHALLENGES 7
#define P3D_RECORD_NO_SPECIES 0xFFFFu
typedef struct {
    uint8_t viewed[P3D_RECORD_BYTES];
    uint16_t recent[P3D_RECORD_RECENT]; /* Most recently opened first. */
    uint16_t runs[P3D_RECORD_CHALLENGES];
    uint8_t best[P3D_RECORD_CHALLENGES];
    uint32_t rounds;
} P3DRecords;
/* Independent P3RC v1 save: does not modify legacy P3SV files. */
void p3dRecordsReset(P3DRecords *r);
int p3dRecordsValid(const P3DRecords *r);
int p3dRecordsVisit(P3DRecords *r,int species);
int p3dRecordsSeen(const P3DRecords *r,int species);
int p3dRecordsCount(const P3DRecords *r,int first,int last);
int p3dRecordsTotal(const P3DRecords *r);
int p3dRecordsComplete(P3DRecords *r,int challenge_mode,int score);
int p3dRecordsStore(const char *save_base,const P3DRecords *r);
int p3dRecordsLoad(const char *save_base,P3DRecords *out);
#endif
