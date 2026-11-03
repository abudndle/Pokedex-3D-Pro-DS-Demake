#include "dsi_camera_session.h"
#include <string.h>
/* Bounds represent a conservative DS-capable preview, not raw sensor limits. */
#define P3D_FRAME_MAX_WIDTH 256u
#define P3D_FRAME_MAX_HEIGHT 192u
#define P3D_FRAME_MAX_BYTES (P3D_FRAME_MAX_WIDTH*P3D_FRAME_MAX_HEIGHT*2u)
void p3dCameraSessionInit(P3DCameraSession *s){
    if(!s)return;
    memset(s,0,sizeof(*s));
    s->state=P3D_CAMERA_UNAVAILABLE;
}
int p3dCameraFrameValid(const P3DCameraFrame *f){
    size_t line,required;
    if(!f || !f->pixels || f->format!=P3D_CAMERA_RGB565 ||
       !f->width || !f->height || f->width>P3D_FRAME_MAX_WIDTH ||
       f->height>P3D_FRAME_MAX_HEIGHT || (f->stride_bytes&1u))return 0;
    line=(size_t)f->width*2u;
    if((size_t)f->stride_bytes<line)return 0;
    required=((size_t)f->height-1u)*f->stride_bytes+line;
    return required<=P3D_FRAME_MAX_BYTES && f->bytes>=required;
}
void p3dCameraSessionClose(P3DCameraSession *s){
    if(!s)return;
    if(s->owns_device && s->backend.close)s->backend.close(s->backend.ctx);
    memset(&s->backend,0,sizeof(s->backend));
    s->owns_device=0;
    s->frames_received=0;
    s->state=P3D_CAMERA_CLOSED;
}
int p3dCameraSessionOpen(P3DCameraSession *s,int is_dsi,P3DCameraBackend b){
    if(!s)return 0;
    /* Never call a hardware callback unless the caller confirmed DSi mode. */
    if(!is_dsi){
        if(s->owns_device)p3dCameraSessionClose(s);
        s->state=P3D_CAMERA_UNAVAILABLE;
        return 0;
    }
    if(s->owns_device)return 0; /* no double opens or lost ownership */
    s->state=P3D_CAMERA_CLOSED;
    if(!b.open || !b.read || !b.close)return 0;
    s->backend=b;
    if(!b.open(b.ctx)){
        /* Failed init may have partially enabled hardware; require cleanup. */
        b.close(b.ctx);
        memset(&s->backend,0,sizeof(s->backend));
        s->state=P3D_CAMERA_ERROR;
        return 0;
    }
    s->owns_device=1;
    s->state=P3D_CAMERA_OPEN;
    return 1;
}
int p3dCameraSessionRead(P3DCameraSession *s,P3DCameraFrame *out){
    P3DCameraFrame temp;
    if(out)memset(out,0,sizeof(*out));
    if(!s || !out || !s->owns_device ||
       (s->state!=P3D_CAMERA_OPEN && s->state!=P3D_CAMERA_STREAMING))
        return 0;
    memset(&temp,0,sizeof(temp));
    if(!s->backend.read(s->backend.ctx,&temp) || !p3dCameraFrameValid(&temp)){
        p3dCameraSessionClose(s);
        s->state=P3D_CAMERA_ERROR;
        return 0;
    }
    *out=temp;
    s->state=P3D_CAMERA_STREAMING;
    s->frames_received++;
    return 1;
}
