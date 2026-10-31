#include <assert.h>
#include <stdio.h>
#include "preview_stream.h"
static int emitted;
void glColor3b(unsigned char r,unsigned char g,unsigned char b){(void)r;(void)g;(void)b;}
void glBegin(int m){assert(m==1);}
void glVertex3v16(short x,short y,short z){(void)x;(void)y;(void)z;emitted++;}
void glEnd(void){}
int main(void){
 assert(previewStreamInit());
 assert(previewStreamLoad(0));
 assert(previewStreamHasModel());
 assert(previewStreamTriangleCount()==1);
 assert(previewStreamOriginalTriangleCount()==42);
 previewStreamDraw();assert(emitted==3);
 assert(!previewStreamLoad(721));
 assert(!previewStreamHasModel());
 puts("Original-geometry preview stream: PASS");
 return 0;
}
