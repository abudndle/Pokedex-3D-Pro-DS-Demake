#include "dsi_camera_preview.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct {
    int opens,reads,closes,fail_read,alias;
    unsigned char pixels[8];
    uint16_t *destination;
} PreviewBackend;
static int preview_open(void *ctx){
    ((PreviewBackend *)ctx)->opens++;
    return 1;
}
static int preview_read(void *ctx,P3DCameraFrame *frame){
    PreviewBackend *b=(PreviewBackend *)ctx;
    b->reads++;
    if(b->fail_read)return 0;
    frame->width=2;frame->height=2;frame->stride_bytes=4;
    frame->format=P3D_CAMERA_RGB565;
    frame->pixels=b->alias?(const void *)b->destination:(const void *)b->pixels;
    frame->bytes=8;
    return 1;
}
static void preview_close(void *ctx){((PreviewBackend *)ctx)->closes++;}
static void test_capture_transaction(void){
    PreviewBackend b={0};
    P3DCameraSession s;
    P3DCameraBackend backend={preview_open,preview_read,preview_close,&b};
    uint16_t output[P3D_PREVIEW_PIXELS];
    size_t center=((P3D_PREVIEW_HEIGHT-2u)/2u)*P3D_PREVIEW_WIDTH+
                  (P3D_PREVIEW_WIDTH-2u)/2u;
    b.pixels[0]=0x1f;b.pixels[1]=0;
    b.pixels[2]=0xe0;b.pixels[3]=7;
    b.destination=output;
    p3dCameraSessionInit(&s);
    output[0]=0x5555;
    assert(!p3dCameraCapturePreview(&s,output,P3D_PREVIEW_PIXELS));
    assert(output[0]==0x5555 && b.reads==0);
    assert(!p3dCameraSessionOpen(&s,0,backend) && b.opens==0);
    assert(p3dCameraSessionOpen(&s,1,backend));
    assert(!p3dCameraCapturePreview(&s,output,P3D_PREVIEW_PIXELS-1u));
    assert(output[0]==0x5555 && b.reads==0 && b.closes==0);
    assert(p3dCameraCapturePreview(&s,output,P3D_PREVIEW_PIXELS));
    assert(output[center]==0x001f && output[center+1u]==0x07e0);
    assert(s.state==P3D_CAMERA_STREAMING && s.frames_received==1);
    b.alias=1;
    output[0]=0x7777;
    assert(!p3dCameraCapturePreview(&s,output,P3D_PREVIEW_PIXELS));
    assert(output[0]==0x7777 && b.closes==1);
    assert(s.state==P3D_CAMERA_ERROR && !s.owns_device);
    assert(!p3dCameraCapturePreview(&s,output,P3D_PREVIEW_PIXELS));
    b.alias=0;
    assert(p3dCameraSessionOpen(&s,1,backend));
    b.fail_read=1;
    output[0]=0x8888;
    assert(!p3dCameraCapturePreview(&s,output,P3D_PREVIEW_PIXELS));
    assert(output[0]==0x8888 && b.closes==2);
    assert(s.state==P3D_CAMERA_ERROR);
    b.fail_read=0;
    assert(p3dCameraSessionOpen(&s,1,backend));
    assert(p3dCameraCapturePreview(&s,output,P3D_PREVIEW_PIXELS));
    p3dCameraSessionClose(&s);
    assert(b.closes==3 && b.opens==3);
}
int main(void){
    test_capture_transaction();
    unsigned char source[12]={0x1f,0x00, 0xe0,0x07, 0xff,0xff,
                              0x00,0xf8, 0x01,0x00, 0xaa,0xbb};
    uint16_t dst[P3D_PREVIEW_PIXELS];
    P3DCameraFrame f;
    const size_t x=(P3D_PREVIEW_WIDTH-2u)/2u;
    const size_t y=(P3D_PREVIEW_HEIGHT-2u)/2u;
    memset(&f,0,sizeof f);
    f.width=2;f.height=2;f.stride_bytes=6;
    f.format=P3D_CAMERA_RGB565;f.pixels=source;f.bytes=sizeof source;
    for(size_t i=0;i<P3D_PREVIEW_PIXELS;i++)dst[i]=0x1234;
    assert(p3dCameraPreviewStage(&f,dst,P3D_PREVIEW_PIXELS));
    assert(dst[y*P3D_PREVIEW_WIDTH+x]==0x001f);
    assert(dst[y*P3D_PREVIEW_WIDTH+x+1u]==0x07e0);
    assert(dst[(y+1u)*P3D_PREVIEW_WIDTH+x]==0xf800);
    assert(dst[(y+1u)*P3D_PREVIEW_WIDTH+x+1u]==0x0001);
    assert(dst[0]==0 && dst[P3D_PREVIEW_PIXELS-1u]==0);
    dst[0]=0x1234;
    assert(!p3dCameraPreviewStage(&f,dst,P3D_PREVIEW_PIXELS-1u));
    assert(dst[0]==0x1234);
    f.stride_bytes=2;
    assert(!p3dCameraPreviewStage(&f,dst,P3D_PREVIEW_PIXELS));
    assert(dst[0]==0x1234);
    f.stride_bytes=6;
    f.pixels=dst;
    f.bytes=P3D_PREVIEW_PIXELS*2u;
    assert(!p3dCameraPreviewStage(&f,dst,P3D_PREVIEW_PIXELS));
    assert(dst[0]==0x1234);
    puts("C338: bounded RGB565 staging, centering, padding and alias guards: PASS");
    return 0;
}
