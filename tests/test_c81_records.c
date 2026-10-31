#include "records.h"
#include "save_store.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static void slot(char *out,size_t size,const char *prefix,char id) {
    int n=snprintf(out,size,"%s_records_%c.sav",prefix,id);
    assert(n>0 && (size_t)n<size);
}
static void flip(const char *path) {
    FILE *f=fopen(path,"r+b");
    int c;
    assert(f);
    assert(fseek(f,20,SEEK_SET)==0);
    c=fgetc(f);assert(c!=EOF);
    assert(fseek(f,20,SEEK_SET)==0);
    assert(fputc(c^1,f)!=EOF);
    assert(fclose(f)==0);
}
int main(int argc,char **argv) {
    P3DRecords history,readback,older,bad;
    P3DSaveState legacy,loaded_legacy;
    char a[256],b[256];
    assert(argc==2);
    slot(a,sizeof(a),argv[1],'A');
    slot(b,sizeof(b),argv[1],'B');
    remove(a);remove(b);
    p3dRecordsReset(&history);
    assert(p3dRecordsValid(&history));
    assert(!p3dRecordsLoad(argv[1],&readback));
    assert(history.recent[0]==P3D_RECORD_NO_SPECIES);
    assert(p3dRecordsTotal(&history)==0);
    for(int i=0;i<649;i++)assert(p3dRecordsVisit(&history,i));
    assert(p3dRecordsTotal(&history)==649);
    assert(p3dRecordsCount(&history,0,150)==151);
    assert(p3dRecordsCount(&history,151,250)==100);
    assert(p3dRecordsCount(&history,251,385)==135);
    assert(p3dRecordsCount(&history,386,492)==107);
    assert(p3dRecordsCount(&history,493,648)==156);
    assert(!p3dRecordsVisit(&history,648));
    assert(p3dRecordsVisit(&history,640));
    assert(history.recent[0]==640);
    assert(p3dRecordsComplete(&history,3,6));
    assert(p3dRecordsComplete(&history,3,9));
    assert(history.best[3]==9 && history.runs[3]==2);
    assert(!p3dRecordsComplete(&history,7,10));
    assert(p3dRecordsValid(&history));
    assert(p3dRecordsStore(argv[1],&history));
    assert(p3dRecordsLoad(argv[1],&readback));
    assert(memcmp(&history,&readback,sizeof(history))==0);
    older=history;
    assert(p3dRecordsVisit(&history,1));
    assert(p3dRecordsStore(argv[1],&history));
    flip(b); /* Newer slot corrupted: recover last valid snapshot. */
    assert(p3dRecordsLoad(argv[1],&readback));
    assert(memcmp(&older,&readback,sizeof(older))==0);
    assert(p3dRecordsStore(argv[1],&history)); /* Repair corrupt slot. */
    assert(p3dRecordsLoad(argv[1],&readback));
    assert(memcmp(&history,&readback,sizeof(history))==0);
    bad=history;bad.viewed[81]|=0x80;
    assert(!p3dRecordsValid(&bad));
    assert(!p3dRecordsStore(argv[1],&bad));
    bad=history;bad.recent[1]=bad.recent[0];
    assert(!p3dRecordsValid(&bad));
    memset(&legacy,0,sizeof(legacy));
    legacy.selected_model=25;legacy.move_index=12;legacy.rotate=1;
    legacy.challenge_correct=3;legacy.challenge_total=4;
    assert(p3dSaveStore(argv[1],&legacy));
    assert(p3dSaveLoad(argv[1],&loaded_legacy));
    assert(memcmp(&legacy,&loaded_legacy,sizeof(legacy))==0);
    assert(p3dRecordsStore(argv[1],&history));
    assert(p3dSaveLoad(argv[1],&loaded_legacy));
    assert(memcmp(&legacy,&loaded_legacy,sizeof(legacy))==0);
    printf("C81 Records: 649 species, five regions, challenge scores, CRC recovery, old save PASS\n");
    return 0;
}
