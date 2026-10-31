/* Native DS dual-screen development menu.
 * This is an interactive development shell, NOT the original game's graphics.
 * Replace with verified recovered Pokédex 3D Pro UI and game features.
 */
#include <nds.h>
#include <stdio.h>
#include <string.h>
#include <filesystem.h>
#include "feature_menu.h"
#include "menu_layout.h"
#include "menu_navigation.h"
#include "dsi_features.h"
#include "challenge.h"
#include "game_save_bridge.h"
#include "preview_stream.h"
#include "original_ui_page.h"
#include "move_dex.h"
#include "photo_album.h"
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
static int attack_type=1, defend_type=4, defend_type2=-1;
static P3DChallenge quiz;
static int challenge_correct_total=0, challenge_answer_total=0;
static unsigned int challenge_seed=0x13579BDFu;
static int favorite_index=0;
static int storage_ready=0;
static int nitro_ready=0;
static int save_message=0;
static int progress_dirty=0;
static int preview_ready=0;
static int preview_found=0;
static int move_catalog_ready=0;
static int move_text_offset=0;
static P3DPhotoAlbum photo_album;
static int album_ready=0;
static size_t album_offset=0;
static size_t album_selected=0;
static int album_confirm_delete=0;
static int art_page=-1;
static int showing_original_art=0;
static int original_art_available=0;
static int prefer_original_art=1;
static void prepare_original_art(void){
    int page=home?P3D_PAGE_HOME:(int)state.page;
    if(page==art_page)return;
    art_page=page;
    original_art_available=prefer_original_art&&nitro_ready&&p3dOriginalUiPageLoad(page);
    if(original_art_available){
        /* Reuse the existing bitmap layer; changing pages must not reset VRAM
         * that the console also uses. Keep the text console hidden only while
         * the original full-screen artwork is active. */
        if(!showing_original_art){
            bgInitSub(2,BgType_Bmp16,BgSize_B16_256x256,0,0);
            bgHide(3);
            bgShow(2);
        }
        p3dOriginalUiPageDraw();
        showing_original_art=1;
    }else if(showing_original_art){
        bgHide(2);
        consoleInit(&bottom_console,3,BgType_Text4bpp,BgSize_T_256x256,31,0,false,true);
        showing_original_art=0;
    }
}

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
static int save_progress(void){
    P3DSaveState record;
    if(!storage_ready){save_message=2;return 0;}
    if(!p3dGameSaveCapture(&record,&state,dex_index,move_index,challenge_correct_total,challenge_answer_total)){
        save_message=2;
        return 0;
    }
    save_message=p3dSaveStore(P3D_SAVE_BASE,&record)?1:2;
    return save_message==1;
}


