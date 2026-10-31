/* Native display of private, original-art-derived 256x192 RGB555 pages.
 * Source bitmap assets are intentionally not redistributed in the repository.
 */
#include "original_ui_page.h"
#include <nds.h>
#include <stdio.h>
#include <string.h>
#define PAGE_PIXELS (256u*192u)
static unsigned short page_pixels[PAGE_PIXELS];
static int page_ready;
int p3dOriginalUiPageLoad(int page) {
    static const char *names[]={"home","dex","search","moves","types",
                                 "favorites","challenge","settings","album","ar"};
    char path[96];
    FILE *file;
    size_t count;
    page_ready=0;
    if(page<0 || page>=10)return 0;
    snprintf(path,sizeof(path),"nitro:/ui/pages/t0_%02d_%s.rgb555",page,names[page]);
    file=fopen(path,"rb");
    if(!file)return 0;
    count=fread(page_pixels,sizeof(page_pixels[0]),PAGE_PIXELS,file);
    if(count!=PAGE_PIXELS || fgetc(file)!=EOF){fclose(file);return 0;}
    fclose(file);
    page_ready=1;
    return 1;
}
int p3dOriginalUiPageReady(void){return page_ready;}
void p3dOriginalUiPageDraw(void){
    unsigned short *dst;
    if(!page_ready)return;
    dst=(unsigned short*)BG_BMP_RAM_SUB(0);
    for(int y=0;y<192;y++)
        dmaCopyHalfWords(3,page_pixels+(size_t)y*256,dst+y*256,256*2);
}
