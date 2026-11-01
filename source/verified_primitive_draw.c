#include "verified_primitive_draw.h"
#ifdef C7_TEST_HOST
/* Host fixtures check the GL call sequence without DS hardware. */
extern void p3dTestBegin(int mode);
extern void p3dTestVertex(int16_t x,int16_t y,int16_t z);
extern void p3dTestEnd(void);
#define P3D_BEGIN() p3dTestBegin(0)
#define P3D_VERTEX(v) p3dTestVertex((v)[0],(v)[1],(v)[2])
#define P3D_END() p3dTestEnd()
#else
#include <nds.h>
#define P3D_BEGIN() glBegin(GL_TRIANGLES)
#define P3D_VERTEX(v) glVertex3v16((v16)(v)[0],(v16)(v)[1],(v16)(v)[2])
#define P3D_END() glEnd()
#endif
static int draw_triangle(void *context,uint16_t mesh,
    const int16_t *a,const int16_t *b,const int16_t *c){
    (void)context;(void)mesh;
    P3D_VERTEX(a);P3D_VERTEX(b);P3D_VERTEX(c);
    return 1;
}
static int accept_triangle(void *context,uint16_t mesh,
    const int16_t *a,const int16_t *b,const int16_t *c){
    (void)context;(void)mesh;(void)a;(void)b;(void)c;
    return 1;
}
int p3dVerifiedPrimitiveDraw(const uint8_t *indices,size_t size,
    uint16_t model,const P3DPrimitiveVertices *meshes,size_t mesh_count,
    uint32_t *drawn_triangles){
    uint32_t validated=0,drawn=0;
    if(drawn_triangles)*drawn_triangles=0;
    /* Validate all triangles before opening a GL primitive. */
    if(!p3dVerifiedPrimitiveBridge(indices,size,model,meshes,mesh_count,
        accept_triangle,0,&validated)||!validated)return 0;
    P3D_BEGIN();
    int ok=p3dVerifiedPrimitiveBridge(indices,size,model,meshes,mesh_count,
        draw_triangle,0,&drawn);
    P3D_END();
    if(!ok||drawn!=validated)return 0;
    if(drawn_triangles)*drawn_triangles=drawn;
    return 1;
}
