/* Host regression test for the dual-slot save format.
 * Link with source/save_store.c. Uses only self-created temporary files.
 */
#include "save_store.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
int main(void){
    char base[120],a[128],b[128];
    P3DSaveState one={0},two={0},got={0};
    snprintf(base,sizeof(base),"/tmp/p3d_save_test_%ld",(long)getpid());
    snprintf(a,sizeof(a),"%s_A.sav",base);
    snprintf(b,sizeof(b),"%s_B.sav",base);
    remove(a);remove(b);
    one.selected_model=25;one.rotate=1;
    two.selected_model=151;two.rotate=1;
    assert(p3dSaveStore(base,&one));
    assert(p3dSaveLoad(base,&got)&&got.selected_model==25);
    assert(p3dSaveStore(base,&two));
    assert(p3dSaveLoad(base,&got)&&got.selected_model==151);
    /* Corrupt newest B slot; loader must recover older valid A slot. */
    FILE *f=fopen(b,"r+b");
    assert(f);
    assert(fseek(f,20,SEEK_SET)==0);
    assert(fputc(0xff,f)!=EOF);
    assert(fclose(f)==0);
    assert(p3dSaveLoad(base,&got)&&got.selected_model==25);
    /* A subsequent save must restore redundancy after the damaged B slot. */
    assert(p3dSaveStore(base,&two));
    assert(p3dSaveLoad(base,&got)&&got.selected_model==151);
    /* Truncating B must also recover the older valid A generation. */
    f=fopen(b,"wb");
    assert(f);
    assert(fputc(0,f)!=EOF);
    assert(fclose(f)==0);
    assert(p3dSaveLoad(base,&got)&&got.selected_model==25);
    remove(a);remove(b);
    puts("Dual-slot save recovery: PASS");
    return 0;
}
