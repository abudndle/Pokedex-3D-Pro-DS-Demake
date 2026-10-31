#include "bmp_loader.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
int main(int argc,char **argv){
 uint16_t pixels[4];int w=0,h=0;
 if(argc!=2)return 2;
 assert(p3dBmpDecode24(argv[1],pixels,4,&w,&h));
 assert(w==2&&h==2);
 /* Top left is red; top right green; lower left blue. */
 assert(pixels[0]==0xfc00u);
 assert(pixels[1]==0x83e0u);
 assert(pixels[2]==0x801fu);
 assert(!p3dBmpDecode24(argv[1],pixels,3,&w,&h));
 puts("BMP RGB555 decoder: PASS");return 0;
}
