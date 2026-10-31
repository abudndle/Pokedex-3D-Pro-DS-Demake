/* Asset-free native build smoke entry point.
 * This DEVELOPMENT SHELL is intentionally not the original Pokédex 3D Pro UI.
 * It will be replaced by the recovered C14 main.c when migration is complete.
 * Do not distribute this as a finished port or substitute original assets.
 */
#include <nds.h>
#include <stdio.h>
#include "feature_menu.h"
#include "menu_layout.h"
#include "dsi_features.h"

static P3DMenu menu_state;
static P3DPage pages[P3D_MENU_MAX];
static int selected=0;
static int page_count=0;
static int on_home=1;

static void draw_shell(void) {
    consoleClear();
    iprintf("POKEDEX 3D PRO - DS\n");
    iprintf("PORT DEVELOPMENT BUILD\n");
    iprintf("-----------------------\n");
    if (on_home) {
        size_t start=p3dMenuVisibleStart((size_t)page_count,selected);
        iprintf("A: Open  B: Back\n");
        iprintf("Up/Down: Navigate\n\n");
        for (int row=0;row<P3D_MENU_VISIBLE_ROWS;row++) {
            size_t i=start+(size_t)row;
            if (i>=(size_t)page_count) break;
            iprintf("%c %s\n",selected==(int)i?'>':' ',p3dPageName(pages[i]));
        }
    } else {
        iprintf("%s\n\n",p3dPageName(menu_state.page));
        iprintf("Gameplay screen migration\n");
        iprintf("still in progress.\n");
        iprintf("Original asset renderer\n");
        iprintf("not yet connected.\n");
        iprintf("\nB: Return to main menu\n");
    }
    iprintf("\nNOT THE FINAL GAME\n");
}
int main(void){
    /* No DSi camera UI until camera capability and feature are implemented. */
    P3DCapabilities capabilities=p3dCapabilities(0,0,0);
    consoleDemoInit();
    p3dMenuReset(&menu_state);
    page_count=(int)p3dMenuEntries(capabilities,pages);
    draw_shell();
    while (1) {
        swiWaitForVBlank();
        scanKeys();
        unsigned pressed=keysDown();
        int changed=0;
        if (on_home) {
            if ((pressed&KEY_UP)&&selected>0){selected--;changed=1;}
            if ((pressed&KEY_DOWN)&&selected<page_count-1){selected++;changed=1;}
            if (pressed&KEY_TOUCH) {
                touchPosition touch;
                touchRead(&touch);
                int selected_from_touch=p3dMenuHitTest(touch.px,touch.py,(size_t)page_count,selected);
                if(selected_from_touch>=0){selected=selected_from_touch;changed=1;}
            }
            if ((pressed&KEY_A)&&selected<page_count) {
                if(p3dMenuEnter(&menu_state,capabilities,pages[selected])) {
                    on_home=0;changed=1;
                }
            }
        } else if (pressed&KEY_B) {
            on_home=1;changed=1;
        }
        if(changed)draw_shell();
    }
}
