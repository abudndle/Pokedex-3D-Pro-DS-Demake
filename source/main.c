/* Native DS dual-screen development menu.
 * This is an interactive development shell, NOT the original game's graphics.
 * Replace with verified recovered Pokédex 3D Pro UI and game features.
 */
#include <nds.h>
#include <stdio.h>
#include "feature_menu.h"
#include "menu_layout.h"
#include "menu_navigation.h"
#include "dsi_features.h"

#define MENU_TOUCH_Y 88
#define MENU_TOUCH_STEP 16
#define MENU_TOUCH_ROWS 6

static PrintConsole top_console, bottom_console;
static P3DMenu state;
static P3DPage pages[P3D_MENU_MAX];
static int highlighted=0, count=0, home=1;
static int dex_index=0, move_index=0;
static int attack_type=1, defend_type=4;

static void render(void) {
    consoleSelect(&top_console);
    consoleClear();
    printf("POKEDEX 3D PRO DS\n");
    printf("========================\n\n");
    if (home) {
        printf("Choose a feature on the\n");
        printf("touchscreen.\n\n");
        printf("UP / DOWN: SELECT\n");
        printf("A: OPEN\n");
    } else {
        printf("%s\n\n", p3dPageName(state.page));
        if(state.page==P3D_PAGE_DEX){
            printf("Pokemon entry: %03d / 649\n",dex_index+1);
            printf("LEFT/RIGHT: browse entries\n");
            printf("Original models pending.\n");
        } else if(state.page==P3D_PAGE_MOVES){
            printf("Move entry: %03d / 559\n",move_index+1);
            printf("LEFT/RIGHT: browse moves\n");
            printf("Move data asset pending.\n");
        } else if(state.page==P3D_PAGE_TYPES){
            printf("Type chart: FIRE -> GRASS\n");
            printf("Effect: %dx\n",p3dTypeEffect(1,4)/10);
        } else {
            printf("Native feature UI pending.\n");
        }
        printf("\n");
        printf("B: RETURN TO MENU\n");
    }
    printf("\nDEVELOPMENT BUILD\n");

    consoleSelect(&bottom_console);
    consoleClear();
    printf("POKEDEX 3D PRO\n");
    printf("------------------------\n");
    if (home) {
        size_t first=p3dMenuVisibleStart((size_t)count,highlighted);
        printf("Tap a menu entry:\n");
        for (int row=0;row<MENU_TOUCH_ROWS;row++) {
            size_t index=first+(size_t)row;
            if(index>=(size_t)count) break;
            /* Text console is 8 pixels per row, zero-based.
               Two console rows per menu entry => 16-pixel touch target. */
            printf("\x1b[%d;1H%c %-25s",11+row*2,
                   (int)index==highlighted?'>':' ',
                   p3dPageName(pages[index]));
        }
        printf("\x1b[24;1HUse A to open selected");
    } else {
        printf("\x1b[9;1H%s",p3dPageName(state.page));
        printf("\x1b[13;1HFeature implementation pending");
        printf("\x1b[17;1HPress B to go back");
    }
}
int main(void) {
    P3DCapabilities caps=p3dCapabilities(0,0,0);
    videoSetMode(MODE_0_2D);
    videoSetModeSub(MODE_0_2D);
    vramSetBankA(VRAM_A_MAIN_BG);
    vramSetBankC(VRAM_C_SUB_BG);
    consoleInit(&top_console,3,BgType_Text4bpp,BgSize_T_256x256,
                31,0,true,true);
    consoleInit(&bottom_console,3,BgType_Text4bpp,BgSize_T_256x256,
                31,0,false,true);
    p3dMenuReset(&state);
    count=(int)p3dMenuEntries(caps,pages);
    render();
    while(1) {
        swiWaitForVBlank();
        scanKeys();
        unsigned down=keysDown();
        int redraw=0;
        if(home) {
            if((down&KEY_UP)&&highlighted>0){highlighted--;redraw=1;}
            if((down&KEY_DOWN)&&highlighted<count-1){highlighted++;redraw=1;}
            if(down&KEY_TOUCH) {
                touchPosition point;
                touchRead(&point);
                int hit=p3dMenuTouchIndex(point.px,point.py,count,highlighted);
                if(hit>=0) {
                    highlighted=hit;
                    if(p3dMenuEnter(&state,caps,pages[highlighted]))home=0;
                    redraw=1;
                }
            }
            if((down&KEY_A)&&highlighted>=0&&highlighted<count) {
                if(p3dMenuEnter(&state,caps,pages[highlighted]))home=0;
                redraw=1;
            }
        } else {
            if(down&KEY_B){home=1;redraw=1;}
            if(state.page==P3D_PAGE_TYPES){
                if(down&KEY_UP){attack_type=(attack_type+16)%17;redraw=1;}
                if(down&KEY_DOWN){attack_type=(attack_type+1)%17;redraw=1;}
                if(down&KEY_LEFT){defend_type=(defend_type+16)%17;redraw=1;}
                if(down&KEY_RIGHT){defend_type=(defend_type+1)%17;redraw=1;}
            }
            if(state.page==P3D_PAGE_DEX){
                if((down&KEY_LEFT)&&dex_index>0){dex_index--;redraw=1;}
                if((down&KEY_RIGHT)&&dex_index<648){dex_index++;redraw=1;}
            }
            if(state.page==P3D_PAGE_MOVES){
                if((down&KEY_LEFT)&&move_index>0){move_index--;redraw=1;}
                if((down&KEY_RIGHT)&&move_index<558){move_index++;redraw=1;}
            }
        }
        if(redraw)render();
    }
}
