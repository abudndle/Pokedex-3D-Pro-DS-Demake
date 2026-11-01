#include "search_touch.h"
#include <assert.h>
#include <stdio.h>
int main(void){
    assert(p3dSearchTouchAction(-1,95)==0);
    assert(p3dSearchTouchAction(256,95)==0);
    assert(p3dSearchTouchAction(10,88)==P3D_SEARCH_TOUCH_REGION);
    assert(p3dSearchTouchAction(127,103)==P3D_SEARCH_TOUCH_REGION);
    assert(p3dSearchTouchAction(128,88)==P3D_SEARCH_TOUCH_SCOPE);
    assert(p3dSearchTouchAction(1,104)==P3D_SEARCH_TOUCH_FIELD);
    assert(p3dSearchTouchAction(200,119)==P3D_SEARCH_TOUCH_FIELD);
    assert(p3dSearchTouchAction(16,144)=='A');
    assert(p3dSearchTouchAction(31,159)=='A');
    assert(p3dSearchTouchAction(32,144)=='B');
    assert(p3dSearchTouchAction(223,159)=='M');
    assert(p3dSearchTouchAction(16,160)=='N');
    assert(p3dSearchTouchAction(223,175)=='Z');
    assert(p3dSearchTouchAction(15,144)==0);
    assert(p3dSearchTouchAction(224,170)==0);
    assert(p3dSearchTouchAction(30,176)==P3D_SEARCH_TOUCH_BACKSPACE);
    assert(p3dSearchTouchAction(72,176)==P3D_SEARCH_TOUCH_NEXT);
    assert(p3dSearchTouchAction(159,191)==P3D_SEARCH_TOUCH_NEXT);
    assert(p3dSearchTouchAction(160,176)==P3D_SEARCH_TOUCH_PREVIOUS);
    assert(p3dSearchTouchAction(255,191)==P3D_SEARCH_TOUCH_PREVIOUS);
    assert(p3dSearchTouchAction(0,192)==0);
    assert(p3dSearchTouchAction(0,142)==0);
    /* Test actual rendered glyph positions through shared one-based rows. */
    assert(p3dSearchTouchAction(0,(P3D_SEARCH_REGION_ROW-1)*8)==P3D_SEARCH_TOUCH_REGION);
    assert(p3dSearchTouchAction(128,(P3D_SEARCH_REGION_ROW-1)*8)==P3D_SEARCH_TOUCH_SCOPE);
    assert(p3dSearchTouchAction(0,(P3D_SEARCH_FIELD_ROW-1)*8)==P3D_SEARCH_TOUCH_FIELD);
    for(int row=0;row<2;row++)for(int col=0;col<13;col++){
        int y=(P3D_SEARCH_KEYBOARD_ROW-1)*8+row*16;
        assert(p3dSearchTouchAction(16+col*16,y)=='A'+row*13+col);
        assert(p3dSearchTouchAction(31+col*16,y+15)=='A'+row*13+col);
    }
    assert(p3dSearchTouchAction(0,(P3D_SEARCH_ACTIONS_ROW-1)*8)==P3D_SEARCH_TOUCH_BACKSPACE);
    assert(p3dSearchTouchAction(100,(P3D_SEARCH_RESULT_ROW-1)*8)==0);
    assert(p3dSearchTouchAction(100,128)==0); /* B hint is outside all targets. */
    puts("C83 text-mode touch keyboard bounds and all 26 letters: PASS");
    return 0;
}