static void render(void) {
    update_preview_mode();
    /* The upper BG3 text console is in front of the 3D layer. Hide it for
     * model previews, restoring it for menu pages or missing meshes. */
    if(display_preview)bgHide(3);
    else bgShow(3);
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
        } else if(state.page==P3D_PAGE_SEARCH){
            printf("Pokemon number: %03d / 649\n",state.selected_dex+1);
            printf("LEFT/RIGHT: +/- 1\n");
            printf("UP/DOWN: +/- 10\n");
            printf("A: open this Pokemon\n");
        } else if(state.page==P3D_PAGE_MOVES){
            printf("Move entry: %03d / 559\n",move_index+1);
            printf("LEFT/RIGHT: +/- 1 move\n");
            printf("UP/DOWN: +/- 10 moves\n");
            if(move_catalog_ready){
                P3DMove entry;
                if(p3dMoveDexRead(move_index,&entry)){
                    printf("%s\n",entry.name);
                    printf("%.48s\n",entry.description);
                }else printf("Move record unavailable.\n");
            }else printf("Original Move Dex unavailable.\n");
        } else if(state.page==P3D_PAGE_TYPES){
            int effect=defend_type2<0?p3dTypeEffect(attack_type,defend_type):
                       p3dTypeEffectDual(attack_type,defend_type,defend_type2);
            printf("Attack: %s\n",p3dTypeName(attack_type));
            printf("Defend: %s\n",p3dTypeName(defend_type));
            if(defend_type2>=0)printf("Second: %s\n",p3dTypeName(defend_type2));
            if(effect==0)printf("Effect: immune (0x)\n");
            else if(effect==5)printf("Effect: resisted (0.5x)\n");
            else if(effect==20)printf("Effect: super effective (2x)\n");
            else if(effect==40)printf("Effect: double weak (4x)\n");
            else if(effect==2)printf("Effect: double resist (0.25x)\n");
            else printf("Effect: normal (1x)\n");
            printf("Arrows: change types\n");
            printf("X: second type ON/OFF\n");
            printf("L/R: second type\n");
        } else if(state.page==P3D_PAGE_SETTINGS){
            printf("Automatic model rotation: %s\n",state.rotate?"ON":"OFF");
            printf("A: toggle automatic rotation\n");
            printf("L/R: rotate manually in Pokedex\n");
        } else if(state.page==P3D_PAGE_FAVORITES){
            printf("Saved favorites: %d / %d\n",state.favorites_count,P3D_FAVORITES_MAX);
            if(state.favorites_count>0){
                printf("Pokemon #%03d\n",state.favorites[favorite_index]+1);
                printf("LEFT/RIGHT: browse\n");
                printf("A: remove favorite\n");
            }else printf("No favorites yet.\n");
        } else if(state.page==P3D_PAGE_ALBUM){
            if(!storage_ready)printf("Photo Album needs FAT storage.\n");
            else if(!album_ready)printf("Photo folder unavailable.\n");
            else {
                char photos[P3D_ALBUM_PAGE_MAX][32];
                size_t total=0;
                size_t shown=p3dPhotoAlbumPage(&photo_album,photos,P3D_ALBUM_PAGE_MAX,album_offset,&total);
                printf("Photos: %u\n",(unsigned)total);
                if(!shown)printf("No saved AR photos.\n");
                for(size_t i=0;i<shown;i++)printf("%c%s\n",i==album_selected?'>':' ',photos[i]);
                printf("UP/DOWN: select  L/R: page\n");
                if(album_confirm_delete && shown)
                    printf("Delete %s? A:yes B:no\n",photos[album_selected]);
                else printf("X: delete (confirm with A)\n");
            }
        } else if(state.page==P3D_PAGE_CHALLENGE){
            if(quiz.stage==P3D_CHALLENGE_PICKER){
                printf("Mode: %s\n",p3dChallengeName(quiz.mode_cursor));
                printf("LEFT/RIGHT: select region\n");
                printf("A: Start quiz\n");
            }else if(quiz.stage==P3D_CHALLENGE_RESULTS){
                printf("Quiz complete: %d / %d\n",quiz.score,P3D_CHALLENGE_QUESTIONS);
                printf("Total correct: %d / %d\n",challenge_correct_total,challenge_answer_total);
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
    if(!nitro_ready)printf("NitroFS unavailable: assets disabled\n");
    if(!storage_ready)printf("No writable storage\n");
    else if(save_message==1)printf("Progress saved\n");
    else if(save_message==2)printf("Save failed\n");
    else if(save_message==3)printf("Progress restored\n");

    }
    prepare_original_art();
    if(showing_original_art)return;
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
        }else if(state.page==P3D_PAGE_SEARCH){
            printf("\x1b[13;1HSearch #%03d",state.selected_dex+1);
            printf("\x1b[15;1HA: open Pokemon");
        }else if(state.page==P3D_PAGE_MOVES){
            printf("\x1b[11;1HMove %03d of 559",move_index+1);
            if(move_catalog_ready){
                P3DMove entry;
                if(p3dMoveDexRead(move_index,&entry)){
                    printf("\x1b[13;1H%.28s",entry.name);
                    /* Clip each fragment to the console's 32-character
                     * width and display the available 84 characters. */
                    for(size_t part=0;part<3;part++){
                        size_t offset=(size_t)move_text_offset+part*28;
                        if(strlen(entry.description)<=offset)break;
                        printf("\x1b[%d;1H%.28s",15+(int)part*2,entry.description+offset);
                    }
                }
            }
            printf("\x1b[21;1HL/R: scroll text");
            printf("\x1b[23;1HArrows: browse moves");
        }else if(state.page==P3D_PAGE_TYPES){
            int effect=defend_type2<0?p3dTypeEffect(attack_type,defend_type):
                       p3dTypeEffectDual(attack_type,defend_type,defend_type2);
            printf("\x1b[11;1HAttack: %s",p3dTypeName(attack_type));
            printf("\x1b[13;1HDefend: %s",p3dTypeName(defend_type));
            printf("\x1b[15;1HSecond: %s",defend_type2<0?"OFF":p3dTypeName(defend_type2));
            if(effect==0)printf("\x1b[17;1HEffect: 0x");
            else if(effect==2)printf("\x1b[17;1HEffect: 0.25x");
            else if(effect==5)printf("\x1b[17;1HEffect: 0.5x");
            else if(effect==20)printf("\x1b[17;1HEffect: 2x");
            else if(effect==40)printf("\x1b[17;1HEffect: 4x");
            else printf("\x1b[17;1HEffect: 1x");
            printf("\x1b[20;1HX: 2nd type  L/R: change");
        }else if(state.page==P3D_PAGE_SETTINGS){
            printf("\x1b[13;1HAuto rotate: %s",state.rotate?"ON":"OFF");
            printf("\x1b[15;1HA: toggle setting");
        }else if(state.page==P3D_PAGE_FAVORITES){
            printf("\x1b[13;1HSaved: %d / %d",state.favorites_count,P3D_FAVORITES_MAX);
            printf("\x1b[15;1HChoose in Pokedex");
        }else if(state.page==P3D_PAGE_ALBUM){
            if(!storage_ready)printf("\x1b[13;1HFAT storage unavailable");
            else if(!album_ready)printf("\x1b[13;1HPhoto folder unavailable");
            else {
                size_t total=0;
                char names[P3D_ALBUM_PAGE_MAX][32];
                size_t shown=p3dPhotoAlbumPage(&photo_album,names,P3D_ALBUM_PAGE_MAX,album_offset,&total);
                printf("\x1b[11;1HPhotos: %u",(unsigned)total);
                for(size_t i=0;i<shown && i<5;i++)
                    printf("\x1b[%d;1H%c%s",13+(int)i*2,i==album_selected?'>':' ',names[i]);
                printf("\x1b[24;1H%s",album_confirm_delete?"A: delete  B: cancel":"X: delete  L/R: page");
            }
        }else if(state.page==P3D_PAGE_CHALLENGE){
            if(quiz.stage==P3D_CHALLENGE_PICKER){
                printf("\x1b[13;1H%s",p3dChallengeName(quiz.mode_cursor));
                printf("\x1b[15;1HLEFT/RIGHT: choose");
            }else if(quiz.stage==P3D_CHALLENGE_RESULTS){
                printf("\x1b[13;1HScore: %d / %d",quiz.score,P3D_CHALLENGE_QUESTIONS);
                printf("\x1b[15;1HA: replay challenge");
            }else{
                printf("\x1b[8;1HQuestion %d / %d",quiz.question+1,P3D_CHALLENGE_QUESTIONS);
                for(int i=0;i<P3D_CHALLENGE_OPTIONS;i++)
                    printf("\x1b[%d;2H%c Pokemon #%03d",11+i*3,
                           quiz.selected==i?'>':' ',quiz.choices[i]+1);
                printf("\x1b[23;1HTap answer or press A");
            }
        }else{
            printf("\x1b[13;1HFeature implementation pending");
        }
        if(state.page==P3D_PAGE_CHALLENGE && quiz.stage==P3D_CHALLENGE_QUESTION)
            printf("\x1b[24;1HB: Return to menu");
        else printf("\x1b[17;1HPress B to go back");
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
    videoSetModeSub(MODE_5_2D);
    vramSetBankA(VRAM_A_MAIN_BG);
    vramSetBankC(VRAM_C_SUB_BG);
    consoleInit(&top_console,3,BgType_Text4bpp,BgSize_T_256x256,
                31,0,true,true);
    consoleInit(&bottom_console,3,BgType_Text4bpp,BgSize_T_256x256,
                31,0,false,true);
    /* Mount the ROM filesystem before accessing original pages, models, or moves. */
    nitro_ready=nitroFSInit(NULL)?1:0;
    p3dMenuReset(&state);
    p3dChallengeReset(&quiz);
    /* FAT/DLDI storage is optional in DS mode; no media means volatile progress. */
    #ifdef P3D_HAVE_FAT
    storage_ready=fatInitDefault()?1:0;
    #else
    storage_ready=0; /* FAT support disabled for this build configuration */
    #endif
    if(storage_ready){
        P3DSaveState record;
        if(p3dSaveLoad(P3D_SAVE_BASE,&record)){
            if(p3dGameSaveRestore(&record,&state,&dex_index,&move_index)){
                challenge_correct_total=(int)record.challenge_correct;
                challenge_answer_total=(int)record.challenge_total;
                save_message=3;
            }
        }
    }
    /* libfat mounts the default writable device as fat:/; create the album
     * directory only when the device is actually available. */
    if(storage_ready)album_ready=p3dPhotoAlbumOpen(&photo_album,"fat:/Pokedex 3D Pro/Photos");
    if(nitro_ready){
        preview_ready=previewStreamInit();
        /* Moves must remain available even if a model preview is missing. */
        move_catalog_ready=p3dMoveDexInit("nitro:/moves.p3dm");
    }
    reload_preview();
    count=(int)p3dMenuEntries(caps,pages);
    render();
    while(1) {
        swiWaitForVBlank();
        challenge_seed+=0x9E3779B9u; /* Vary each game session's quiz sequence. */
        scanKeys();
        unsigned down=keysDown();
        unsigned held=keysHeld();
        int redraw=0;
        /* SELECT makes the text navigation available even with a full-screen
         * recovered UI image. Press SELECT again to restore original art. */
        if(down&KEY_SELECT){
            prefer_original_art=!prefer_original_art;
            /* An invisible confirmation must never remain armed when the
             * screen mode changes, including returning to the text screen. */
            album_confirm_delete=0;
            art_page=-1; /* force re-evaluation of the same page */
            redraw=1;
        }
        /* START explicitly retries a previously failed save, including from
         * the home menu, without discarding unsaved changes on failure. */
        if((down&KEY_START)&&progress_dirty){
            if(save_progress())progress_dirty=0;
            redraw=1;
        }
        /* Avoid a phantom save success from a previous write after the next
         * gameplay modification; keep the dirty flag until persistence works. */
        if(progress_dirty && save_message==1)save_message=0;
        if(home) {
            if((down&KEY_UP)&&highlighted>0){highlighted--;redraw=1;}
            if((down&KEY_DOWN)&&highlighted<count-1){highlighted++;redraw=1;}
            if(down&KEY_TOUCH) {
                touchPosition point;
                touchRead(&point);
                int hit=p3dMenuTouchIndex(point.px,point.py,count,highlighted);
                if(hit>=0) {
                    highlighted=hit;
                    if(p3dMenuEnter(&state,caps,pages[highlighted])){home=0;if(state.page==P3D_PAGE_CHALLENGE)p3dChallengeReset(&quiz);if(state.page==P3D_PAGE_SEARCH)state.selected_dex=dex_index;}
                    redraw=1;
                }
            }
            /* A menu tap already opens an entry; do not let a simultaneous
             * A press open the next highlighted entry in the same frame. */
            if((down&KEY_A)&&!(down&KEY_TOUCH)&&highlighted>=0&&highlighted<count) {
                if(p3dMenuEnter(&state,caps,pages[highlighted])){home=0;if(state.page==P3D_PAGE_CHALLENGE)p3dChallengeReset(&quiz);if(state.page==P3D_PAGE_SEARCH)state.selected_dex=dex_index;}
                redraw=1;
            }
        } else {
            if(down&KEY_B){
                if(state.page==P3D_PAGE_ALBUM && album_confirm_delete){
                    album_confirm_delete=0;
                }else{
                    if(progress_dirty && save_progress())progress_dirty=0;
                    home=1;
                }
                redraw=1;
            } else {
            /* Challenge picker: process mode choice before A starts a quiz.
             * This avoids silently ignoring same-frame direction + A. */
            if(state.page==P3D_PAGE_CHALLENGE &&
               quiz.stage==P3D_CHALLENGE_PICKER){
                int available=p3dChallengeAvailableModes(challenge_answer_total);
                if((down&KEY_LEFT)&&quiz.mode_cursor>0){quiz.mode_cursor--;redraw=1;}
                if((down&KEY_RIGHT)&&quiz.mode_cursor<available-1){quiz.mode_cursor++;redraw=1;}
            }
            if(state.page==P3D_PAGE_CHALLENGE){
                if(quiz.stage==P3D_CHALLENGE_PICKER||quiz.stage==P3D_CHALLENGE_RESULTS){
                    if(down&KEY_A){
                        /* Preserve the selected region when retrying. */
                        int mode=quiz.mode_cursor;
                        if(p3dChallengeBegin(&quiz,mode,challenge_seed,challenge_answer_total))
                            redraw=1;
                    }
                }else{
                    if((down&KEY_UP)&&quiz.selected>0){quiz.selected--;redraw=1;}
                    if((down&KEY_DOWN)&&quiz.selected<3){quiz.selected++;redraw=1;}
                    if((down&KEY_A)&&!(down&KEY_TOUCH)){
                        int result=p3dChallengeAnswer(&quiz,quiz.selected);
                        if(result>=0 && challenge_answer_total<100000000){
                            challenge_answer_total++;
                            if(result)challenge_correct_total++;
                            progress_dirty=1;
                        }
                        redraw=1;
                    }
                }
            }

            /* Touch the four answer rows on the lower screen in text mode.
             * Keep the original-art layout untouched until its coordinates
             * have been recovered from the source game. */
            if(state.page==P3D_PAGE_CHALLENGE &&
               quiz.stage==P3D_CHALLENGE_QUESTION &&
               !showing_original_art && (down&KEY_TOUCH)){
                touchPosition point;
                touchRead(&point);
                /* Choices are drawn at console rows 11,14,17,20:
                 * y=88,112,136,160. Keep the four 24px hitboxes
                 * aligned with their visible labels. */
                if(point.px>=24 && point.px<232 &&
                   point.py>=88 && point.py<184){
                    int selected=(point.py-88)/24;
                    if(selected>=0 && selected<P3D_CHALLENGE_OPTIONS){
                        quiz.selected=selected;
                        int result=p3dChallengeAnswer(&quiz,selected);
                        if(result>=0 && challenge_answer_total<100000000){
                            challenge_answer_total++;
                            if(result)challenge_correct_total++;
                            progress_dirty=1;
                        }
                        redraw=1;
                    }
                }
            }
            if(state.page==P3D_PAGE_SEARCH){
                int next=state.selected_dex;
                if(down&KEY_LEFT)next--;
                if(down&KEY_RIGHT)next++;
                if(down&KEY_UP)next-=10;
                if(down&KEY_DOWN)next+=10;
                if(next<0)next=0;
                if(next>648)next=648;
                if(next!=state.selected_dex){state.selected_dex=next;redraw=1;}
                if(down&KEY_A){
                    dex_index=state.selected_dex;
                    state.page=P3D_PAGE_DEX;
                    reload_preview();
                    progress_dirty=1;
                    redraw=1;
                }
            }
            if(state.page==P3D_PAGE_ALBUM && album_ready){
                char names[P3D_ALBUM_PAGE_MAX][32];
                size_t total=0;
                size_t shown=p3dPhotoAlbumPage(&photo_album,names,P3D_ALBUM_PAGE_MAX,album_offset,&total);
                if(!shown)album_selected=0;
                else if(album_selected>=shown)album_selected=shown-1;
                if(album_confirm_delete){
                    /* A deletion must not be confirmed under an invisible
                     * bitmap-overlay prompt or after a simultaneous selection. */
                    if((down&KEY_A) && !showing_original_art &&
                       !(down&(KEY_UP|KEY_DOWN|KEY_LEFT|KEY_RIGHT|KEY_TOUCH))){
                        if(shown && p3dPhotoAlbumDelete(&photo_album,names[album_selected]))
                            redraw=1;
                        album_confirm_delete=0;
                        redraw=1;
                    }
                    if((down&KEY_X) || showing_original_art){
                        album_confirm_delete=0;redraw=1;
                    }
                }else{
                    if((down&KEY_UP) && album_selected>0){album_selected--;redraw=1;}
                    if((down&KEY_DOWN) && album_selected+1<shown){album_selected++;redraw=1;}
                    /* Never request deletion while its confirmation is hidden
                     * beneath an original-art bitmap overlay. */
                    if((down&KEY_X) && shown && !showing_original_art &&
                       !(down&(KEY_LEFT|KEY_RIGHT|KEY_UP|KEY_DOWN))){
                        album_confirm_delete=1;redraw=1;
                    }
                    int direction=(down&KEY_LEFT)?-1:((down&KEY_RIGHT)?1:0);
                    if((down&KEY_TOUCH) && !showing_original_art){
                        touchPosition point;
                        touchRead(&point);
                        /* Only corner taps navigate; center taps select a
                         * filename, even in the bottom two rows. */
                        if(point.py>=150 && point.py<192 &&
                           (point.px<64 || point.px>=192))
                            direction=point.px<64?-1:1;
                        /* The five visible filename rows start at console row
                         * 13, then advance two 8-pixel rows per filename. */
                        if(point.px>=64 && point.px<192 &&
                           point.py>=104 && point.py<184){
                            int hit=((int)point.py-104)/16;
                            if(hit>=0 && hit<5 && (size_t)hit<shown){
                                album_selected=(size_t)hit;redraw=1;
                                direction=0;
                            }
                        }
                    }
                    if(direction<0 && album_offset>=P3D_ALBUM_PAGE_MAX){
                        album_offset-=P3D_ALBUM_PAGE_MAX;album_selected=0;redraw=1;
                    }else if(direction>0 && album_offset+P3D_ALBUM_PAGE_MAX<total){
                        album_offset+=P3D_ALBUM_PAGE_MAX;album_selected=0;redraw=1;
                    }
                }
            }
            if(state.page==P3D_PAGE_SETTINGS){
                int toggle=(down&KEY_A)!=0;
                if((down&KEY_TOUCH) && !showing_original_art){
                    touchPosition point;
                    touchRead(&point);
                    /* Touch the visible setting row on the text screen. */
                    if(point.px>=8 && point.px<248 &&
                       point.py>=96 && point.py<128)toggle=1;
                }
                if(toggle){
                    state.rotate=!state.rotate;
                    progress_dirty=1;
                    redraw=1;
                }
            }
            if(state.page==P3D_PAGE_TYPES){
                if(down&KEY_UP){attack_type=(attack_type+16)%17;redraw=1;}
                if(down&KEY_DOWN){attack_type=(attack_type+1)%17;redraw=1;}
                if(down&KEY_LEFT){defend_type=(defend_type+16)%17;redraw=1;}
                if(down&KEY_RIGHT){defend_type=(defend_type+1)%17;redraw=1;}
                if(down&KEY_X){defend_type2=defend_type2<0?0:-1;redraw=1;}
                if(defend_type2>=0){
                    if(down&KEY_L){defend_type2=(defend_type2+16)%17;redraw=1;}
                    if(down&KEY_R){defend_type2=(defend_type2+1)%17;redraw=1;}
                }
            }
            if(state.page==P3D_PAGE_FAVORITES){
                /* A corrupted list count must never be used to index a DS
                 * array, even if the save loader normally rejects it. */
                if(state.favorites_count<0 || state.favorites_count>P3D_FAVORITES_MAX)
                    state.favorites_count=0;
                /* Restored or recently shortened lists can leave the cursor
                 * outside the current count. Clamp before any rendering or
                 * left/right navigation. */
                if(favorite_index<0 || favorite_index>=state.favorites_count)
                    favorite_index=0;
                if((down&KEY_LEFT)&&favorite_index>0){favorite_index--;redraw=1;}
                if((down&KEY_RIGHT)&&favorite_index<state.favorites_count-1){favorite_index++;redraw=1;}
                if((down&KEY_A)&&state.favorites_count>0){
                    if(favorite_index<0 || favorite_index>=state.favorites_count)
                        favorite_index=0;
                    int removed=p3dFavoriteToggle(&state,state.favorites[favorite_index]);
                    if(removed){
                        progress_dirty=1;
                        if(favorite_index>=state.favorites_count)
                            favorite_index=state.favorites_count?state.favorites_count-1:0;
                        redraw=1;
                    }
                }
                /* If A removed the last favorite, X must not act on the
                 * entry that has just shifted in the same input frame. */
                if((down&KEY_X)&&!(down&KEY_A)&&state.favorites_count>0){
                    /* Clamp the view cursor before indexing restored favorites. */
                    if(favorite_index<0 || favorite_index>=state.favorites_count)
                        favorite_index=0;
                    dex_index=state.favorites[favorite_index];
                    state.page=P3D_PAGE_DEX;
                    reload_preview();
                    progress_dirty=1;
                    redraw=1;
                }
            }
            /* Selecting a favorite is a navigation action. Do not process
             * Pokédex A/LEFT/RIGHT input again on the same frame; otherwise
             * X+A could immediately remove the just-opened favorite. */
            if(state.page==P3D_PAGE_DEX && !(down&KEY_X)){
                /* Held shoulder buttons rotate continuously rather than taking
                 * only one step per press.  The model is drawn each frame, so
                 * rotation needs no expensive full-console redraw. */
                if(preview_found){
                    if((held&KEY_L) && !(held&KEY_R))
                        model_yaw=(model_yaw-256)&32767;
                    else if((held&KEY_R) && !(held&KEY_L))
                        model_yaw=(model_yaw+256)&32767;
                    else if(state.rotate && !(held&KEY_L) && !(held&KEY_R))
                        model_yaw=(model_yaw+64)&32767;
                }
                if(down&KEY_A){if(p3dFavoriteToggle(&state,dex_index))progress_dirty=1;redraw=1;}
                if((down&KEY_LEFT)&&dex_index>0){dex_index--;reload_preview();progress_dirty=1;redraw=1;}
                if((down&KEY_RIGHT)&&dex_index<648){dex_index++;reload_preview();progress_dirty=1;redraw=1;}
            }
            /* In text navigation mode, the bottom corners also browse entries.
             * Original-art mode retains its artwork without guessed hitboxes. */
            if(!showing_original_art && (down&KEY_TOUCH)){
                touchPosition point;
                touchRead(&point);
                if(point.py>=150 && point.py<192){
                    int direction=point.px<64?-1:(point.px>=192?1:0);
                    if(state.page==P3D_PAGE_DEX && direction){
                        int next=dex_index+direction;
                        if(next>=0 && next<649){
                            dex_index=next;reload_preview();
                            progress_dirty=1;redraw=1;
                        }
                    } else if(state.page==P3D_PAGE_SEARCH && direction){
                        int next=state.selected_dex+direction;
                        if(next>=0 && next<649){
                            state.selected_dex=next;
                            redraw=1;
                        }
                    } else if(state.page==P3D_PAGE_MOVES && direction){
                        int next=move_index+direction;
                        if(next>=0 && next<559){
                            move_index=next;progress_dirty=1;redraw=1;
                        }
                    }
                }
            }
            if(state.page==P3D_PAGE_MOVES){
                if(move_catalog_ready && (down&(KEY_L|KEY_R))){
                    P3DMove entry;
                    if(p3dMoveDexRead(move_index,&entry)){
                        int length=(int)strlen(entry.description);
                        int max_offset=length>84?length-84:0;
                        if((down&KEY_L) && move_text_offset>0){
                            move_text_offset=move_text_offset>=28?move_text_offset-28:0;
                            redraw=1;
                        }
                        if((down&KEY_R) && move_text_offset<max_offset){
                            move_text_offset+=28;
                            if(move_text_offset>max_offset)move_text_offset=max_offset;
                            redraw=1;
                        }
                    }
                }
                int next=move_index;
                if(down&KEY_LEFT)next--;
                if(down&KEY_RIGHT)next++;
                if(down&KEY_UP)next-=10;
                if(down&KEY_DOWN)next+=10;
                if(next<0)next=0;
                if(next>558)next=558;
                if(next!=move_index){
                    move_index=next;
                    move_text_offset=0;
                    progress_dirty=1;
                    redraw=1;
                }
            }
            } /* Do not process page-specific input after B returns home. */
        }
        /* Update page/model state before issuing 3D commands.  Previously
         * render_model() ran with the prior frame's display_preview flag:
         * switching between a model and a text page could render a stale
         * model for one extra frame. */
        if(redraw)render();
        if(display_preview)render_model();
    }
}
