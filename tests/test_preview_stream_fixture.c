#include <assert.h>
#include <stdio.h>
#include "preview_stream.h"
static int emitted;
static int red_seen,green_seen;

void glColor3b(unsigned char r,unsigned char g,unsigned char b){if(r==255&&g==0&&b==0)red_seen++;if(r==0&&g==255&&b==0)green_seen++;}
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
 assert(previewStreamLoad(1));
 assert(previewStreamTriangleCount()==600);
 emitted=0; previewStreamDraw(); assert(emitted==1800);
 assert(previewStreamLoad(3));
 emitted=0;red_seen=green_seen=0; previewStreamDraw();
 assert(emitted==6 && red_seen==1 && green_seen==1);
 assert(!previewStreamLoad(4)); /* v2 colors truncated */
 assert(!previewStreamLoad(2)); /* 601 triangles must not overflow the buffer. */
 assert(!previewStreamLoad(721));
 assert(!previewStreamHasModel());
 puts("Original-geometry preview stream: PASS");
 return 0;
}
