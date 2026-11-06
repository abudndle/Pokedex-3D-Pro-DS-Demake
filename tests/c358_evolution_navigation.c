#include "species_details.h"
#include "resume_state.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
 assert(argc==4);P3DSpeciesDetails d;P3DResumeState saved={0},restored;
 if(!strcmp(argv[3],"verify")){
  assert(p3dResumeLoad(argv[2],&restored));
  assert(restored.dex==648&&restored.selected_dex==648&&restored.selected_form==0);
  assert(restored.dex_detail_tab==3&&!restored.quiz_active&&!restored.album_view_active);
  puts("C358 exact evolution target and tab survive process restart: PASS");return 0;
 }
 assert(p3dSpeciesDetailsLoad(argv[1],0,2,&d));
 int dex=0,selected=0,form=2;
 assert(p3dSpeciesEvolutionTouch(&d,128,88,&dex,&selected,&form));
 assert(dex==4&&selected==4&&form==0);
 dex=0;selected=0;form=2;
 assert(p3dSpeciesEvolutionTouch(&d,255,119,&dex,&selected,&form));
 assert(dex==648&&selected==648&&form==0);
 saved.page=P3D_PAGE_DEX;saved.dex=648;saved.selected_dex=648;saved.dex_detail_tab=3;
 assert(p3dResumeStore(argv[2],&saved));
 /* A later tap cannot use the previous species/form record. */
 assert(!p3dSpeciesEvolutionTouch(&d,128,88,&dex,&selected,&form));
 assert(dex==648&&selected==648&&form==0);
 const int misses[][2]={{-1,88},{256,88},{128,87},{128,120},{128,160},{128,180}};
 for(unsigned i=0;i<sizeof(misses)/sizeof(misses[0]);i++){
  dex=0;selected=17;form=2;
  assert(!p3dSpeciesEvolutionTouch(&d,misses[i][0],misses[i][1],&dex,&selected,&form));
  assert(dex==0&&selected==17&&form==2);
 }
 dex=0;selected=17;form=1;
 assert(!p3dSpeciesEvolutionTouch(&d,128,88,&dex,&selected,&form));
 assert(dex==0&&selected==17&&form==1);form=2;
 assert(!p3dSpeciesEvolutionTouch(&d,128,88,&dex,&selected,&dex));
 assert(dex==0&&selected==17&&form==2);
 assert(!p3dSpeciesEvolutionTouch(NULL,128,88,&dex,&selected,&form));
 assert(!p3dSpeciesEvolutionTouch(&d,128,88,NULL,&selected,&form));
 P3DSpeciesDetails bad=d;bad.evolutions[0]=649;
 assert(!p3dSpeciesEvolutionTouch(&bad,128,88,&dex,&selected,&form));
 bad=d;bad.evolutions[0]=0;
 assert(!p3dSpeciesEvolutionTouch(&bad,128,88,&dex,&selected,&form));
 bad=d;bad.fields=0;
 assert(!p3dSpeciesEvolutionTouch(&bad,128,88,&dex,&selected,&form));
 bad=d;bad.evolutions[1]=649;
 assert(!p3dSpeciesEvolutionTouch(&bad,128,88,&dex,&selected,&form));
 bad=d;bad.evolutions_count=0;bad.evolutions[0]=bad.evolutions[1]=0;
 assert(p3dSpeciesDetailsValid(&bad));
 assert(!p3dSpeciesEvolutionTouch(&bad,128,88,&dex,&selected,&form));
 bad=d;bad.species=4;bad.form=999;bad.evolutions_count=1;
 bad.evolutions[0]=bad.evolutions[1]=0;dex=4;form=999;
 assert(p3dSpeciesEvolutionTouch(&bad,0,103,&dex,&selected,&form));
 assert(dex==0&&selected==0&&form==0);
 selected=17;form=2;
 bad=d;bad.evolutions_count=1;bad.evolutions[1]=0;
 assert(!p3dSpeciesEvolutionTouch(&bad,128,104,&dex,&selected,&form));
 assert(dex==0&&selected==17&&form==2);
 assert(!p3dSpeciesDetailsLoad("missing-c358-record",0,2,&bad));
 assert(!p3dSpeciesEvolutionTouch(&bad,128,88,&dex,&selected,&form));
 puts("C358 real P3SD branch navigation, stale identity and fail-closed touch bounds: PASS");
 return 0;
}
