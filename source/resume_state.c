#include "resume_state.h"
#include "dex_search.h"
#include "photo_album.h"
#include "records.h"
#include <stdio.h>
#include <string.h>
#define P3RV_V1_SIZE 32u
#define P3RV_V2_SIZE 48u
static unsigned r16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
static uint32_t r32(const unsigned char *p){
    return (uint32_t)r16(p)|((uint32_t)r16(p+2)<<16);
}
static void w16(unsigned char *p,unsigned n){
    p[0]=(unsigned char)n;p[1]=(unsigned char)(n>>8);
}
static void w32(unsigned char *p,uint32_t n){
    w16(p,n);w16(p+2,n>>16);
}
static uint32_t checksum(const unsigned char *p,unsigned n){
    uint32_t crc=0xffffffffu;
    for(unsigned i=0;i<n;i++){
        crc^=p[i];
        for(unsigned k=0;k<8;k++)
            crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
    }
    return crc^0xffffffffu;
}
int p3dResumeStateValid(const P3DResumeState *s){
    return s&&s->home<=1&&s->page<P3D_PAGE_COUNT &&
        s->highlight<P3D_MENU_MAX&&s->records_tab<=2&&
        s->dex<649&&s->move<559&&s->selected_dex<649&&
        s->album_page<=999&&s->album_selected<P3D_ALBUM_PAGE_MAX&&
        s->records_recent_cursor<P3D_RECORD_RECENT&&
        s->move_show_effect<=1&&s->search_region<P3D_DEX_REGIONS&&
        s->search_scope<P3D_DEX_SCOPE_COUNT&&
        s->search_field<=P3D_DEX_SEARCH_DESCRIPTION&&
        s->favorite_cursor<P3D_FAVORITES_MAX&&
        s->move_text_offset<=4096;
}
static int file_path(char path[256],const char *base,int slot){
    int n;
    if(!base||!*base)return 0;
    n=snprintf(path,256,"%s_resume_%c.sav",base,slot?'B':'A');
    return n>0&&n<256;
}
static void pack(unsigned char b[P3RV_V2_SIZE],const P3DResumeState *s,uint32_t seq){
    memset(b,0,P3RV_V2_SIZE);
    memcpy(b,"P3RV",4);b[4]=2;
    w32(b+8,seq);
    b[12]=s->home;b[13]=s->page;b[14]=s->highlight;b[15]=s->records_tab;
    w16(b+16,s->dex);w16(b+18,s->move);
    w16(b+20,s->selected_dex);w16(b+22,s->album_page);
    w16(b+24,s->selected_form);
    b[26]=s->album_selected;b[27]=s->records_recent_cursor;
    b[28]=s->move_show_effect;b[29]=s->search_region;
    b[30]=s->search_scope;b[31]=s->search_field;
    w16(b+32,s->move_text_offset);
    w16(b+34,s->menu_cursor);
    b[36]=s->favorite_cursor;
    w32(b+44,checksum(b,44));
}
static int unpack(const unsigned char *b,unsigned size,
                  P3DResumeState *s,uint32_t *seq){
    unsigned version, crc_offset;
    if(size<P3RV_V1_SIZE||memcmp(b,"P3RV",4)!=0||
       b[5]!=0||r16(b+6)!=0)return 0;
    version=b[4];
    if(version==1 && size==P3RV_V1_SIZE && r32(b+24)==0){
        crc_offset=28;
    }else if(version==2 && size==P3RV_V2_SIZE){
        for(unsigned i=37;i<44;i++)if(b[i]!=0)return 0;
        crc_offset=44;
    }else return 0;
    if(r32(b+crc_offset)!=checksum(b,crc_offset))return 0;
    memset(s,0,sizeof(*s));
    *seq=r32(b+8);s->home=b[12];s->page=b[13];
    s->highlight=b[14];s->records_tab=b[15];
    s->dex=(uint16_t)r16(b+16);s->move=(uint16_t)r16(b+18);
    s->selected_dex=(uint16_t)r16(b+20);s->album_page=(uint16_t)r16(b+22);
    if(version==2){
        s->selected_form=(uint16_t)r16(b+24);
        s->album_selected=b[26];s->records_recent_cursor=b[27];
        s->move_show_effect=b[28];s->search_region=b[29];
        s->search_scope=b[30];s->search_field=b[31];
        s->move_text_offset=(uint16_t)r16(b+32);
        s->menu_cursor=(uint16_t)r16(b+34);
        s->favorite_cursor=b[36];
    }
    return p3dResumeStateValid(s);
}
static int read_slot(const char *base,int slot,P3DResumeState *out,uint32_t *seq){
    char name[256];unsigned char b[P3RV_V2_SIZE];FILE *f;unsigned size;int ok;
    if(!file_path(name,base,slot)||(f=fopen(name,"rb"))==NULL)return 0;
    size=(unsigned)fread(b,1,P3RV_V2_SIZE,f);
    ok=!ferror(f)&&fgetc(f)==EOF&&!ferror(f);
    fclose(f);
    return ok&&unpack(b,size,out,seq);
}
static int newer(uint32_t a,uint32_t b){
    uint32_t delta=a-b;
    return delta!=0u&&delta<0x80000000u;
}
int p3dResumeLoad(const char *base,P3DResumeState *out){
    P3DResumeState a,b;uint32_t sa=0,sb=0;int va,vb;
    if(!out)return 0;
    va=read_slot(base,0,&a,&sa);vb=read_slot(base,1,&b,&sb);
    if(!va&&!vb)return 0;
    *out=va&&(!vb||!newer(sb,sa))?a:b;
    return 1;
}
int p3dResumeStore(const char *base,const P3DResumeState *s){
    P3DResumeState a,b;uint32_t sa=0,sb=0,seq=1;
    int va,vb,slot;char name[256];unsigned char bytes[P3RV_V2_SIZE];FILE *f;
    if(!p3dResumeStateValid(s))return 0;
    va=read_slot(base,0,&a,&sa);vb=read_slot(base,1,&b,&sb);
    if(va&&vb){
        int active=newer(sb,sa)?1:0;
        slot=1-active;seq=(active?sb:sa)+1;
    }else if(va){slot=1;seq=sa+1;}
    else if(vb){slot=0;seq=sb+1;}
    else slot=0;
    if(!file_path(name,base,slot))return 0;
    pack(bytes,s,seq);
    f=fopen(name,"wb");if(!f)return 0;
    if(fwrite(bytes,1,P3RV_V2_SIZE,f)!=P3RV_V2_SIZE||fflush(f)!=0){
        fclose(f);return 0;
    }
    return fclose(f)==0;
}
int p3dResumeApply(const P3DResumeState *s,P3DCapabilities caps,
                   int *home,P3DMenu *menu,int *highlight){
    if(!p3dResumeStateValid(s)||!home||!menu||!highlight)return 0;
    /* Old P3RV saves may refer to a longer development menu. */
    size_t entries=p3dMenuEntries(caps,NULL);
    *highlight=s->highlight<entries?s->highlight:(int)(entries-1);
    if(s->home){*home=1;return 1;}
    if(s->page==P3D_PAGE_AR&&!p3dCanEnterFeature(caps,P3D_FEATURE_AR)){
        *home=1;return 1;
    }
    if(s->page==P3D_PAGE_HOME){*home=1;return 1;}
    if(!p3dMenuEnter(menu,caps,(P3DPage)s->page)){
        *home=1;return 1;
    }
    *home=0;
    menu->selected_dex=s->selected_dex;
    menu->cursor=s->menu_cursor;
    /* Favorites list comes from P3SV. Never restore a cursor beyond it. */
    menu->favorite_cursor=(menu->favorites_count>0&&
        s->favorite_cursor<(unsigned)menu->favorites_count)
        ?s->favorite_cursor:0;
    return 1;
}
int p3dResumeRestoreBoot(const char *base,P3DResumeState *restored,
                         P3DCapabilities caps,int *home,
                         P3DMenu *menu,int *highlight){
    P3DResumeState checkpoint;
    if(!restored||!p3dResumeLoad(base,&checkpoint)||
       !p3dResumeApply(&checkpoint,caps,home,menu,highlight))
        return 0;
    *restored=checkpoint;
    return 1;
}
