#include "dsi_camera_session.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct {
    int opens,reads,closes,fail_open,fail_read,bad_frame;
    unsigned short pixels[256*192];
} Fake;
static int open_cam(void *p){Fake *f=p;f->opens++;return !f->fail_open;}
static int read_cam(void *p,P3DCameraFrame *frame){
    Fake *f=p;f->reads++;
    if(f->fail_read)return 0;
    frame->pixels=f->pixels;frame->width=256;frame->height=192;
    frame->format=P3D_CAMERA_RGB565;frame->stride_bytes=f->bad_frame?1:512;
    frame->bytes=sizeof(f->pixels);return 1;
}
static void close_cam(void *p){((Fake *)p)->closes++;}
int main(void){
    P3DCameraSession s;P3DCameraFrame f;Fake fake={0};
    P3DCameraBackend b={open_cam,read_cam,close_cam,&fake};
    p3dCameraSessionInit(&s);
    assert(s.state==P3D_CAMERA_UNAVAILABLE);
    assert(!p3dCameraSessionOpen(&s,0,b) && fake.opens==0);
    assert(s.state==P3D_CAMERA_UNAVAILABLE);
    assert(!p3dCameraSessionRead(&s,&f));
    assert(p3dCameraSessionOpen(&s,1,b));
    assert(!p3dCameraSessionOpen(&s,1,b));
    assert(fake.opens==1 && s.state==P3D_CAMERA_OPEN);
    assert(p3dCameraSessionRead(&s,&f) && s.state==P3D_CAMERA_STREAMING);
    assert(s.frames_received==1 && f.width==256);
    assert(!p3dCameraSessionOpen(&s,0,b));
    assert(fake.closes==1 && s.state==P3D_CAMERA_UNAVAILABLE);
    fake.fail_open=1;
    assert(!p3dCameraSessionOpen(&s,1,b) && s.state==P3D_CAMERA_ERROR);
    assert(fake.closes==2);
    fake.fail_open=0;
    assert(p3dCameraSessionOpen(&s,1,b));
    fake.bad_frame=1;
    assert(!p3dCameraSessionRead(&s,&f) && s.state==P3D_CAMERA_ERROR);
    assert(fake.closes==3 && f.pixels==NULL);
    fake.bad_frame=0;
    assert(p3dCameraSessionOpen(&s,1,b));
    fake.fail_read=1;
    assert(!p3dCameraSessionRead(&s,&f) && fake.closes==4);
    p3dCameraSessionClose(&s);
    assert(fake.closes==4 && s.state==P3D_CAMERA_CLOSED);
    assert(!p3dCameraFrameValid(NULL));
    memset(&f,0,sizeof(f));f.pixels=fake.pixels;f.width=256;f.height=192;
    f.stride_bytes=512;f.bytes=sizeof(fake.pixels);f.format=P3D_CAMERA_RGB565;
    assert(p3dCameraFrameValid(&f));
    f.bytes--;assert(!p3dCameraFrameValid(&f));
    f.bytes=sizeof(fake.pixels);f.width=257;assert(!p3dCameraFrameValid(&f));
    f.width=256;f.stride_bytes=0;assert(!p3dCameraFrameValid(&f));
    f.stride_bytes=512;f.format=(P3DCameraFormat)99;assert(!p3dCameraFrameValid(&f));
    puts("C337: DSi-only camera lifecycle/preview frame guards: PASS (synthetic backend)");
    return 0;
}
