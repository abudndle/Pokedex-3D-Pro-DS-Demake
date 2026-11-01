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

    /* Missing, negative, and out-of-range originals fail closed. */
    assert(!p3dOriginalUiPageLoad(P3D_PAGE_AR));
    assert(!p3dOriginalUiPageReady());
    p3d_c104_bitmap[0] = 0x5678u;
    p3dOriginalUiPageDraw();
    assert(p3d_c104_bitmap[0] == 0x5678u);
    assert(!p3dOriginalUiPageLoad(-1));
    assert(!p3dOriginalUiPageLoad(P3D_PAGE_COUNT));
    puts("C104: all-page original-art lookup and Records bitmap: PASS");
    return 0;
}
