#include "resume_state.h"
#include "photo_album.h"
#include "records.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static void put16(unsigned char *p,unsigned n){
    p[0]=(unsigned char)n;p[1]=(unsigned char)(n>>8);
}
static void put32(unsigned char *p,uint32_t n){
    put16(p,n);put16(p+2,n>>16);
}
static uint32_t crc(const unsigned char *p,unsigned n){
    uint32_t v=0xffffffffu;
    for(unsigned i=0;i<n;i++){
        v^=p[i];
        for(unsigned bit=0;bit<8;bit++)
            v=(v>>1)^((v&1u)?0xedb88320u:0u);
    }
    return v^0xffffffffu;
}
static void write_blob(const char *path,const unsigned char *bytes,unsigned size){
    FILE *f=fopen(path,"wb");
    assert(f!=NULL);
    assert(fwrite(bytes,1,size,f)==size);
    assert(fclose(f)==0);
}
int main(int argc,char **argv){
    P3DResumeState before={0},after;
    P3DMenu menu;
    P3DCapabilities caps=p3dCapabilities(0,0,0);
    char v3_path[300],legacy_base[280],legacy_file[320];
    unsigned char legacy[32]={0},v3[80]={0};
    int home=1,highlight=0;
    assert(argc==2);
    before.home=0;before.page=P3D_PAGE_DEX;before.highlight=4;
    before.dex=386;before.selected_dex=386;before.move=212;
    before.records_tab=1;before.album_page=17;
    before.selected_form=21;
    before.album_selected=P3D_ALBUM_PAGE_MAX-1;
    before.records_recent_cursor=P3D_RECORD_RECENT-1;
    before.move_show_effect=1;
    before.search_region=5;before.search_scope=2;before.search_field=1;
    before.move_text_offset=165;before.menu_cursor=42;
    before.favorite_cursor=2;
    assert(p3dResumeStateValid(&before));
    assert(p3dResumeStore(argv[1],&before));
    assert(p3dResumeLoad(argv[1],&after));
    assert(memcmp(&after,&before,sizeof(after))==0);
    p3dMenuReset(&menu);
    menu.favorites_count=3;
    assert(p3dResumeRestoreBoot(argv[1],&after,caps,&home,&menu,&highlight));
    assert(!home&&highlight==4&&menu.page==P3D_PAGE_DEX);
    assert(menu.cursor==42&&menu.favorite_cursor==2);
    assert(snprintf(v3_path,sizeof(v3_path),
                    "%s_resume_A.sav",argv[1])>0);
    FILE *f=fopen(v3_path,"rb");
    assert(f!=NULL);
    assert(fread(v3,1,sizeof(v3),f)==sizeof(v3));
    assert(fgetc(f)==EOF);
    assert(fclose(f)==0);
    assert(!memcmp(v3,"P3RV",4)&&v3[4]==3);
    /* Invalid in-screen cursor or Search filter must NOT be persisted. */
    before.album_selected=P3D_ALBUM_PAGE_MAX;
    assert(!p3dResumeStore(argv[1],&before));
    before.album_selected=0;
    before.search_scope=3;
    assert(!p3dResumeStore(argv[1],&before));
    before.search_scope=0;
    before.records_recent_cursor=P3D_RECORD_RECENT;
    assert(!p3dResumeStore(argv[1],&before));
    before.records_recent_cursor=0;
    before.move_show_effect=2;
    assert(!p3dResumeStore(argv[1],&before));
    before.move_show_effect=1;
    before.move_text_offset=4097;
    assert(!p3dResumeStore(argv[1],&before));
    before.move_text_offset=165;
    assert(p3dResumeStateValid(&before));

    /* Corrupt an extended field but recompute CRC: validation still fails.
     * The other original checkpoint remains a valid fallback after a
     * later write to slot B. */
    before.dex=222;
    assert(p3dResumeStore(argv[1],&before));
    v3[26]=0xff;
    put32(v3+76,crc(v3,76));
    write_blob(v3_path,v3,sizeof(v3));
    assert(p3dResumeLoad(argv[1],&after));
    assert(after.dex==222); /* Valid B survived invalid A. */

    /* Reproduce the precise 32-byte C119 P3RV version 1 disk layout.
     * The new loader must migrate every legacy page/selection without
     * interpreting its old reserved bytes as new state. */
    assert(snprintf(legacy_base,sizeof(legacy_base),
                    "%s_legacy",argv[1])>0);
    assert(snprintf(legacy_file,sizeof(legacy_file),
                    "%s_resume_A.sav",legacy_base)>0);
    memcpy(legacy,"P3RV",4);
    legacy[4]=1;
    put32(legacy+8,0xfffffffeu);
    legacy[12]=0;legacy[13]=P3D_PAGE_MOVES;
    legacy[14]=3;legacy[15]=2;
    put16(legacy+16,83);put16(legacy+18,222);
    put16(legacy+20,83);put16(legacy+22,7);
    put32(legacy+28,crc(legacy,28));
    write_blob(legacy_file,legacy,sizeof(legacy));
    assert(p3dResumeLoad(legacy_base,&after));
    assert(after.page==P3D_PAGE_MOVES&&after.dex==83&&after.move==222);
    assert(after.selected_form==0&&after.album_selected==0);
    assert(after.move_show_effect==0&&after.move_text_offset==0);
    assert(after.search_scope==0&&after.records_recent_cursor==0);
    p3dMenuReset(&menu);home=1;
    assert(p3dResumeRestoreBoot(legacy_base,&after,caps,&home,&menu,&highlight));
    assert(!home&&menu.page==P3D_PAGE_MOVES&&highlight==3);
    after.move_show_effect=1;
    assert(p3dResumeStore(legacy_base,&after));
    assert(p3dResumeLoad(legacy_base,&after));
    assert(after.move_show_effect==1);
    /* New B is preferred even across a wrapping 32-bit sequence counter. */
    assert(snprintf(v3_path,sizeof(v3_path),
                    "%s_resume_B.sav",legacy_base)>0);
    f=fopen(v3_path,"rb");assert(f);
    assert(fread(v3,1,sizeof(v3),f)==sizeof(v3));
    assert(fclose(f)==0);
    assert(v3[4]==3);
    /* Corrupt B; exact old A still restores, all extended fields default. */
    v3[5]=1; /* nonzero reserved is invalid even if other data correct */
    write_blob(v3_path,v3,sizeof(v3));
    assert(p3dResumeLoad(legacy_base,&after));
    assert(after.move_show_effect==0&&after.move==222);
    puts("C121: P3RV v3 exact in-screen resume and CRC-compatible v1 migration: PASS");
    return 0;
}
