#include "photo_png.h"
#include <string.h>
/* Keep the pinned decoder and inflater in one private translation unit.
 * Gamma correction is disabled: no libm dependency or gamma lookup heap. */
#define PNGLE_NO_GAMMA_CORRECTION
#define MINIZ_USE_UNALIGNED_LOADS_AND_STORES 0
#if defined(__GNUC__)
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wmisleading-indentation"
#pragma GCC diagnostic ignored "-Wimplicit-fallthrough"
#pragma GCC diagnostic ignored "-Wtype-limits"
#pragma GCC diagnostic ignored "-Wsign-compare"
#endif
#include "../third_party/pngle/miniz.c"
#include "../third_party/pngle/pngle.c"
#if defined(__GNUC__)
#pragma GCC diagnostic pop
#endif
typedef struct {
    uint16_t *pixels;
    unsigned width,height,drawn,dw,dh,left,top;
    int done,bad;
} PhotoDecode;
static unsigned photo_be32(const unsigned char *p){
    return ((unsigned)p[0]<<24)|((unsigned)p[1]<<16)|((unsigned)p[2]<<8)|p[3];
}
static void photo_draw(pngle_t *png,uint32_t x,uint32_t y,uint32_t w,uint32_t h,const uint8_t rgba[4]){
    PhotoDecode *d=pngle_get_user_data(png);
    if(d->bad)return;
    if(w!=1||h!=1||x!=d->drawn%d->width||y!=d->drawn/d->width||y>=d->height){
        d->bad=1;return;
    }
    d->drawn++;
    /* Nearest-neighbor scale while preserving aspect ratio; no full source
     * framebuffer exists. Blend source alpha over the black letterbox. */
    unsigned x0=(x*d->dw+d->width-1)/d->width;
    unsigned x1=((x+1)*d->dw+d->width-1)/d->width;
    unsigned y0=(y*d->dh+d->height-1)/d->height;
    unsigned y1=((y+1)*d->dh+d->height-1)/d->height;
    unsigned r=((unsigned)rgba[0]*rgba[3]+127)/255;
    unsigned g=((unsigned)rgba[1]*rgba[3]+127)/255;
    unsigned b=((unsigned)rgba[2]*rgba[3]+127)/255;
    uint16_t color=(uint16_t)(0x8000u|(r>>3)|((g>>3)<<5)|((b>>3)<<10));
    for(unsigned dy=y0;dy<y1;dy++)
        for(unsigned dx=x0;dx<x1;dx++)
            d->pixels[(dy+d->top)*256+dx+d->left]=color;
}
static void photo_done(pngle_t *png){((PhotoDecode *)pngle_get_user_data(png))->done=1;}
int p3dPhotoPngDecode(FILE *file,uint16_t pixels[256u*192u],unsigned *width,unsigned *height,P3DPhotoIdentity *identity){
    unsigned char buf[1024];size_t pending=0,total=0;int ok=0;
    uint32_t source_crc=0;
    PhotoDecode d={0};pngle_t *png=NULL;
    if(width)*width=0;
    if(height)*height=0;
    if(identity)memset(identity,0,sizeof(*identity));
    if(!file||!pixels||!width||!height||!identity)return 0;
    for(unsigned i=0;i<256u*192u;i++)pixels[i]=0x8000;
    /* Validate the actual first header before pngle can allocate a scanline. */
    if(fread(buf,1,33,file)!=33||memcmp(buf,"\x89PNG\r\n\x1a\n",8)||
       photo_be32(buf+8)!=13||memcmp(buf+12,"IHDR",4)||buf[28]!=0)goto end;
    d.width=photo_be32(buf+16);d.height=photo_be32(buf+20);
    if(!d.width||!d.height||d.width>640||d.height>480)goto end;
    d.pixels=pixels;
    if(d.width*192u>=d.height*256u){d.dw=256;d.dh=d.height*256/d.width;}
    else{d.dh=192;d.dw=d.width*192/d.height;}
    if(!d.dw)d.dw=1;
    if(!d.dh)d.dh=1;
    d.left=(256-d.dw)/2;d.top=(192-d.dh)/2;
    png=pngle_new();if(!png)goto end;
    pngle_set_user_data(png,&d);pngle_set_draw_callback(png,photo_draw);
    pngle_set_done_callback(png,photo_done);
    pending=33;total=33;
    source_crc=(uint32_t)mz_crc32(source_crc,buf,33);
    for(;;){
        int consumed=pngle_feed(png,buf,pending);
        if(consumed<0||(size_t)consumed>pending||d.bad)goto end;
        pending-=(size_t)consumed;
        if(pending)memmove(buf,buf+consumed,pending);
        if(d.done){
            if(pending||fgetc(file)!=EOF||ferror(file)||d.drawn!=d.width*d.height)goto end;
            ok=1;break;
        }
        if(pending==sizeof(buf)||total>=P3D_PHOTO_FILE_MAX)goto end;
        size_t take=sizeof(buf)-pending;
        if(take>P3D_PHOTO_FILE_MAX-total)take=P3D_PHOTO_FILE_MAX-total;
        size_t n=fread(buf+pending,1,take,file);
        if(!n||ferror(file))goto end;
        source_crc=(uint32_t)mz_crc32(source_crc,buf+pending,n);
        pending+=n;total+=n;
    }
end:
    pngle_destroy(png);
    if(ok){
        *width=d.width;*height=d.height;
        identity->checksum=source_crc;identity->bytes=(uint32_t)total;
    }
    else for(unsigned i=0;i<256u*192u;i++)pixels[i]=0x8000;
    return ok;
}
