#include "original_home_hotspots.h"
#include <stdio.h>
#include <string.h>
#define P3HM_BYTES (16u+P3D_ORIGINAL_HOME_ICONS*10u)
static unsigned rd16(const unsigned char *p){
    return (unsigned)p[0]|((unsigned)p[1]<<8);
}
static uint32_t rd32(const unsigned char *p){
    return (uint32_t)rd16(p)|((uint32_t)rd16(p+2)<<16);
}
static uint32_t crc32(const unsigned char *p,unsigned n){
    uint32_t value=0xffffffffu;
    for(unsigned i=0;i<n;i++){
        value^=p[i];
        for(unsigned j=0;j<8;j++)
            value=(value>>1)^((value&1u)?0xedb88320u:0u);
    }
    return value^0xffffffffu;
}
static const uint16_t original_pages[P3D_ORIGINAL_HOME_ICONS]={
    P3D_PAGE_DEX,P3D_PAGE_MOVES,P3D_PAGE_CHALLENGE,
    P3D_PAGE_RECORDS,P3D_PAGE_ALBUM,P3D_PAGE_AR,P3D_PAGE_SETTINGS
};
int p3dHomeHotspotsValidate(const P3DHomeHotspots *map){
    unsigned found=0;
    if(!map)return 0;
    for(unsigned i=0;i<P3D_ORIGINAL_HOME_ICONS;i++){
        const P3DHomeHotspot *r=&map->icons[i];
        unsigned slot=P3D_ORIGINAL_HOME_ICONS;
        if(r->x0>=r->x1||r->y0>=r->y1||
           r->x1>256||r->y1>192||
           r->x1-r->x0<8||r->y1-r->y0<8)return 0;
        for(unsigned j=0;j<P3D_ORIGINAL_HOME_ICONS;j++)
            if(r->page==original_pages[j]){slot=j;break;}
        if(slot==P3D_ORIGINAL_HOME_ICONS||(found&(1u<<slot)))return 0;
        found|=1u<<slot;
        for(unsigned j=0;j<i;j++){
            const P3DHomeHotspot *a=&map->icons[j];
            if(r->x0<a->x1&&a->x0<r->x1&&
               r->y0<a->y1&&a->y0<r->y1)return 0;
        }
    }
    return found==((1u<<P3D_ORIGINAL_HOME_ICONS)-1u);
}
int p3dHomeHotspotsLoad(P3DHomeHotspots *out,const char *path){
    unsigned char bytes[P3HM_BYTES];
    FILE *file;
    int good;
    if(!out)return 0;
    memset(out,0,sizeof(*out));
    if(!path)return 0;
    file=fopen(path,"rb");
    if(!file)return 0;
    good=fread(bytes,1,sizeof(bytes),file)==sizeof(bytes)&&
         fgetc(file)==EOF&&!ferror(file);
    fclose(file);
    if(!good||memcmp(bytes,"P3HM",4)!=0||rd16(bytes+4)!=1||
       rd16(bytes+6)!=P3D_ORIGINAL_HOME_ICONS||
       rd32(bytes+8)!=0||
       rd32(bytes+12)!=crc32(bytes+16,sizeof(bytes)-16))return 0;
    for(unsigned i=0;i<P3D_ORIGINAL_HOME_ICONS;i++){
        P3DHomeHotspot *r=&out->icons[i];
        unsigned off=16+i*10;
        r->page=(uint16_t)rd16(bytes+off);
        r->x0=(uint16_t)rd16(bytes+off+2);
        r->y0=(uint16_t)rd16(bytes+off+4);
        r->x1=(uint16_t)rd16(bytes+off+6);
        r->y1=(uint16_t)rd16(bytes+off+8);
    }
    if(!p3dHomeHotspotsValidate(out)){
        memset(out,0,sizeof(*out));
        return 0;
    }
    out->ready=1;
    return 1;
}
int p3dHomeHotspotsHit(const P3DHomeHotspots *map,int x,int y){
    if(!map||!map->ready||x<0||x>=256||y<0||y>=192)return -1;
    for(unsigned i=0;i<P3D_ORIGINAL_HOME_ICONS;i++){
        const P3DHomeHotspot *r=&map->icons[i];
        if(x>=r->x0&&x<r->x1&&y>=r->y0&&y<r->y1)
            return (int)r->page;
    }
    return -1;
}
