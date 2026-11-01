#include "resume_state.h"
#include "title_idle.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
int main(int argc,char **argv){
    P3DResumeState a={0},loaded;
    P3DTitleIdle idle;
    P3DCapabilities ds=p3dCapabilities(0,0,0);
    P3DCapabilities dsi=p3dCapabilities(1,1,1);
    P3DMenu menu;
    int home=1,highlight=0;
    char path[260],clock[80];
    assert(argc==2);
    assert(!p3dResumeLoad(argv[1],&loaded));
    assert(!p3dResumeRestoreBoot(argv[1],&loaded,ds,&home,&menu,
                                 &highlight));
    /* No valid checkpoint: the original 3DS title is allowed at boot. */
    a.home=0;a.page=P3D_PAGE_DEX;a.highlight=3;
    a.records_tab=2;a.dex=24;a.move=7;a.selected_dex=24;a.album_page=5;
    assert(p3dResumeStateValid(&a));
    assert(p3dResumeStore(argv[1],&a));
    assert(p3dResumeLoad(argv[1],&loaded));
    assert(loaded.dex==24 && loaded.page==P3D_PAGE_DEX);
    /* Reset must enter the saved Pokédex page directly, regardless of
     * whether legacy progress data was created with this checkpoint. */
    p3dMenuReset(&menu);home=1;
    assert(p3dResumeRestoreBoot(argv[1],&loaded,ds,&home,&menu,&highlight));
    assert(!home && menu.page==P3D_PAGE_DEX && loaded.dex==24);
    p3dMenuReset(&menu);
    assert(p3dResumeApply(&loaded,ds,&home,&menu,&highlight));
    assert(!home && menu.page==P3D_PAGE_DEX && highlight==3);
    assert(menu.selected_dex==24);
    a.page=P3D_PAGE_RECORDS;a.dex=25;
    assert(p3dResumeStore(argv[1],&a));
    assert(p3dResumeLoad(argv[1],&loaded));
    assert(loaded.dex==25 && loaded.page==P3D_PAGE_RECORDS);
    a.page=P3D_PAGE_MOVES;a.move=100;
    assert(p3dResumeStore(argv[1],&a));
    assert(p3dResumeLoad(argv[1],&loaded));
    assert(loaded.move==100);
    p3dMenuReset(&menu);home=1;
    assert(p3dResumeRestoreBoot(argv[1],&loaded,ds,&home,&menu,&highlight));
    assert(!home && menu.page==P3D_PAGE_MOVES && loaded.move==100);
    /* Corrupt latest A slot; older valid B slot remains recoverable. */
    assert(snprintf(path,sizeof(path),"%s_resume_A.sav",argv[1])>0);
    FILE *f=fopen(path,"wb");
    assert(f);
    assert(fwrite("bad",1,3,f)==3);
    assert(fclose(f)==0);
    assert(p3dResumeLoad(argv[1],&loaded));
    assert(loaded.page==P3D_PAGE_RECORDS && loaded.dex==25);
    p3dMenuReset(&menu);home=1;
    assert(p3dResumeRestoreBoot(argv[1],&loaded,ds,&home,&menu,&highlight));
    assert(!home && menu.page==P3D_PAGE_RECORDS);
    assert(loaded.dex==25);
    a.page=P3D_PAGE_AR;
    assert(p3dResumeStore(argv[1],&a));
    assert(p3dResumeLoad(argv[1],&loaded));
    assert(loaded.page==P3D_PAGE_AR);
    p3dMenuReset(&menu);home=0;
    assert(p3dResumeApply(&loaded,ds,&home,&menu,&highlight));
    assert(home); /* disabled DSi camera cannot be reopened on DS */
    p3dMenuReset(&menu);home=1;
    assert(p3dResumeApply(&loaded,dsi,&home,&menu,&highlight));
    assert(!home && menu.page==P3D_PAGE_AR);
    a.page=P3D_PAGE_COUNT;
    assert(!p3dResumeStateValid(&a));
    assert(!p3dResumeStore(argv[1],&a));
    assert(!p3dResumeApply(&a,ds,&home,&menu,&highlight));
    assert(!p3dResumeStore(NULL,&loaded));
    p3dTitleIdleReset(&idle);
    assert(!idle.active && !idle.ticks);
    for(unsigned i=1;i<P3D_TITLE_IDLE_TICKS;i++)
        assert(!p3dTitleIdleAdvance(&idle));
    assert(!idle.active);
    assert(p3dTitleIdleAdvance(&idle));
    assert(idle.active);
    assert(!p3dTitleIdleAdvance(&idle));
    assert(p3dTitleIdleClock(clock,sizeof(clock),time(NULL)));
    assert(strlen(clock)>=12);
    assert(!p3dTitleIdleClock(clock,3,time(NULL)));
    assert(!p3dTitleIdleClock(NULL,0,time(NULL)));
    p3dTitleIdleReset(&idle);
    assert(!idle.active && !idle.ticks);
    /* C120: idle can pick ANY Pokédex species without looking at the
     * resumed/saved Dex entry (which remains intact until idle A is used). */
    {
        unsigned char seen[P3D_TITLE_POKEDEX_COUNT]={0};
        unsigned covered=0;
        P3DTitleIdle first,second;
        for(uint32_t seed=1;seed<=20000;seed++){
            p3dTitleIdleReset(&first);
            p3dTitleIdleSeed(&first,seed);
            unsigned species=p3dTitleIdleChooseSpecies(&first);
            assert(species<P3D_TITLE_POKEDEX_COUNT);
            if(!seen[species]){seen[species]=1;covered++;}
        }
        assert(covered==P3D_TITLE_POKEDEX_COUNT);
        p3dTitleIdleReset(&first);
        p3dTitleIdleReset(&second);
        p3dTitleIdleSeed(&first,0x12345678u);
        p3dTitleIdleSeed(&second,0x12345678u);
        /* Different saved Pokédex entries do not influence idle species. */
        a.dex=1;
        unsigned one=p3dTitleIdleChooseSpecies(&first);
        a.dex=648;
        unsigned two=p3dTitleIdleChooseSpecies(&second);
        assert(one==two);
        assert(a.dex==648);
        assert(!p3dTitleIdleSceneDue(&first)); /* inactive title */
        first.active=1;
        for(unsigned i=1;i<P3D_TITLE_SCENE_TICKS;i++)
            assert(!p3dTitleIdleSceneDue(&first));
        assert(p3dTitleIdleSceneDue(&first));
        unsigned previous=first.species;
        unsigned next=p3dTitleIdleChooseSpecies(&first);
        assert(next<P3D_TITLE_POKEDEX_COUNT && next!=previous);
        assert(!first.scene_ticks);
        for(unsigned i=0;i<10000;i++){
            previous=next;
            next=p3dTitleIdleChooseSpecies(&first);
            assert(next!=previous && next<P3D_TITLE_POKEDEX_COUNT);
        }
        assert(!p3dTitleIdleSceneDue(NULL));
        assert(p3dTitleIdleChooseSpecies(NULL)==0);
        p3dTitleIdleReset(&first);
        assert(!first.active && !first.has_species);
    }
    puts("C120 independent full-Pokédex title scenes, resume and RTC: PASS");
    return 0;
}
