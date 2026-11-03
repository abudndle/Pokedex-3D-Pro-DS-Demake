#include "dsi_camera_preview.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void){
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
