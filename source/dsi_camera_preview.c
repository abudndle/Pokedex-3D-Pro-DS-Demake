#include "dsi_camera_preview.h"
#include <string.h>
/* Preserve exact sensor pixels, centered without cropping or speculative
 * color correction. A future hardware bridge owns VRAM allocation/upload. */
int p3dCameraPreviewStage(const P3DCameraFrame *f,
                          uint16_t *dest,size_t count){
    size_t left,top,y;
    const unsigned char *src;
    if(!f || !dest || count<P3D_PREVIEW_PIXELS ||
       !p3dCameraFrameValid(f))return 0;
    /* Separate source and staging buffers are required; explicitly reject
     * overlap, including a source entirely contained within the destination. */
    {
        uintptr_t src_start=(uintptr_t)f->pixels;
        uintptr_t dst_start=(uintptr_t)dest;
        size_t source_size=f->bytes, output_size=P3D_PREVIEW_PIXELS*sizeof(uint16_t);
        if(source_size>UINTPTR_MAX-src_start ||
           output_size>UINTPTR_MAX-dst_start)return 0;
        if(src_start<dst_start+output_size &&
           dst_start<src_start+source_size)return 0;
    }
    memset(dest,0,P3D_PREVIEW_PIXELS*sizeof(*dest));
    left=(P3D_PREVIEW_WIDTH-f->width)/2u;
    top=(P3D_PREVIEW_HEIGHT-f->height)/2u;
    src=(const unsigned char *)f->pixels;
    for(y=0;y<f->height;y++){
        size_t x;
        const unsigned char *row=src+y*f->stride_bytes;
        uint16_t *dstrow=dest+(top+y)*P3D_PREVIEW_WIDTH+left;
        for(x=0;x<f->width;x++){
            /* Little-endian RGB565 in the capture contract. */
            dstrow[x]=(uint16_t)((unsigned)row[x*2u]|
                                 ((unsigned)row[x*2u+1u]<<8));
        }
    }
    return 1;
}
