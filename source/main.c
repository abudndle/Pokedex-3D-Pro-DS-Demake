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
#include "challenge.h"
#include "game_save_bridge.h"
#include "preview_stream.h"
#include "move_dex.h"
#ifdef P3D_HAVE_FAT
#include <fat.h>
#endif

#define MENU_TOUCH_Y 88
#define MENU_TOUCH_STEP 16
#define MENU_TOUCH_ROWS 6

static PrintConsole top_console, bottom_console;
static P3DMenu state;
static P3DPage pages[P3D_MENU_MAX];
static int highlighted=0, count=0, home=1;
static int dex_index=0, move_index=0;
static int attack_type=1, defend_type=4;
static P3DChallenge quiz;
static int favorite_index=0;
static int storage_ready=0;
static int save_message=0;
static int progress_dirty=0;
static int preview_ready=0;
static int preview_found=0;
static int move_catalog_ready=0;
static void reload_preview(void){preview_found=preview_ready&&previewStreamLoad(dex_index);}
static int display_preview=0;
static int model_yaw=0;
static void update_preview_mode(void){display_preview=!home&&state.page==P3D_PAGE_DEX&&preview_found;}
static void render_model(void){
    if(!display_preview)return;
    glViewport(0,0,255,191);
    glMatrixMode(GL_PROJECTION);glLoadIdentity();
    gluPerspective(50,256.0/192.0,0.1,20.0);
    glMatrixMode(GL_MODELVIEW);glLoadIdentity();
    glTranslatef32(0,0,floattof32(-3));
    glRotateYi(model_yaw);
    glPolyFmt(POLY_ALPHA(31)|POLY_CULL_NONE);
    glColor3b(255,255,255);
    previewStreamDraw();
    glFlush(0);
}

#define P3D_SAVE_BASE "fat:/pokedex3d" 
static void save_progress(void){
    P3DSaveState record;
    if(!storage_ready)return;
    if(p3dGameSaveCapture(&record,&state,dex_index,move_index,0,0))
        save_message=p3dSaveStore(P3D_SAVE_BASE,&record)?1:2;
}


