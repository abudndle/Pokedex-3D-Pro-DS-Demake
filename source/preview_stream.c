/* Stream original-ROM-derived low-poly mesh samples from NitroFS.
 * Each DS3M contains ONLY source triangle coordinates normalized for DS;
 * no procedural replacements or unverified textures are included here.
 * Requires BlocksDS/libnds and an .nds with nitrofs/ packaged correctly.
 */
#include <nds.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "preview_stream.h"

#define C7_MAX_PREVIEW_TRIANGLES 600
static int16_t s_xyz[C7_MAX_PREVIEW_TRIANGLES * 9];
static int s_loaded = 0;
static int s_triangle_count = 0;
static int s_original_triangle_count = 0;
static int s_fs_available = 0;

static uint16_t get16(const unsigned char *p) {
    return (uint16_t)((unsigned int)p[0] | ((unsigned int)p[1] << 8));
}
static uint32_t get32(const unsigned char *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
int previewStreamInit(void) {
#ifdef C7_TEST_HOST
    s_fs_available = 1;
#else
    /* main() owns NitroFS mounting; never initialize the filesystem twice. */
    s_fs_available = 1;
#endif
    return s_fs_available;
}
int previewStreamLoad(int resource_index) {
    unsigned char head[16];
    char path[80];
    FILE *f;
    unsigned int tri_count, j;
    s_loaded=0;
    s_triangle_count=0;
    s_original_triangle_count=0;
    if (!s_fs_available || resource_index < 0 || resource_index > 729) return 0;
#ifdef C7_TEST_HOST
    snprintf(path,sizeof(path),"nitrofs/preview/p%03d.ds3m",resource_index);
#else
    snprintf(path,sizeof(path),"nitro:/preview/p%03d.ds3m",resource_index);
#endif
    f=fopen(path,"rb");
    if (!f) return 0;
    if (fread(head,1,sizeof(head),f)!=sizeof(head)) {fclose(f);return 0;}
    if (memcmp(head,"DS3M",4)!=0 || get16(head+4)!=1) {fclose(f);return 0;}
    tri_count=get16(head+6);
    if (tri_count<1 || tri_count>C7_MAX_PREVIEW_TRIANGLES) {fclose(f);return 0;}
    if (fread(s_xyz,sizeof(s_xyz[0]),tri_count*9,f)!=(size_t)tri_count*9) {fclose(f);return 0;}
    if (fgetc(f)!=EOF) {fclose(f);return 0;}
    fclose(f);
    s_triangle_count=(int)tri_count;
    s_original_triangle_count=(int)get32(head+12);
    s_loaded=1;
    /* Native Nintendo DS ARM9 runs little-endian, matching DS3M data. */
    for (j=0;j<(unsigned int)(s_triangle_count*9);j++) {
        /* Values are signed v16 4.12; no extra conversion is necessary. */
        (void)s_xyz[j];
    }
    return 1;
}
int previewStreamHasModel(void) { return s_loaded; }
int previewStreamTriangleCount(void) { return s_triangle_count; }
int previewStreamOriginalTriangleCount(void) { return s_original_triangle_count; }
void previewStreamDraw(void) {
    int i;
    if (!s_loaded) return;
    glColor3b(192,224,232);
    glBegin(GL_TRIANGLES);
    for (i=0;i<s_triangle_count*9;i+=3)
        glVertex3v16((v16)s_xyz[i],(v16)s_xyz[i+1],(v16)s_xyz[i+2]);
    glEnd();
}
