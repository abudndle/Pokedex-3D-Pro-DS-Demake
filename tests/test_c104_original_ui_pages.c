#include <assert.h>
#include <stdio.h>
#include "original_ui_page.h"
#include "feature_menu.h"

unsigned short p3d_c104_bitmap[256u*192u];
unsigned short p3d_c105_top_bitmap[256u*192u];

int main(void) {
    assert(P3D_PAGE_RECORDS == 10);
    assert(P3D_PAGE_COUNT == 11);
    assert(p3dOriginalUiPageLoad(P3D_PAGE_HOME));
    assert(p3dOriginalUiPageReady());
    p3dOriginalUiPageDraw();
    assert(p3d_c104_bitmap[0] == 0x9234u);
    assert(p3d_c104_bitmap[256u*192u-1] == 0x9234u);

    /* C104: Records is also an original-art destination, not a text-only page. */
    assert(p3dOriginalUiPageLoad(P3D_PAGE_RECORDS));
    assert(p3dOriginalUiPageReady());
    p3dOriginalUiPageDraw();
    assert(p3d_c104_bitmap[0] == 0x801fu);
    assert(p3d_c104_bitmap[256u*192u-1] == 0x801fu);

    /* C105: the upper screen is a separate original source file and
     * separate native main-BG framebuffer, not duplicated bottom art. */
    assert(p3dOriginalTopPageLoad(P3D_PAGE_HOME));
    assert(p3dOriginalTopPageReady());
    p3dOriginalTopPageDraw();
    assert(p3d_c105_top_bitmap[0] == 0xa345u);
    assert(p3d_c105_top_bitmap[256u*192u-1] == 0xa345u);
    assert(p3d_c104_bitmap[0] == 0x801fu);
    assert(p3dOriginalTopPageLoad(P3D_PAGE_RECORDS));
    p3dOriginalTopPageDraw();
    assert(p3d_c105_top_bitmap[0] == 0x83e0u);
    assert(!p3dOriginalTopPageLoad(P3D_PAGE_AR));
    assert(!p3dOriginalTopPageReady());
    p3d_c105_top_bitmap[0] = 0x7777u;
    p3dOriginalTopPageDraw();
    assert(p3d_c105_top_bitmap[0] == 0x7777u);
    assert(!p3dOriginalTopPageLoad(-1));
    assert(!p3dOriginalTopPageLoad(P3D_PAGE_COUNT));

    /* C106: BG2 alpha bit must be preserved, revealing live BG0 3D only
     * in the explicitly source-masked model viewport. */
    assert(p3dOriginalTopOverlayLoad(P3D_PAGE_DEX));
    assert(p3dOriginalTopOverlayReady());
    p3dOriginalTopOverlayDraw();
    assert(p3d_c105_top_bitmap[0] == 0x9123u);
    assert(p3d_c105_top_bitmap[1] == 0x0000u);
    assert(p3d_c105_top_bitmap[256u*96u+128u] == 0x0042u);
    assert(p3d_c105_top_bitmap[256u*192u-1] == 0x9123u);
    /* The original bottom-screen HUD is an independent asset. */
    assert(p3d_c104_bitmap[0] == 0x801fu);
    assert(!p3dOriginalTopOverlayLoad(P3D_PAGE_RECORDS));
    assert(!p3dOriginalTopOverlayReady());
    p3d_c105_top_bitmap[0] = 0x5555u;
    p3dOriginalTopOverlayDraw();
    assert(p3d_c105_top_bitmap[0] == 0x5555u);
    assert(!p3dOriginalTopOverlayLoad(P3D_PAGE_SEARCH));
    assert(!p3dOriginalTopOverlayLoad(-1));
    assert(!p3dOriginalTopOverlayLoad(P3D_PAGE_COUNT));

    /* C116: original 3DS title is independent of the HOME art and uses
     * both private source screens, not duplicated lower-screen contents. */
    assert(p3dOriginalTitleLoad());
    assert(p3dOriginalTitleReady());
    p3dOriginalTitleDraw();
    assert(p3d_c104_bitmap[0]==0x9234u);
    assert(p3d_c105_top_bitmap[0]==0xa345u);
    assert(p3dOriginalUiPageLoad(P3D_PAGE_HOME));
    assert(p3dOriginalTopPageLoad(P3D_PAGE_HOME));
    p3dOriginalUiPageDraw();
    p3dOriginalTopPageDraw();
    assert(p3d_c104_bitmap[0]==0x9234u);
    assert(p3d_c105_top_bitmap[0]==0xa345u);
    /* Delete upper title: a lower title alone is never a fake dual-screen
     * original title. Old frame buffers may not be drawn after failure. */
    assert(remove("nitro:/ui/title/t1_title.rgb555")==0);
    assert(!p3dOriginalTitleLoad());
    assert(!p3dOriginalTitleReady());
    p3d_c104_bitmap[0]=0x3456u;
    p3d_c105_top_bitmap[0]=0x5678u;
    p3dOriginalTitleDraw();
    assert(p3d_c104_bitmap[0]==0x3456u);
    assert(p3d_c105_top_bitmap[0]==0x5678u);

    /* Missing, negative, and out-of-range originals fail closed. */
    assert(!p3dOriginalUiPageLoad(P3D_PAGE_AR));
    assert(!p3dOriginalUiPageReady());
    p3d_c104_bitmap[0] = 0x5678u;
    p3dOriginalUiPageDraw();
    assert(p3d_c104_bitmap[0] == 0x5678u);
    assert(!p3dOriginalUiPageLoad(-1));
    assert(!p3dOriginalUiPageLoad(P3D_PAGE_COUNT));
    puts("C106: masked native 3D overlay and upper/lower original UI loading: PASS");
    return 0;
}
