#include <assert.h>
#include <stdint.h>
#include <nds.h>
#include <stdio.h>
#include "ds_texture_upload.h"
#include "texture_pixels.h"

static int last_format,last_w,last_h,last_id;
static int uploaded,deleted,fail_upload;
static uint16_t source_first,source_second;

void glGenTextures(int count,int *ids){
    assert(count==1);
    *ids=++last_id;
}
void glBindTexture(int target,int id){(void)target;(void)id;}
int glTexImage2D(int target,int unused1,int format,int width,int height,
                 int unused2,int params,const void *pixels){
    const uint16_t *data=(const uint16_t*)pixels;
    (void)target;(void)unused1;(void)unused2;(void)params;
    last_format=format;last_w=width;last_h=height;
    source_first=data[0];source_second=data[1];
    uploaded++;
    return !fail_upload;
}
void glDeleteTextures(int count,const int *ids){
    assert(count==1 && *ids>0);
    deleted++;
}
int main(int argc,char **argv){
    static P3DTexturePixels image;
    int id=0;
    assert(argc==3);
    /* v1 RGB555 comes from legacy samples with no defined alpha bit:
     * conversion to opaque RGB555 is intentional for backwards compatibility. */
    assert(p3dTexturePixelsLoad(&image,argv[1]));
    assert(image.version==1 && image.ready);
    assert(p3dDsTextureUpload(&image,&id));
    assert(id>0 && last_format==GL_RGB);
    assert(source_first==0x1234 && source_second==0x9234);
    assert(last_w==0 && last_h==0);
    assert(image.pixels[0]==0x1234);
    /* v2 A1RGB555 preserves source alpha without glTexImage2D
     * silently rewriting the transparent original texels. */
    assert(p3dTexturePixelsLoad(&image,argv[2]));
    assert(image.version==2 && image.ready);
    assert(p3dDsTextureUpload(&image,&id));
    assert(id>0 && last_format==GL_RGBA);
    assert(source_first==0x1234 && source_second==0x9234);
    assert(image.pixels[0]==0x1234 && image.pixels[1]==0x9234);
    /* Validation rejects unsupported source provenance. */
    image.version=3;
    id=123;
    int attempts=uploaded;
    assert(!p3dDsTextureUpload(&image,&id));
    assert(uploaded==attempts && id==0);
    image.version=2;
    image.ready=0;
    id=456;
    assert(!p3dDsTextureUpload(&image,&id));
    assert(id==0);
    image.ready=1;
    assert(!p3dDsTextureUpload(&image,NULL));
    /* Failure must delete the allocated DS GPU texture, not leak VRAM. */
    fail_upload=1;
    id=99;
    assert(!p3dDsTextureUpload(&image,&id));
    assert(id==0 && deleted==1 && uploaded==attempts+1);
    puts("C107: native original texture alpha and GL upload failure: PASS");
    return 0;
}
