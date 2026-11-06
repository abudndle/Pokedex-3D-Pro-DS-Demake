#include "search_touch.h"
#include <assert.h>
#include <stdio.h>
int main(void){
    /* libnds console H row 23 draws DEL/NEXT/PREV at y=184..191.
     * The old one-based conversion mapped the second letter row padding
     * to these actions instead, and mapped blank space above Region to Region. */
    assert(p3dSearchTouchAction(24,175)=='N');
    assert(p3dSearchTouchAction(24,183)=='N');
    assert(p3dSearchTouchAction(10,95)==0);
    assert(p3dSearchTouchAction(-1,96)==0);
    assert(p3dSearchTouchAction(256,96)==0);
    assert(p3dSearchTouchAction(10,96)==P3D_SEARCH_TOUCH_REGION);
    assert(p3dSearchTouchAction(127,111)==P3D_SEARCH_TOUCH_REGION);
    assert(p3dSearchTouchAction(128,96)==P3D_SEARCH_TOUCH_SCOPE);
    assert(p3dSearchTouchAction(255,111)==P3D_SEARCH_TOUCH_SCOPE);
    assert(p3dSearchTouchAction(1,112)==P3D_SEARCH_TOUCH_FIELD);
    assert(p3dSearchTouchAction(200,127)==P3D_SEARCH_TOUCH_FIELD);
    assert(p3dSearchTouchAction(100,128)==0);
    assert(p3dSearchTouchAction(100,151)==0);
    /* Each actual rendered glyph is eight pixels high, with 16px cells.
     * First glyph is x=24 from console column 1 plus two literal spaces. */
    for(int row=0;row<2;row++)for(int col=0;col<13;col++){
        for(int pixel=0;pixel<8;pixel++)
            assert(p3dSearchTouchAction(24+col*16,152+row*16+pixel)=='A'+row*13+col);
        assert(p3dSearchTouchAction(16+col*16,152+row*16)=='A'+row*13+col);
        assert(p3dSearchTouchAction(31+col*16,167+row*16)=='A'+row*13+col);
    }
    assert(p3dSearchTouchAction(15,152)==0);
    assert(p3dSearchTouchAction(224,176)==0);
    for(int y=184;y<192;y++){
        assert(p3dSearchTouchAction(30,y)==P3D_SEARCH_TOUCH_BACKSPACE);
        assert(p3dSearchTouchAction(71,y)==P3D_SEARCH_TOUCH_BACKSPACE);
        assert(p3dSearchTouchAction(72,y)==P3D_SEARCH_TOUCH_NEXT);
        assert(p3dSearchTouchAction(159,y)==P3D_SEARCH_TOUCH_NEXT);
        assert(p3dSearchTouchAction(160,y)==P3D_SEARCH_TOUCH_PREVIOUS);
        assert(p3dSearchTouchAction(255,y)==P3D_SEARCH_TOUCH_PREVIOUS);
    }
    assert(p3dSearchTouchAction(0,-1)==0);
    assert(p3dSearchTouchAction(0,192)==0);
    assert(p3dSearchTouchAction(0,200)==0);
    puts("C83 rendered zero-based console search glyphs and touch bounds: PASS");
    return 0;
}
