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
#include "model_uv.h"
#include "preview_chunk_stream.h"

#define C7_MAX_PREVIEW_TRIANGLES 600
static int16_t s_xyz[C7_MAX_PREVIEW_TRIANGLES * 9];
static unsigned char s_face_rgb[C7_MAX_PREVIEW_TRIANGLES * 3];
static int s_has_face_colors;
static P3DUvMap s_uv;
static int s_loaded = 0;
static int s_triangle_count = 0;
static int s_original_triangle_count = 0;
static int s_fs_available = 0;
static P3DChunkStream s_chunk_stream;
static int s_chunked = 0;
static int s_drawing_chunk = 0;

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
    unsigned int tri_count, j, version;
    s_loaded=0;
    s_triangle_count=0;
    s_original_triangle_count=0;
    s_has_face_colors=0;
    s_uv.ready=0;
    s_chunked=0;
    s_drawing_chunk=0;
    p3dChunkClose(&s_chunk_stream);
    if (!s_fs_available || resource_index < 0 || resource_index >= 738) return 0;
#ifdef C7_TEST_HOST
    snprintf(path,sizeof(path),"nitrofs/preview/p%03d.ds3m",resource_index);
#else
    snprintf(path,sizeof(path),"nitro:/preview/p%03d.ds3m",resource_index);
#endif
    f=fopen(path,"rb");
    if (!f){
        /* Diagnostic chunk assets are explicitly separate from the legacy
         * 600-face DS3M. No guessed P3MT texture maps are activated here. */
#ifdef C7_TEST_HOST
        snprintf(path,sizeof(path),"nitrofs/preview/p%03d.p3cs",resource_index);
#else
        snprintf(path,sizeof(path),"nitro:/preview/p%03d.p3cs",resource_index);
#endif
        if(!p3dChunkOpen(&s_chunk_stream,path,(unsigned)resource_index))return 0;
        s_chunked=1;
        s_triangle_count=(int)s_chunk_stream.total_triangles;
        s_original_triangle_count=(int)s_chunk_stream.original_triangles;
        s_loaded=1;
        return 1;
    }
    if (fread(head,1,sizeof(head),f)!=sizeof(head)) {fclose(f);return 0;}
    version=get16(head+4);
    if (memcmp(head,"DS3M",4)!=0 || (version!=1 && version!=2)) {fclose(f);return 0;}
    tri_count=get16(head+6);
    if (tri_count<1 || tri_count>C7_MAX_PREVIEW_TRIANGLES) {fclose(f);return 0;}
    if (fread(s_xyz,sizeof(s_xyz[0]),tri_count*9,f)!=(size_t)tri_count*9) {fclose(f);return 0;}
    /* v2 contract: packed RGB888 triplets, one per triangle, after all XYZ. */
    if (version==2 && fread(s_face_rgb,3,tri_count,f)!=(size_t)tri_count) {fclose(f);return 0;}
    if (fgetc(f)!=EOF) {fclose(f);return 0;}
    fclose(f);
    s_triangle_count=(int)tri_count;
    s_original_triangle_count=(int)get32(head+12);
    s_has_face_colors=(version==2);
    s_loaded=1;
    /* Optional private UV companion: never invent texture coordinates. */
#ifdef C7_TEST_HOST
    snprintf(path,sizeof(path),"nitrofs/preview/p%03d.p3uv",resource_index);
#else
    snprintf(path,sizeof(path),"nitro:/preview/p%03d.p3uv",resource_index);
