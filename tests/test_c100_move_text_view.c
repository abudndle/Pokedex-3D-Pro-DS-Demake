#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "move_text_view.h"
int main(void){
    P3DMove entry;
    memset(&entry,0,sizeof(entry));
    strcpy(entry.name,"Synthetic move");
    strcpy(entry.description,"Original description fixture");
    strcpy(entry.effect,"Original effect fixture");
    assert(!p3dMoveTextField(NULL,P3D_MOVE_FIELD_EFFECT));
    assert(!p3dMoveTextField(&entry,-1));
    assert(!p3dMoveTextField(&entry,2));
    assert(strcmp(p3dMoveTextField(&entry,P3D_MOVE_FIELD_DESCRIPTION),"Original description fixture")==0);
    assert(strcmp(p3dMoveTextField(&entry,P3D_MOVE_FIELD_EFFECT),"Original effect fixture")==0);
    assert(p3dMoveTextScroll(10000,entry.description,0)==0);
    assert(p3dMoveTextScroll(-100,entry.effect,-1)==0);
    assert(p3dMoveTextScroll(0,NULL,+1)==0);
    memset(entry.effect,'E',sizeof(entry.effect)-1);
    entry.effect[sizeof(entry.effect)-1]=0;
    assert(p3dMoveTextScroll(0,entry.effect,1)==28);
    assert(p3dMoveTextScroll(28,entry.effect,-1)==0);
    assert(p3dMoveTextScroll(10000,entry.effect,0)==(int)strlen(entry.effect)-84);
    assert(p3dMoveTextScroll(10000,entry.effect,1)==(int)strlen(entry.effect)-84);
    entry.effect[0]=0;
    assert(p3dMoveTextField(&entry,P3D_MOVE_FIELD_EFFECT)[0]==0);
    assert(strcmp(p3dMoveTextField(&entry,P3D_MOVE_FIELD_DESCRIPTION),"Original description fixture")==0);
    /* C101: deliberately unterminated original record, exactly one fixed
     * P3D_MOVE_TEXT_MAX buffer. Sanitizer runs must not overread it. */
    memset(entry.effect,'E',sizeof(entry.effect));
    assert(p3dMoveTextScroll(10000,entry.effect,0)==P3D_MOVE_TEXT_MAX-84);
    assert(p3dMoveTextScroll(0,entry.effect,+1)==28);
    assert(p3dMoveTextScroll(10000,entry.effect,+1)==P3D_MOVE_TEXT_MAX-84);
    entry.effect[0]=0;
    assert(p3dMoveTextScroll(10000,entry.effect,+1)==0);
    puts("C100/C101 original move effect/view helper: PASS");
    return 0;
}
