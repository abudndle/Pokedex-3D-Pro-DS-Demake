#include "verified_primitive_uv_draw.h"
#include <nds.h>
static int draw_triangle(void *context,uint16_t mesh,
    const P3DPrimitiveUvVertex *a,const P3DPrimitiveUvVertex *b,
    const P3DPrimitiveUvVertex *c){
    int *started=context;
    (void)mesh;
    if(!*started){
        glBegin(GL_TRIANGLES);
        *started=1;
    }
    glTexCoord2t16((t16)a->u,(t16)a->v);glVertex3v16((v16)a->xyz[0],(v16)a->xyz[1],(v16)a->xyz[2]);
    glTexCoord2t16((t16)b->u,(t16)b->v);glVertex3v16((v16)b->xyz[0],(v16)b->xyz[1],(v16)b->xyz[2]);
    glTexCoord2t16((t16)c->u,(t16)c->v);glVertex3v16((v16)c->xyz[0],(v16)c->xyz[1],(v16)c->xyz[2]);
    return 1;
}
int p3dVerifiedPrimitiveUvDraw(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,uint32_t *drawn_triangles){
    int started=0;
    if(drawn_triangles)*drawn_triangles=0;
    /* The bridge preflights the entire pair before the first callback. */
    int ok=p3dVerifiedPrimitiveUvBridge(geometry,uv,draw_triangle,&started);
    if(started)glEnd();
    if(!ok)return 0;
    if(drawn_triangles)*drawn_triangles=geometry->triangles;
    return 1;
}
