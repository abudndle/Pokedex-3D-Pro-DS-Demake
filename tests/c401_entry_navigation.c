#include "entry_navigation.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static P3DMenu fixture(void){
 P3DMenu menu;memset(&menu,0,sizeof(menu));menu.page=P3D_PAGE_RECORDS;
 menu.cursor=4;menu.selected_dex=33;menu.move_index=7;menu.move_effect=1;
 menu.move_page=56;menu.favorites_count=2;menu.favorites[0]=24;menu.favorites[1]=648;
 strcpy(menu.search_query,"EEVEE");return menu;
}
static void pokemon_opens_exact_entry(void){
 P3DMenu menu=fixture(),expected=menu;
 int dex=3,form=5,tab=3;unsigned buttons=0x400;
 assert(p3dEntryOpenPokemon(&menu,24,&dex,&form,&tab,&buttons));
 assert(menu.selected_dex==24);assert(menu.page==P3D_PAGE_DEX);
 assert(dex==24&&form==0&&tab==0&&buttons==0);
 expected.page=P3D_PAGE_DEX;expected.selected_dex=24;
 assert(memcmp(&menu,&expected,sizeof(menu))==0);
 /* An explicit reopen clears stale presentation state and consumes X.
  * Therefore the new Dex page cannot reuse that X to enter Search. */
 form=2;tab=3;buttons=0x400;
 assert(p3dEntryOpenPokemon(&menu,24,&dex,&form,&tab,&buttons));
 assert(dex==24&&form==0&&tab==0&&buttons==0);
}
static void move_reopen_resets_view(void){
 P3DMenu menu=fixture(),expected=menu;
 int move=7,offset=196,effect=1;unsigned buttons=0x100;
 assert(p3dEntryOpenMove(&menu,7,&move,&offset,&effect,&buttons));
 assert(move==7&&offset==0&&effect==0&&buttons==0);
 expected.page=P3D_PAGE_MOVES;expected.move_index=7;
 expected.move_effect=0;expected.move_page=0;
 assert(memcmp(&menu,&expected,sizeof(menu))==0);
}
static void all_targets(void){
 for(int target=0;target<649;target++){
  P3DMenu menu=fixture(),expected=menu;int dex=-1,form=1,tab=3;unsigned buttons=~0u;
  menu.page=(P3DPage)(target%P3D_PAGE_COUNT);expected=menu;
  assert(p3dEntryOpenPokemon(&menu,target,&dex,&form,&tab,&buttons));
  assert(dex==target&&form==0&&tab==0&&buttons==0);
  expected.page=P3D_PAGE_DEX;expected.selected_dex=target;
  assert(memcmp(&menu,&expected,sizeof(menu))==0);
 }
 for(int target=0;target<559;target++){
  P3DMenu menu=fixture(),expected=menu;int move=-1,offset=84,effect=1;unsigned buttons=~0u;
  menu.page=(P3DPage)(target%P3D_PAGE_COUNT);expected=menu;
  assert(p3dEntryOpenMove(&menu,target,&move,&offset,&effect,&buttons));
  assert(move==target&&offset==0&&effect==0&&buttons==0);
  expected.page=P3D_PAGE_MOVES;expected.move_index=target;expected.move_effect=0;expected.move_page=0;
  assert(memcmp(&menu,&expected,sizeof(menu))==0);
 }
}
static void rejects_atomically(void){
 for(int kind=0;kind<2;kind++)for(int bad=0;bad<17;bad++){
  P3DMenu menu=fixture(),before;
  int a=22,b=33,c=44,target=5;unsigned buttons=0x123;
  P3DMenu *mp=&menu;int *ap=&a,*bp=&b,*cp=&c;unsigned *keys=&buttons;
  switch(bad){
   case 0:target=-1;break;case 1:target=kind?559:649;break;
   case 2:mp=NULL;break;case 3:ap=NULL;break;case 4:bp=NULL;break;
   case 5:cp=NULL;break;case 6:keys=NULL;break;
   case 7:menu.page=(P3DPage)-1;break;case 8:menu.page=P3D_PAGE_COUNT;break;
   case 9:bp=ap;break;case 10:cp=bp;break;case 11:ap=&menu.selected_dex;break;
   case 12:cp=&menu.cursor;break;case 13:keys=(unsigned *)&a;break;
   case 14:cp=ap;break;case 15:keys=(unsigned *)&menu.selected_dex;break;
   case 16:bp=&menu.move_page;break;
  }
  before=menu;
  int accepted=kind?p3dEntryOpenMove(mp,target,ap,bp,cp,keys):
                    p3dEntryOpenPokemon(mp,target,ap,bp,cp,keys);
  assert(!accepted);assert(memcmp(&menu,&before,sizeof(menu))==0);
  assert(a==22&&b==33&&c==44&&buttons==0x123);
 }
}
int main(void){
 pokemon_opens_exact_entry();move_reopen_resets_view();all_targets();rejects_atomically();
 puts("C401 atomic entry opening, exact selection, reset and consumed input: PASS");return 0;
}
