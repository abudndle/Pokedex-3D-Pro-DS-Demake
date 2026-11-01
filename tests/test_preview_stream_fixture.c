#include <assert.h>
#include <stdio.h>
#include "preview_stream.h"
static int emitted;
static int red_seen,green_seen;
static int uv_seen,white_seen;
static short uv_u[3],uv_v[3];

void glTexCoord2t16(short u,short v){if(uv_seen<3){uv_u[uv_seen]=u;uv_v[uv_seen]=v;}uv_seen++;}
void glColor3b(unsigned char r,unsigned char g,unsigned char b){if(r==255&&g==255&&b==255)white_seen++;if(r==255&&g==0&&b==0)red_seen++;if(r==0&&g==255&&b==0)green_seen++;}
void glBegin(int m){assert(m==1);}
void glVertex3v16(short x,short y,short z){(void)x;(void)y;(void)z;emitted++;}
void glEnd(void){}
int main(void){
 assert(previewStreamInit());
 assert(previewStreamLoad(0));
 assert(previewStreamHasModel());
 assert(previewStreamTriangleCount()==1);
 assert(previewStreamOriginalTriangleCount()==42);
 assert(previewStreamHasUv());
 previewStreamDraw();assert(emitted==3 && uv_seen==3);
 emitted=0;uv_seen=0;white_seen=0;
 previewStreamDrawMode(8,16);
 assert(emitted==3 && uv_seen==3 && white_seen==1);
 assert(uv_u[0]==0 && uv_v[0]==0);
 assert(uv_u[1]==128 && uv_v[1]==0);
 assert(uv_u[2]==0 && uv_v[2]==256);
 assert(previewStreamLoad(1));
 assert(previewStreamTriangleCount()==600);
 assert(!previewStreamHasUv());
 emitted=0; previewStreamDraw(); assert(emitted==1800);
 assert(previewStreamLoad(3));
 emitted=0;red_seen=green_seen=0; previewStreamDraw();
 assert(emitted==6 && red_seen==1 && green_seen==1);
 emitted=0;red_seen=green_seen=0;
 previewStreamDrawRange(1,1,0,0);
 assert(emitted==3 && red_seen==0 && green_seen==1);
 emitted=0;
 previewStreamDrawRange(1,2,0,0);
 assert(emitted==0); /* Reject ranges exceeding the loaded mesh. */
 previewStreamDrawRange(-1,1,0,0);
 assert(emitted==0);
 previewStreamDrawRange(0,0,0,0);
 assert(emitted==0);
 assert(!previewStreamPrefersChunks()); /* C98 default preserves old gameplay. */
 assert(previewStreamLoad(5)); /* p005 has BOTH legacy and chunked files */
 assert(!previewStreamIsChunked());
 assert(previewStreamTriangleCount()==1);
 previewStreamPreferChunks(1);
 assert(previewStreamPrefersChunks());
 assert(previewStreamLoad(5)); /* explicit opt-in selects 1202 faces */
 assert(previewStreamIsChunked());
 assert(previewStreamTriangleCount()==1202);
 assert(previewStreamOriginalTriangleCount()==5000);
 assert(!previewStreamHasUv()); /* sampler binding stays intentionally disabled */
 emitted=0;
 previewStreamDraw();
 assert(emitted==1202*3);
 emitted=0;
 previewStreamDrawRange(0,1,8,8); /* no external range without matched source textures */
 assert(emitted==0);
 /* Recheck an original-derived chunk *after* load. Its last source
  * byte changes after the open CRC check, requiring draw-time fail-close. */
 {
     FILE *mut=fopen("nitrofs/preview/p005.p3cs","r+b");
     assert(mut);
     assert(fseek(mut,-1,SEEK_END)==0);
     assert(fputc(0,mut)!=EOF);
     assert(fclose(mut)==0);
 }
 emitted=0;
 previewStreamDraw();
 assert(!previewStreamHasModel());
 assert(!previewStreamIsChunked());
 assert(!previewStreamHasUv());
 assert(previewStreamTriangleCount()==0);
 assert(previewStreamOriginalTriangleCount()==0);
 emitted=0;
 previewStreamDraw();
 assert(emitted==0);
 assert(previewStreamLoad(6)); /* invalid P3CS falls back to legacy DS3M */
 assert(!previewStreamIsChunked());
 assert(previewStreamTriangleCount()==1);
 assert(!previewStreamLoad(7)); /* P3CS-only corrupt source cannot render */
 assert(!previewStreamHasModel());
 previewStreamPreferChunks(0);
 assert(!previewStreamPrefersChunks());
 assert(previewStreamLoad(5)); /* reverting to original 600-face setting */
 assert(!previewStreamIsChunked());
 assert(previewStreamTriangleCount()==1);
 assert(!previewStreamLoad(4)); /* v2 colors truncated */
 assert(!previewStreamLoad(2)); /* 601 triangles must not overflow the buffer. */
 assert(!previewStreamLoad(721));
 assert(previewStreamLoad(737));
 assert(previewStreamTriangleCount()==1);
 assert(!previewStreamLoad(738));
 assert(!previewStreamLoad(-1));
 assert(!previewStreamHasModel());
 puts("Original-geometry preview stream: PASS");
 return 0;
}
