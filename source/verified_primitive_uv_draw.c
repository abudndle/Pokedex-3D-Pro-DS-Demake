#include "verified_primitive_uv_draw.h"
#ifndef C7_TEST_HOST
#include <nds.h>
static int draw_triangle(void *context,uint16_t mesh,
    const P3DPrimitiveUvVertex *a,const P3DPrimitiveUvVertex *b,
    const P3DPrimitiveUvVertex *c){
    (void)context;(void)mesh;
    glTexCoord2t16((t16)a->u,(t16)a->v);glVertex3v16((v16)a->xyz[0],(v16)a->xyz[1],(v16)a->xyz[2]);
    glTexCoord2t16((t16)b->u,(t16)b->v);glVertex3v16((v16)b->xyz[0],(v16)b->xyz[1],(v16)b->xyz[2]);
    glTexCoord2t16((t16)c->u,(t16)c->v);glVertex3v16((v16)c->xyz[0],(v16)c->xyz[1],(v16)c->xyz[2]);
    return 1;
}
#else
extern int p3dTestUvTriangle(uint16_t mesh,
    const P3DPrimitiveUvVertex *a,const P3DPrimitiveUvVertex *b,
    const P3DPrimitiveUvVertex *c);
static int draw_triangle(void *context,uint16_t mesh,
    const P3DPrimitiveUvVertex *a,const P3DPrimitiveUvVertex *b,
    const P3DPrimitiveUvVertex *c){
    (void)context;return p3dTestUvTriangle(mesh,a,b,c);
}
#endif
int p3dVerifiedPrimitiveUvDraw(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,uint32_t *drawn_triangles){
    if(drawn_triangles)*drawn_triangles=0;
    if(!geometry||!uv||!geometry->ready||!uv->ready)return 0;
#ifndef C7_TEST_HOST
    glBegin(GL_TRIANGLES);
#endif
    int ok=p3dVerifiedPrimitiveUvBridge(geometry,uv,draw_triangle,0);
#ifndef C7_TEST_HOST
    glEnd();
#endif
    if(!ok)return 0;
    if(drawn_triangles)*drawn_triangles=geometry->triangles;
    return 1;
}