#endif
    p3dUvLoad(&s_uv,path,tri_count);
    /* Native Nintendo DS ARM9 runs little-endian, matching DS3M data. */
    for (j=0;j<(unsigned int)(s_triangle_count*9);j++) {
        /* Values are signed v16 4.12; no extra conversion is necessary. */
        (void)s_xyz[j];
    }
    return 1;
}
int previewStreamHasModel(void) { return s_loaded; }
int previewStreamHasUv(void) { return s_loaded && !s_chunked && s_uv.ready; }
int previewStreamIsChunked(void) { return s_loaded && s_chunked; }
int previewStreamTriangleCount(void) { return s_triangle_count; }
int previewStreamOriginalTriangleCount(void) { return s_original_triangle_count; }
void previewStreamDrawRange(int first_triangle,int triangle_count,int texture_width,int texture_height) {
    int textured=texture_width>0 && texture_height>0;
    int i;
    if (!s_loaded || (s_chunked && !s_drawing_chunk) || first_triangle<0 || triangle_count<1 ||
        first_triangle>s_triangle_count || triangle_count>s_triangle_count-first_triangle) return;
    glColor3b(textured ? 255 : 192,textured ? 255 : 224,textured ? 255 : 232);
    glBegin(GL_TRIANGLES);
    for (i=first_triangle*9;i<(first_triangle+triangle_count)*9;i+=9) {
        if (s_has_face_colors && !textured) {
            int c=(i/9)*3;
            glColor3b(s_face_rgb[c],s_face_rgb[c+1],s_face_rgb[c+2]);
        }
        if(s_uv.ready)glTexCoord2t16((t16)(textured ? (int)s_uv.uv[(i/9)*6]*texture_width/256 : s_uv.uv[(i/9)*6]),(t16)(textured ? (int)s_uv.uv[(i/9)*6+1]*texture_height/256 : s_uv.uv[(i/9)*6+1]));
        glVertex3v16((v16)s_xyz[i],(v16)s_xyz[i+1],(v16)s_xyz[i+2]);
        if(s_uv.ready)glTexCoord2t16((t16)(textured ? (int)s_uv.uv[(i/9)*6+2]*texture_width/256 : s_uv.uv[(i/9)*6+2]),(t16)(textured ? (int)s_uv.uv[(i/9)*6+3]*texture_height/256 : s_uv.uv[(i/9)*6+3]));
        glVertex3v16((v16)s_xyz[i+3],(v16)s_xyz[i+4],(v16)s_xyz[i+5]);
        if(s_uv.ready)glTexCoord2t16((t16)(textured ? (int)s_uv.uv[(i/9)*6+4]*texture_width/256 : s_uv.uv[(i/9)*6+4]),(t16)(textured ? (int)s_uv.uv[(i/9)*6+5]*texture_height/256 : s_uv.uv[(i/9)*6+5]));
        glVertex3v16((v16)s_xyz[i+6],(v16)s_xyz[i+7],(v16)s_xyz[i+8]);
    }
    glEnd();
}

void previewStreamDraw(void) {
    if(!s_loaded)return;
    if(!s_chunked){
        previewStreamDrawRange(0,s_triangle_count,0,0);
        return;
    }
    /* Reuse the existing static 600-triangle vertex/UV/color buffers.
     * A full 1800-triangle source model is never resident in RAM. */
    const int total=s_triangle_count;
    for(unsigned i=0;i<s_chunk_stream.chunk_count;i++){
        if(!p3dChunkRead(&s_chunk_stream,i,s_xyz,s_uv.uv,s_face_rgb)){
            /* A chunk can become unreadable after successful open (media
             * corruption or truncated NitroFS asset). Invalidate all model
             * metadata, not only the ready bit, before returning to UI. */
            s_uv.ready=0;
            s_uv.triangles=0;
            s_has_face_colors=0;
            s_loaded=0;
            s_original_triangle_count=0;
            s_chunked=0;
            s_drawing_chunk=0;
            s_triangle_count=0;
            return; /* fail closed if NitroFS data changed after opening */
        }
        s_uv.ready=1;
        s_uv.triangles=s_chunk_stream.chunks[i].triangles;
        s_has_face_colors=1;
        s_triangle_count=(int)s_chunk_stream.chunks[i].triangles;
        s_drawing_chunk=1;
        previewStreamDrawRange(0,s_triangle_count,0,0);
        s_drawing_chunk=0;
    }
    s_triangle_count=total;
}
void previewStreamDrawMode(int texture_width,int texture_height) {
    if(s_chunked){
        /* Original texture samplers are still experimental; this chunk path
         * deliberately ignores requested texture dimensions. */
        previewStreamDraw();
    }else{
        previewStreamDrawRange(0,s_triangle_count,texture_width,texture_height);
    }
}