static void render(void) {
    update_preview_mode();
    if(!display_preview){
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
            if(preview_found)printf("Source mesh: %d tris\n",previewStreamTriangleCount());
            else printf("Source mesh unavailable\n");
            printf("A: toggle favorite (%s)\n",p3dFavoriteContains(&state,dex_index)?"saved":"not saved");
        } else if(state.page==P3D_PAGE_MOVES){
            printf("Move entry: %03d / 559\n",move_index+1);
            printf("LEFT/RIGHT: browse moves\n");
            if(move_catalog_ready){
                P3DMove entry;
                if(p3dMoveDexRead(move_index,&entry)){
                    printf("%s\n",entry.name);
                    printf("%.48s\n",entry.description);
                }else printf("Move record unavailable.\n");
            }else printf("Original Move Dex unavailable.\n");
        } else if(state.page==P3D_PAGE_TYPES){
            int effect=p3dTypeEffect(attack_type,defend_type);
            printf("Attack: %s\n",p3dTypeName(attack_type));
            printf("Defend: %s\n",p3dTypeName(defend_type));
            if(effect==0)printf("Effect: immune (0x)\n");
            else if(effect==5)printf("Effect: resisted (0.5x)\n");
            else if(effect==20)printf("Effect: super effective (2x)\n");
            else printf("Effect: normal (1x)\n");
            printf("Arrows: change types\n");
        } else if(state.page==P3D_PAGE_FAVORITES){
            printf("Saved favorites: %d / %d\n",state.favorites_count,P3D_FAVORITES_MAX);
            if(state.favorites_count>0){
                printf("Pokemon #%03d\n",state.favorites[favorite_index]+1);
                printf("LEFT/RIGHT: browse\n");
                printf("A: remove favorite\n");
            }else printf("No favorites yet.\n");
        } else if(state.page==P3D_PAGE_CHALLENGE){
            if(quiz.stage==P3D_CHALLENGE_PICKER){
                printf("A: Start Unova quiz\n");
            }else if(quiz.stage==P3D_CHALLENGE_RESULTS){
                printf("Quiz complete: %d / %d\n",quiz.score,P3D_CHALLENGE_QUESTIONS);
                printf("A: Try again\n");
            }else{
                printf("Question %d / %d\n",quiz.question+1,P3D_CHALLENGE_QUESTIONS);
                printf("Choose Pokemon number:\n");
                for(int i=0;i<4;i++)printf("%c %d: #%03d\n",quiz.selected==i?'>':' ',i+1,quiz.choices[i]+1);
                printf("UP/DOWN + A: Answer\n");
            }
        } else {
            printf("Native feature UI pending.\n");
        }
        printf("\n");
        printf("B: RETURN TO MENU\n");
    }
    printf("\nDEVELOPMENT BUILD\n");
    if(!storage_ready)printf("No writable storage\n");
    else if(save_message==1)printf("Progress saved\n");
    else if(save_message==2)printf("Save failed\n");
    else if(save_message==3)printf("Progress restored\n");

    }
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
        if(state.page==P3D_PAGE_DEX){
            printf("\x1b[13;1HPokemon %03d of 649",dex_index+1);
            printf("\x1b[15;1HLEFT/RIGHT: browse");
        }else if(state.page==P3D_PAGE_MOVES){
            printf("\x1b[13;1HMove %03d of 559",move_index+1);
            printf("\x1b[15;1HLEFT/RIGHT: browse");
        }else if(state.page==P3D_PAGE_TYPES){
            printf("\x1b[13;1H%s vs %s",p3dTypeName(attack_type),p3dTypeName(defend_type));
            printf("\x1b[15;1HArrows: choose types");
        }else if(state.page==P3D_PAGE_FAVORITES){
            printf("\x1b[13;1HSaved: %d / %d",state.favorites_count,P3D_FAVORITES_MAX);
            printf("\x1b[15;1HChoose in Pokedex");
        }else if(state.page==P3D_PAGE_CHALLENGE){
            printf("\x1b[13;1HChallenge: %d / %d",quiz.question, P3D_CHALLENGE_QUESTIONS);
            printf("\x1b[15;1HA: select   B: return");
        }else{
            printf("\x1b[13;1HFeature implementation pending");
        }
        printf("\x1b[17;1HPress B to go back");
    }
}
int main(void) {
    P3DCapabilities caps=p3dCapabilities(0,0,0);
    videoSetMode(MODE_0_3D);
    glInit();
    glEnable(GL_ANTIALIAS);
    glEnable(GL_BLEND);
    glClearDepth(GL_MAX_DEPTH);
    glClearColor(4,4,8,31);
    videoSetModeSub(MODE_0_2D);
    vramSetBankA(VRAM_A_MAIN_BG);
    vramSetBankC(VRAM_C_SUB_BG);
    consoleInit(&top_console,3,BgType_Text4bpp,BgSize_T_256x256,
                31,0,true,true);
    consoleInit(&bottom_console,3,BgType_Text4bpp,BgSize_T_256x256,
                31,0,false,true);
    p3dMenuReset(&state);
    p3dChallengeReset(&quiz);
    /* FAT/DLDI storage is optional in DS mode; no media means volatile progress. */
    #ifdef P3D_HAVE_FAT
    storage_ready=fatInitDefault()?1:0;
    #else
    storage_ready=0; /* slim development toolchain excludes libfat */
    #endif
    if(storage_ready){
        P3DSaveState record;
        if(p3dSaveLoad(P3D_SAVE_BASE,&record)){
            p3dGameSaveRestore(&record,&state,&dex_index,&move_index);
            save_message=3;
        }
    }
    preview_ready=previewStreamInit();
    if(preview_ready)move_catalog_ready=p3dMoveDexInit("nitro:/moves.p3dm");
    reload_preview();
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
                    if(p3dMenuEnter(&state,caps,pages[highlighted])){home=0;if(state.page==P3D_PAGE_CHALLENGE)p3dChallengeReset(&quiz);}
                    redraw=1;
                }
            }
            if((down&KEY_A)&&highlighted>=0&&highlighted<count) {
                if(p3dMenuEnter(&state,caps,pages[highlighted])){home=0;if(state.page==P3D_PAGE_CHALLENGE)p3dChallengeReset(&quiz);}
                redraw=1;
            }
        } else {
            if(down&KEY_B){if(progress_dirty){save_progress();progress_dirty=0;}home=1;redraw=1;}
            if(state.page==P3D_PAGE_CHALLENGE){
                if(quiz.stage==P3D_CHALLENGE_PICKER||quiz.stage==P3D_CHALLENGE_RESULTS){
                    if(down&KEY_A){p3dChallengeBegin(&quiz,0,1,0);redraw=1;}
                }else{
                    if((down&KEY_UP)&&quiz.selected>0){quiz.selected--;redraw=1;}
                    if((down&KEY_DOWN)&&quiz.selected<3){quiz.selected++;redraw=1;}
                    if(down&KEY_A){p3dChallengeAnswer(&quiz,quiz.selected);redraw=1;}
                }
            }
            if(state.page==P3D_PAGE_TYPES){
                if(down&KEY_UP){attack_type=(attack_type+16)%17;redraw=1;}
                if(down&KEY_DOWN){attack_type=(attack_type+1)%17;redraw=1;}
                if(down&KEY_LEFT){defend_type=(defend_type+16)%17;redraw=1;}
                if(down&KEY_RIGHT){defend_type=(defend_type+1)%17;redraw=1;}
            }
            if(state.page==P3D_PAGE_FAVORITES){
                if((down&KEY_LEFT)&&favorite_index>0){favorite_index--;redraw=1;}
                if((down&KEY_RIGHT)&&favorite_index<state.favorites_count-1){favorite_index++;redraw=1;}
                if((down&KEY_A)&&state.favorites_count>0){
                    p3dFavoriteToggle(&state,state.favorites[favorite_index]);
                    progress_dirty=1;
                    if(favorite_index>=state.favorites_count)favorite_index=state.favorites_count?state.favorites_count-1:0;
                    redraw=1;
                }
            }
            if(state.page==P3D_PAGE_DEX){
                if(preview_found && (down&KEY_L)){model_yaw=(model_yaw-512)&32767;redraw=1;}
                if(preview_found && (down&KEY_R)){model_yaw=(model_yaw+512)&32767;redraw=1;}
                if(down&KEY_A){if(p3dFavoriteToggle(&state,dex_index))progress_dirty=1;redraw=1;}
                if((down&KEY_LEFT)&&dex_index>0){dex_index--;reload_preview();progress_dirty=1;redraw=1;}
                if((down&KEY_RIGHT)&&dex_index<648){dex_index++;reload_preview();progress_dirty=1;redraw=1;}
            }
            if(state.page==P3D_PAGE_MOVES){
                if((down&KEY_LEFT)&&move_index>0){move_index--;progress_dirty=1;redraw=1;}
                if((down&KEY_RIGHT)&&move_index<558){move_index++;progress_dirty=1;redraw=1;}
            }
        }
        if(display_preview)render_model();
        if(redraw){
            render();
        }
    }
}
