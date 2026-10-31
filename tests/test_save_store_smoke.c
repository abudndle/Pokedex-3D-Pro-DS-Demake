#include "save_store.h"
#include <stdio.h>
#include <assert.h>
#include <string.h>
int main(int argc,char **argv){
 P3DSaveState a={0},b={0};if(argc!=2)return 2;
 a.selected_model=1;a.move_index=20;a.favorite_count=1;a.favorites[0]=25;a.rotate=1;
 assert(p3dSaveStore(argv[1],&a));assert(p3dSaveLoad(argv[1],&b));assert(b.selected_model==1);
 a.selected_model=3;assert(p3dSaveStore(argv[1],&a));assert(p3dSaveLoad(argv[1],&b));assert(b.selected_model==3);
 a.favorite_count=7;assert(!p3dSaveStore(argv[1],&a));
 puts("Save backup and validation: PASS");return 0;
}
