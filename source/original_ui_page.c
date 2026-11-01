/* Native display of private, original-art-derived 256x192 RGB555 pages.
 * Source bitmap assets are intentionally not redistributed in the repository.
 */
#include "original_ui_page.h"
#include "feature_menu.h"
#include <nds.h>
#include <stdio.h>
#include <string.h>
#define PAGE_PIXELS (256u*192u)
static unsigned short page_pixels[PAGE_PIXELS];
static unsigned short top_page_pixels[PAGE_PIXELS];
static unsigned short top_overlay_pixels[PAGE_PIXELS];
static int top_overlay_ready;
static int page_ready;
static int top_page_ready;
static int title_ready;
static const char *const s_names[P3D_PAGE_COUNT]={
    [P3D_PAGE_HOME]="home",
    [P3D_PAGE_DEX]="dex",
    [P3D_PAGE_SEARCH]="search",
    [P3D_PAGE_MOVES]="moves",
    [P3D_PAGE_TYPES]="types",
    [P3D_PAGE_FAVORITES]="favorites",
    [P3D_PAGE_CHALLENGE]="challenge",
    [P3D_PAGE_SETTINGS]="settings",
    [P3D_PAGE_ALBUM]="album",
    [P3D_PAGE_AR]="ar",
    [P3D_PAGE_RECORDS]="records"
};
/* Private 3DS title artwork is a separate boot screen, not the first
 * home-menu page. Both source screens must exist or no title is shown. */
static int load_bitmap(const char *path,unsigned short *buffer){
    FILE *file=fopen(path,"rb");
    size_t count;
    if(!file)return 0;
    count=fread(buffer,sizeof(buffer[0]),PAGE_PIXELS,file);
    if(count!=PAGE_PIXELS || fgetc(file)!=EOF || ferror(file)){
        fclose(file);return 0;
    }
    fclose(file);
    return 1;
}
/* Separate main/sub video banks preserve both original source screen pages. */
static int load_page(unsigned screen,int page,unsigned short *buffer){
    char path[96];
    if(page<0 || page>=P3D_PAGE_COUNT || !s_names[page])return 0;
    snprintf(path,sizeof(path),"nitro:/ui/pages/t%u_%02d_%s.rgb555",
             screen,page,s_names[page]);
    return load_bitmap(path,buffer);
}
int p3dOriginalTitleFrameLoad(unsigned frame){
    char bottom[64],top[64];
    /* Use the existing title pair for frame zero, independently recovered
     * pairs for subsequent private original 3DS title animation frames. */
    if(frame>=16)return 0;
    if(frame==0){
        snprintf(bottom,sizeof(bottom),"nitro:/ui/title/t0_title.rgb555");
        snprintf(top,sizeof(top),"nitro:/ui/title/t1_title.rgb555");
    }else{
        snprintf(bottom,sizeof(bottom),"nitro:/ui/title/t0_%02u_title.rgb555",frame);
        snprintf(top,sizeof(top),"nitro:/ui/title/t1_%02u_title.rgb555",frame);
    }
    title_ready=0;
    page_ready=load_bitmap(bottom,page_pixels);
    top_page_ready=load_bitmap(top,top_page_pixels);
    title_ready=page_ready && top_page_ready;
    return title_ready;
}
int p3dOriginalTitleLoad(void){
    /* Reuse two page buffers to avoid another 192 KiB on the DS ARM9. */
    return p3dOriginalTitleFrameLoad(0);
}
int p3dOriginalTitleReady(void){return title_ready;}
void p3dOriginalTitleDraw(void){
    if(!title_ready)return;
    p3dOriginalTopPageDraw();
    p3dOriginalUiPageDraw();
}
int p3dOriginalUiPageLoad(int page){
    page_ready=load_page(0,page,page_pixels);
    return page_ready;
}
int p3dOriginalTopPageLoad(int page){
    top_page_ready=load_page(1,page,top_page_pixels);
    return top_page_ready;
}
/* The transparent cutout is derived from the PRIVATE 3DS UI source:
 * A1 bit 15 is 1 for original UI, 0 where BG0 3D must show through.
 * Reject an all-opaque layer: it would cover the live Pokémon entirely.
 * Reject an all-transparent layer: it would falsely imply restored UI.
 * This overlay is distinct from the opaque upper menu bitmap.
 */
int p3dOriginalTopOverlayLoad(int page){
    char path[96];
    FILE *file;
    size_t count;
    int seen_visible=0,seen_cutout=0;
    top_overlay_ready=0;
    if(page<0 || page>=P3D_PAGE_COUNT || !s_names[page])return 0;
    snprintf(path,sizeof(path),"nitro:/ui/pages/t1_%02d_%s_overlay.rgb555",
             page,s_names[page]);
    file=fopen(path,"rb");
    if(!file)return 0;
    count=fread(top_overlay_pixels,sizeof(top_overlay_pixels[0]),PAGE_PIXELS,file);
    if(count!=PAGE_PIXELS || fgetc(file)!=EOF || ferror(file)){
        fclose(file);
        return 0;
    }
    fclose(file);
    for(unsigned i=0;i<PAGE_PIXELS;i++){
        if(top_overlay_pixels[i]&0x8000u)seen_visible=1;
        else seen_cutout=1;
        if(seen_visible && seen_cutout)break;
    }
    top_overlay_ready=seen_visible && seen_cutout;
    return top_overlay_ready;
}
int p3dOriginalTopOverlayReady(void){return top_overlay_ready;}
void p3dOriginalTopOverlayDraw(void){
    if(!top_overlay_ready)return;
    unsigned short *dst=(unsigned short*)BG_BMP_RAM(0);
    /* Do NOT force bit15 opaque like standalone page art. The 3D engine
     * is displayed through bit15-clear pixels on the higher-priority BG2. */
    for(unsigned y=0;y<192;y++){
        unsigned short *row=dst+y*256;
        const unsigned short *src=top_overlay_pixels+y*256;
        for(unsigned x=0;x<256;x++)row[x]=src[x];
    }
}
int p3dOriginalTopPageReady(void){return top_page_ready;}
void p3dOriginalTopPageDraw(void){
    unsigned short *dst;
    if(!top_page_ready)return;
    dst=(unsigned short*)BG_BMP_RAM(0);
    /* Keep original source RGB555 colors. The standalone top-screen art
     * is opaque when displayed; model pages retain the 3D engine instead. */
    for(unsigned y=0;y<192;y++){
        unsigned short *row=dst+y*256;
        const unsigned short *src=top_page_pixels+y*256;
        for(unsigned x=0;x<256;x++)row[x]=(unsigned short)(src[x]|0x8000u);
    }
}
int p3dOriginalUiPageReady(void){return page_ready;}
void p3dOriginalUiPageDraw(void){
    unsigned short *dst;
    if(!page_ready)return;
    dst=(unsigned short*)BG_BMP_RAM_SUB(0);
    /* DS 16-bit bitmap backgrounds use bit 15 as the visible/opaque flag.\n     * Original RGB555 pixels may have that bit cleared: without setting it,\n     * valid artwork renders transparent on real DS hardware. */
    for(int y=0;y<192;y++) {
        unsigned short *row=dst+y*256;
        const unsigned short *src=page_pixels+(size_t)y*256;
        for(int x=0;x<256;x++)row[x]=(unsigned short)(src[x]|0x8000u);
    }
}
