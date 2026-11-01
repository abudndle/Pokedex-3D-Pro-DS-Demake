/* Native DS dual-screen development menu.
 * This is an interactive development shell, NOT the original game's graphics.
 * Replace with verified recovered Pokédex 3D Pro UI and game features.
 */
#include <nds.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <filesystem.h>
#include "feature_menu.h"
#include "menu_layout.h"
#include "menu_navigation.h"
#include "dsi_features.h"
#include "challenge.h"
#include "game_save_bridge.h"
#include "resume_state.h"
#include "title_idle.h"
#include "preview_stream.h"
#include "species_model_map.h"
#include "form_model_map.h"
#include "form_names.h"
#include "model_animation.h"
#include "model_animation_library.h"
#include "model_material_texture.h"
#include "source_material_map.h"
#include "source_material_texture_match.h"
#include "source_shader_caps.h"
#include "source_material_words.h"
#include "source_color_ranges.h"
#include "texture_asset.h"
#include "preview_texture_set.h"
#include "original_ui_page.h"
#include "title_timeline.h"
#include "title_audio.h"
#include "move_dex.h"
#include "move_text_view.h"
#include "dex_text.h"
#include "dex_search.h"
#include "search_touch.h"
#include "photo_album.h"
#include "records.h"
#ifdef P3D_HAVE_FAT
#include <fat.h>
#endif

#define MENU_TOUCH_Y 88
#define MENU_TOUCH_STEP 16
#define MENU_TOUCH_ROWS 6

static PrintConsole top_console, bottom_console;
static P3DMenu state;
static P3DCapabilities hardware_caps;
static P3DPage pages[P3D_MENU_MAX];
static int highlighted=0, count=0, home=1;
static int dex_index=0, move_index=0;
static int attack_type=1, defend_type=4, defend_type2=-1;
static P3DChallenge quiz;
static P3DRecords records;
static int records_dirty=0;
static int records_tab=0;
static int records_recent_cursor=0;
static int challenge_correct_total=0, challenge_answer_total=0;
static unsigned int challenge_seed=0x13579BDFu;
static int favorite_index=0;
static int storage_ready=0;
static int nitro_ready=0;
static int save_message=0;
static int progress_dirty=0;
static P3DResumeState last_checkpoint;
static int last_checkpoint_valid=0;
static unsigned checkpoint_ticks=0;
static int preview_ready=0;
static int preview_found=0;
static P3DAnimationClip preview_animation;
static P3DAnimationLibrary preview_animation_library;
static P3DMaterialMap preview_materials;
static P3DSourceMaterialMap preview_source_materials;
static P3DSourceShaderCaps preview_source_shaders;
static P3DSourceMaterialWords preview_source_words;
static P3DSourceColorRanges preview_color_ranges;
static P3DTextureManifest preview_textures;
static int material_references_ready=0;
static P3DTexturePixels preview_pixels;
static int texture_payload_ready=0;
static P3DPreviewTextureSet preview_gl_textures;
static unsigned animation_tick=0;
static P3DModelMap species_models;
static P3DFormMap alternate_models;
static P3DFormNames form_names;
static int selected_form=0;
static int move_catalog_ready=0;
static int dex_text_ready=0;
static int search_region=0;
static int search_scope=0;
static int search_field=P3D_DEX_SEARCH_NAME;
static int move_text_offset=0;
/* C100 shows actual original P3DM effect text; defaults to description. */
static int move_show_effect=0;
static P3DPhotoAlbum photo_album;
static int album_ready=0;
static size_t album_offset=0;
static size_t album_selected=0;
static int album_confirm_delete=0;
/* C81 viewed species, regional totals and per-mode high scores are stored in
 * separate dual-slot P3RC saves; P3SV legacy progress remains compatible. */
static size_t records_photo_total(void){
    char names[P3D_ALBUM_PAGE_MAX][32];
    size_t total=0;
    if(album_ready)
        p3dPhotoAlbumPage(&photo_album,names,P3D_ALBUM_PAGE_MAX,0,&total);
    return total;
}
static int art_page=-1;
static int showing_original_art=0;
static int original_art_available=0;
static int prefer_original_art=1;
/* The source 3DS upper artwork lives in DS main BG2; the original
 * 3D Pokémon renderer still owns BG0 on a Dex model page. */
static int top_art_page=-1;
static int top_art_preview=-1;
static int showing_original_top_art=0;
/* Original 3DS title is its own boot state, separate from HOME. */
static int title_active=0;
static P3DTitleIdle title_idle;
static unsigned idle_refresh=0;
static P3DTitleTimeline title_timeline;
static P3DTitleCues title_cues;
static P3DTitleAudio title_pcm;
static int title_audio_channel=-1;
static int display_preview=0;
static void prepare_original_top_art(void){
    int page=home?P3D_PAGE_HOME:(int)state.page;
    if(page==top_art_page && display_preview==top_art_preview)return;
    top_art_page=page;
    top_art_preview=display_preview;
    /* Use the original-source alpha mask on Pokémon model pages.
     * This is a separate source asset from the solid information-page image:
     * never fabricate a cutout from the background or hide the model with
     * an all-opaque bitmap. */
    int have_overlay=display_preview && prefer_original_art && nitro_ready &&
                     p3dOriginalTopOverlayLoad(page);
    int have_page=!display_preview && prefer_original_art && nitro_ready &&
                  p3dOriginalTopPageLoad(page);
    if(have_page || have_overlay){
        if(!showing_original_top_art){
            /* BG2 256x256 16-bit uses the full 128 KiB bank A.
             * Never overlap its bitmap with the tiled BG3 text console.
             * MODE_5_3D retains the hardware 3D engine on BG0. */
            bgHide(3);
            videoSetMode(MODE_5_3D);
            bgInit(2,BgType_Bmp16,BgSize_B16_256x256,0,0);
            bgSetPriority(2,0);
            REG_BG0CNT=(REG_BG0CNT & ~3) | 3;
            bgShow(2);
        }
        if(have_overlay)p3dOriginalTopOverlayDraw();
        else p3dOriginalTopPageDraw();
        showing_original_top_art=1;
    }else if(showing_original_top_art){
        bgHide(2);
        videoSetMode(MODE_0_3D);
        consoleInit(&top_console,3,BgType_Text4bpp,BgSize_T_256x256,
                    31,0,true,true);
        bgSetPriority(3,0);
        REG_BG0CNT=(REG_BG0CNT & ~3) | 3;
        showing_original_top_art=0;
    }
}
/* Reversible source-geometry QA; not saved as an original game option. */
static int prefer_source_chunks=0;
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
            /* Mode 5 is needed only for the original 16-bit bitmap. */
            videoSetModeSub(MODE_5_2D);
            bgInitSub(2,BgType_Bmp16,BgSize_B16_256x256,0,0);
            bgHide(7);
            bgShow(6);
        }
        p3dOriginalUiPageDraw();
        showing_original_art=1;
    }else if(showing_original_art){
        bgHide(6);
        videoSetModeSub(MODE_0_2D);
        consoleInit(&bottom_console,3,BgType_Text4bpp,BgSize_T_256x256,31,0,false,true);
        showing_original_art=0;
    }
}

static void reload_preview(void){
    /* Free all prior per-material VRAM allocations on species/form changes. */
    p3dPreviewTextureSetRelease(&preview_gl_textures);
    /* C120: title idle Pokémon is NOT the saved Dex entry. Its source
     * species/form preview is separate; leaving idle reloads the last
     * saved user's own Dex selection with no temporary save mutation. */
    int species=(title_active && title_idle.active && title_idle.has_species)
        ?(int)title_idle.species:dex_index;
    int form=(title_active && title_idle.active)?0:selected_form;
    int resource=form?p3dFormResolve(&alternate_models,species,form):
                      p3dModelMapResolve(&species_models,species);
    char clip_path[80];
    previewStreamPreferChunks(prefer_source_chunks);
    preview_found=preview_ready&&resource>=0&&previewStreamLoad(resource);
    preview_animation.ready=0;
    preview_animation_library.ready=0;
    preview_materials.ready=0;
    preview_source_materials.ready=0;
    preview_source_shaders.ready=0;
    preview_source_words.ready=0;
    preview_color_ranges.ready=0;
    preview_textures.ready=0;
    material_references_ready=0;
    texture_payload_ready=0;
    preview_pixels.ready=0;
    animation_tick=0;
    if(preview_found){
        /* Load only existing and validated private clips. No invented motion
         * or action labels are generated for missing original assets. */
        p3dAnimationLibraryLoad(&preview_animation_library,
                                &preview_animation,"nitro:/animations",resource);
        snprintf(clip_path,sizeof(clip_path),"nitro:/materials/p%03d.p3mt",resource);
        if(p3dMaterialMapLoad(&preview_materials,clip_path,(unsigned)previewStreamTriangleCount())){
            snprintf(clip_path,sizeof(clip_path),"nitro:/materials/p%03d.p3tx",resource);
            if(p3dTextureManifestLoad(&preview_textures,clip_path) &&
               previewStreamHasUv()){
                /* C109: candidate textures must be referenced by the
                 * matching original C5 draw material. A C92 color-name
                 * hint is not enough to activate a native texture. */
                snprintf(clip_path,sizeof(clip_path),
                         "nitro:/materials/p%03d.p3mr",resource);
                if(p3dSourceMaterialLoad(&preview_source_materials,clip_path,
                       (unsigned)resource,
                       (unsigned)previewStreamTriangleCount())){
                    /* C110 requires original C5 shader capability evidence.
                     * The C5 CF_COLORMAP declaration is not a decoded source
                     * sampler role: multiple distinct texture slots remain
                     * untextured until their 3DS GPU selection is proven. */
                    snprintf(clip_path,sizeof(clip_path),
                             "nitro:/materials/p%03d.p3sc",resource);
                    if(p3dSourceShaderCapsLoad(&preview_source_shaders,
                                              clip_path,(unsigned)resource)){
                        /* C113: original C5's complete 13-word material
                         * operations must agree with P3SC and P3MR before
                         * routing any preview texture. We still DO NOT
                         * claim GPU shader/sampler operations are decoded. */
                        snprintf(clip_path,sizeof(clip_path),
                                 "nitro:/materials/p%03d.p3sw",resource);
                        if(p3dSourceMaterialWordsLoad(&preview_source_words,
                                                    clip_path,(unsigned)resource)
                           && p3dSourceMaterialWordsMatch(
                                &preview_source_words,&preview_source_shaders,
                                &preview_source_materials,(unsigned)resource,
                                (unsigned)previewStreamTriangleCount()))
                            material_references_ready=
                                p3dSourceColorRangesBuild(
                                    &preview_color_ranges,
                                    &preview_source_words,&preview_source_shaders,
                                    &preview_source_materials,&preview_materials,
                                    &preview_textures,(unsigned)resource,
                                    (unsigned)previewStreamTriangleCount());
                    }
                }
            }
            /* C116: a valid P3UV file still needs a verified wrap mode
             * for negative or >1 source UVs. Deny only those material ranges,
             * preserving the safe simple-color ranges and every face. */
            if(material_references_ready && previewStreamHasUv()){
                for(unsigned i=0;i<preview_color_ranges.count;i++){
                    if(preview_color_ranges.enabled[i] &&
                       !previewStreamUvRangeUnit(
                          preview_materials.ranges[i].first_triangle,
                          preview_materials.ranges[i].triangle_count)){
                        preview_color_ranges.enabled[i]=0;
                        preview_color_ranges.approved--;
                    }
                }
            }
            if(material_references_ready && preview_color_ranges.approved &&
               previewStreamHasUv()){
                /* Model-scoped paths avoid colliding texture IDs across species. */
                snprintf(clip_path,sizeof(clip_path),
                         "nitro:/textures/p%03d",resource);
                texture_payload_ready=p3dPreviewTextureSetLoadMasked(
                    &preview_gl_textures,&preview_pixels,
                    &preview_materials,&preview_textures,clip_path,
                    preview_color_ranges.enabled,preview_color_ranges.count);
            }
        }
    }
}
/* Original private 3DS title artwork is never fabricated from home art.
 * Use independent source-derived top and bottom bitmaps at boot only. */
/* A verified title cue can play only if its private source-derived
 * PCM16 bytes and P3TC timing agree; no synthesized/menu sound fallback.
 * Reuse the same 32-KiB buffer only after stopping the ARM7 sample DMA. */
static void play_title_cue(unsigned frame){
    unsigned cue=p3dTitleCueForFrame(&title_cues,frame);
    char path[72];
    if(!cue)return;
    if(title_audio_channel>=0){
        soundKill(title_audio_channel);
        title_audio_channel=-1;
    }
    snprintf(path,sizeof(path),"nitro:/ui/title/audio/c%02u.p3sa",cue);
    if(p3dTitleAudioLoad(&title_pcm,path))
        title_audio_channel=soundPlaySample(
            title_pcm.pcm,SoundFormat_16Bit,
            title_pcm.sample_count*2u,title_pcm.rate,127,64,false,0);
}
static int show_original_title(void){
    if(!nitro_ready || !prefer_original_art || !p3dOriginalTitleLoad())
        return 0;
    bgHide(3);
    videoSetMode(MODE_5_3D);
    bgInit(2,BgType_Bmp16,BgSize_B16_256x256,0,0);
    bgSetPriority(2,0);
    REG_BG0CNT=(REG_BG0CNT & ~3) | 3;
    bgShow(2);
    videoSetModeSub(MODE_5_2D);
    bgInitSub(2,BgType_Bmp16,BgSize_B16_256x256,0,0);
    /* libnds indexes sub BG2/BG3 as 6/7, not main BG2/BG3. */
    bgHide(7);
    bgShow(6);
    p3dOriginalTitleDraw();
    showing_original_top_art=1;
    showing_original_art=1;
    /* Optional private original 3DS timing/animation. No P3TL means the
     * original frame-zero title stays visible, not synthetic animation. */
    (void)p3dTitleTimelineLoad(&title_timeline,
                              "nitro:/ui/title/timeline.p3tl");
    (void)p3dTitleCuesLoad(&title_cues,
                          "nitro:/ui/title/cues.p3tc",
                          title_timeline.ready?title_timeline.frames:1u);
    title_active=1;
    p3dTitleIdleReset(&title_idle);
    /* Console RTC/session entropy, never dex_index or saved Pokémon. */
    p3dTitleIdleSeed(&title_idle,(uint32_t)time(NULL)^(uint32_t)challenge_seed);
    idle_refresh=0;
    if(title_cues.ready){
        soundEnable();
        play_title_cue(0);
    }
    return 1;
}
static int model_yaw=0;
static void update_preview_mode(void){
    display_preview=preview_found &&
        ((!home && state.page==P3D_PAGE_DEX) ||
         (title_active && title_idle.active));
}
static void render_model(void){
    if(!display_preview)return;
    glViewport(0,0,255,191);
    glMatrixMode(GL_PROJECTION);glLoadIdentity();
    gluPerspective(50,256.0/192.0,0.1,20.0);
    glMatrixMode(GL_MODELVIEW);glLoadIdentity();
    glTranslatef32(0,0,floattof32(-3));
    glRotateYi(model_yaw);
    if(preview_animation.ready){
        P3DAnimationFrame pose;
        if(p3dAnimationPoseAt(&preview_animation,animation_tick,&pose)){
            glRotateXi(pose.pitch);
            glRotateYi(pose.yaw);
            glRotateZi(pose.roll);
        }
    }
    glPolyFmt(POLY_ALPHA(31)|POLY_CULL_NONE);
    if(preview_gl_textures.ready){
        /* C115: draw EVERY original triangle exactly once. Only material
         * ranges supported by original-source C5 simple-colormap references
         * use a color texture. Unknown original bump/effect/dual-sampler
         * ranges keep their original geometry and untextured face colors. */
        for(unsigned i=0;i<preview_materials.count;i++){
            const P3DMaterialRange *range=&preview_materials.ranges[i];
            const P3DPreviewTexture *tex=preview_color_ranges.ready &&
                preview_color_ranges.enabled[i]?
                p3dPreviewTextureSetFind(&preview_gl_textures,range->texture_id):NULL;
            if(tex){
                glEnable(GL_TEXTURE_2D);
                glBindTexture(0,tex->gl_id);
                previewStreamDrawRange(range->first_triangle,range->triangle_count,
                                       tex->width,tex->height);
            }else{
                glDisable(GL_TEXTURE_2D);
                glBindTexture(0,0);
                previewStreamDrawRange(range->first_triangle,range->triangle_count,
                                       0,0);
            }
        }
        glDisable(GL_TEXTURE_2D);
        glBindTexture(0,0);
    }else{
        glDisable(GL_TEXTURE_2D);
        previewStreamDraw();
    }
    glFlush(0);
}
/* The original upper title scene changes after idle time. Show the last
 * visited Pokémon only when its recovered source preview is available.
 * The console's actual RTC provides weekday, date, and time. Unrecovered
 * original idle artwork/animations remain out of this development preview. */
static void enter_title_idle(void){
    bgHide(2);
    videoSetMode(MODE_0_3D);
    consoleInit(&top_console,3,BgType_Text4bpp,BgSize_T_256x256,
                31,0,true,true);
    bgSetPriority(3,0);
    REG_BG0CNT=(REG_BG0CNT & ~3)|3;
    showing_original_top_art=0;
    update_preview_mode();
}
static void draw_title_idle_info(void){
    char clock[48];
    time_t now=time(NULL);
    consoleSelect(&top_console);
    consoleClear();
    if(p3dTitleIdleClock(clock,sizeof(clock),now))
        printf("%s\n",clock);
    unsigned species=title_idle.has_species?title_idle.species:0u;
    if(dex_text_ready){
        P3DDexText entry;
        if(p3dDexTextRead((int)species,&entry))
            printf("#%03u %.25s\n",species+1u,entry.name);
        else printf("Pokémon #%03u\n",species+1u);
    }else printf("Pokémon #%03u\n",species+1u);
    printf("\nCheck this Pokémon's\nPokédex entry?\n\nA: CHECK ENTRY\nB/START: CONTINUE");
}

#define P3D_SAVE_BASE "fat:/pokedex3d"
static P3DResumeState current_resume(void){
    P3DResumeState view={0};
    view.home=(uint8_t)(home!=0);
    view.page=(uint8_t)state.page;
    view.highlight=(uint8_t)highlighted;
    view.records_tab=(uint8_t)records_tab;
    view.dex=(uint16_t)dex_index;
    view.move=(uint16_t)move_index;
    view.selected_dex=(uint16_t)state.selected_dex;
    view.album_page=(uint16_t)((album_offset/P3D_ALBUM_PAGE_MAX)>999?
        999:(album_offset/P3D_ALBUM_PAGE_MAX));
    return view;
}
static int save_progress(void){
    P3DSaveState record;
    if(!storage_ready){save_message=2;return 0;}
    if(!p3dGameSaveCapture(&record,&state,dex_index,move_index,challenge_correct_total,challenge_answer_total)){
        save_message=2;
        return 0;
    }
    int saved=p3dSaveStore(P3D_SAVE_BASE,&record)?1:0;
    if(saved){
        P3DResumeState screen=current_resume();
        if(p3dResumeStore(P3D_SAVE_BASE,&screen)){
            last_checkpoint=screen;
            last_checkpoint_valid=1;
            checkpoint_ticks=0;
        }else saved=0;
    }
    if(saved && records_dirty){
        if(p3dRecordsStore(P3D_SAVE_BASE,&records))records_dirty=0;
        else saved=0;
    }
    save_message=saved?1:2;
    return saved;
}


static void render(void) {
    /* View tracking happens on actual Dex-page visits, including forms.
     * Never mark unseen species when merely booting the home menu. */
    if(!home && state.page==P3D_PAGE_DEX && p3dRecordsVisit(&records,dex_index)){
        records_dirty=1;
        progress_dirty=1;
    }
    update_preview_mode();
    prepare_original_top_art();
    /* BG2 source art has its own bitmap VRAM layout. Keep the upper text
     * console hidden when bitmap art (opaque page OR masked model overlay)
     * occupies bank A; live Pokémon remains behind the BG2 mask on BG0. */
    if(display_preview || showing_original_top_art)bgHide(3);
    else bgShow(3);
    if(!display_preview && !showing_original_top_art){
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
            if(dex_text_ready){
                P3DDexText entry;
                if(p3dDexTextRead(dex_index,&entry)){
                    printf("Original name: %.28s\n",entry.name);
                    printf("Height %.15s  Weight %.15s\n",entry.height,entry.weight);
                    printf("%.56s\n",entry.description);
                }
            }
            printf("Pokemon entry: %03d / 649\n",dex_index+1);
            printf("LEFT/RIGHT: browse entries\n");
            printf("Form: %s",selected_form?"alternate":"base");
            if(selected_form){
                const char *name=p3dFormName(&form_names,dex_index,selected_form);
                if(name)printf(" %s",name);
                else printf(" #%d",selected_form);
            }
            printf("\nY: cycle verified forms\n");
            if(preview_found){
                printf("Source mesh: %d tris\n",previewStreamTriangleCount());
                printf("Material refs: %s\n",material_references_ready?"verified":"unavailable");
                printf("Texture data: %s\n",texture_payload_ready?"verified":"unavailable");
                printf("Native textures: %u\n",preview_gl_textures.count);
            }
            else printf("Source mesh unavailable\n");
            if(preview_found){
                if(preview_animation.ready){
                    printf("Animation: %u frames, %u ticks (%s)\n",preview_animation.count,preview_animation.total_ticks,preview_animation.version==2?"smooth":"held");
                    printf("Verified clip: %u / %u\n",preview_animation_library.selected+1,preview_animation_library.count);
                    if(preview_animation_library.count>1)
                        printf("UP/DOWN: select animation\n");
                }else printf("Animation: static (no clip)\n");
            }
            printf("A: toggle favorite (%s)\n",p3dFavoriteContains(&state,dex_index)?"saved":"not saved");
            printf("X: search this Pokemon\n");
        } else if(state.page==P3D_PAGE_SEARCH){
            if(dex_text_ready){
                P3DDexText entry;
                if(p3dDexTextRead(state.selected_dex,&entry))
                    printf("Original name: %.28s\n",entry.name);
                printf("X+UP/DOWN: name initial %c\n",state.search_letter);
                printf("X+LEFT/RIGHT: find by name\n");
                printf("Text query: %.12s\n",state.search_query);
                printf("Region %s Scope %s\n",p3dDexRegionName(search_region),p3dDexScopeName(search_scope));
                printf("Field: %s\n",search_field==P3D_DEX_SEARCH_NAME?"NAME":"DESCRIPTION");
                printf("SELECT: show text search UI\n");
            }
            printf("Pokemon number: %03d / 649\n",state.selected_dex+1);
            printf("LEFT/RIGHT: +/- 1\n");
            printf("UP/DOWN: +/- 10\n");
            printf("A: open this Pokemon\n");
            printf("Y: toggle favorite (%s)\n",p3dFavoriteContains(&state,state.selected_dex)?"saved":"not saved");
            printf("X: open Favorites\n");
            printf("L: open Move Dex\n");
            printf("R: open Settings\n");
        } else if(state.page==P3D_PAGE_MOVES){
            printf("Move entry: %03d / 559\n",move_index+1);
            printf("LEFT/RIGHT: +/- 1 move\n");
            printf("UP/DOWN: +/- 10 moves\n");
            printf("Y: back to Pokemon Search\n");
            printf("X: original effect / description\n");
            if(move_catalog_ready){
                P3DMove entry;
                if(p3dMoveDexRead(move_index,&entry)){
                    printf("%s\n",entry.name);
                    const char *original=p3dMoveTextField(&entry,move_show_effect);
                    printf("%.48s\n",original&&*original?original:"(Original text unavailable)");
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
            printf("Y: open Challenge\n");
            printf("L/R: second type\n");
        } else if(state.page==P3D_PAGE_SETTINGS){
            printf("Automatic model rotation: %s\n",state.rotate?"ON":"OFF");
            printf("Source geometry: %s\n",prefer_source_chunks?"HIGH (TEST)":"LEGACY");
            printf("X: toggle private detail mode\n");
            printf("A: toggle automatic rotation\n");
            printf("Y: open Pokemon Search\n");
            printf("L/R: rotate manually in Pokedex\n");
        } else if(state.page==P3D_PAGE_FAVORITES){
            printf("Saved favorites: %d / %d\n",state.favorites_count,P3D_FAVORITES_MAX);
            if(state.favorites_count>0){
                printf("Pokemon #%03d\n",state.favorites[favorite_index]+1);
                printf("LEFT/RIGHT: browse\n");
                printf("A: remove favorite\n");
                printf("Y: search this Pokemon\n");
            }else printf("No favorites yet.\n");
        } else if(state.page==P3D_PAGE_RECORDS){
            static const char *regions[]={"KANTO","JOHTO","HOENN","SINNOH","UNOVA"};
            static const int first[]={0,151,251,386,493};
            static const int last[]={150,250,385,492,648};
            if(records_tab==0){
                printf("VIEWED: %d / 649\n",p3dRecordsTotal(&records));
                for(int i=0;i<5;i++)
                    printf("%-8s %3d / %3d\n",regions[i],
                           p3dRecordsCount(&records,first[i],last[i]),last[i]-first[i]+1);
                printf("Saved favorites: %d\n",state.favorites_count);
            }else if(records_tab==1){
                printf("RECENT VIEWED POKEMON\n");
                for(int i=0;i<P3D_RECORD_RECENT;i++){
                    int id=records.recent[i];
                    if(id==P3D_RECORD_NO_SPECIES)break;
                    printf("%c %d: Pokemon #%03d\n",
                           i==records_recent_cursor?'>':' ',i+1,id+1);
                }
                printf("UP/DOWN: select, A: open\n");
            }else{
                printf("CHALLENGE HIGHSCORES\n");
                printf("Completed rounds: %u\n",(unsigned)records.rounds);
                for(int i=0;i<P3D_RECORD_CHALLENGES;i++){
                    printf("%d: %2d best, %u runs\n",i+1,
                           records.best[i]==0xffu?-1:(int)records.best[i],
                           (unsigned)records.runs[i]);
                }
                printf("Overall correct: %d/%d\n",
                       challenge_correct_total,challenge_answer_total);
            }
            printf("L/R: record tabs (%d/3)\n",records_tab+1);
            printf("X: Favorites  Y: Challenge\n");
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
                printf("Y: Type Matchups\n");
            }else if(quiz.stage==P3D_CHALLENGE_RESULTS){
                printf("Quiz complete: %d / %d\n",quiz.score,P3D_CHALLENGE_QUESTIONS);
                printf("Total correct: %d / %d\n",challenge_correct_total,challenge_answer_total);
                printf("A: Try again\n");
                printf("Y: Type Matchups\n");
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
            /* Original 3DS AR Viewer icon stays in its menu position on
             * DS; the unactionable fallback is explicitly greyed out. */
            if(pages[index]==P3D_PAGE_AR &&
               !p3dCanEnterFeature(hardware_caps,P3D_FEATURE_AR))
                printf(" [DSi camera only]");
        }
        printf("\x1b[24;1HUse A to open selected");
    } else {
        printf("\x1b[9;1H%s",p3dPageName(state.page));
        if(state.page==P3D_PAGE_DEX){
            if(dex_text_ready){
                P3DDexText entry;
                if(p3dDexTextRead(dex_index,&entry)){
                    printf("\x1b[11;1H%.28s",entry.name);
                    printf("\x1b[21;1HHeight %.10s Wt %.8s",entry.height,entry.weight);
                    printf("\x1b[23;1H%.28s",entry.description);
                }
            }
            printf("\x1b[13;1HPokemon %03d of 649",dex_index+1);
            printf("\x1b[15;1HLEFT/RIGHT: browse");
            if(selected_form){
                const char *name=p3dFormName(&form_names,dex_index,selected_form);
                if(name)printf("\x1b[17;1HForm: %.24s",name);
                else printf("\x1b[17;1HAlternate form #%d",selected_form);
            }
            else printf("\x1b[17;1HBase form");
            printf("\x1b[19;1HY: next verified form");
        }else if(state.page==P3D_PAGE_SEARCH){
            printf("\x1b[9;1H%.28s",state.search_query[0]?state.search_query:"NAME / TEXT SEARCH");
            printf("\x1b[11;1HRegion: %.9s  Scope: %.9s",
                   p3dDexRegionName(search_region),p3dDexScopeName(search_scope));
            printf("\x1b[13;1HField: %s",search_field==P3D_DEX_SEARCH_NAME?"NAME":"DESCRIPTION");
            if(dex_text_ready){
                P3DDexText entry;
                if(p3dDexTextRead(state.selected_dex,&entry))
                    printf("\x1b[15;1H#%03d %.23s",state.selected_dex+1,entry.name);
            }else printf("\x1b[15;1HOriginal text unavailable");
            printf("\x1b[18;1H  A B C D E F G H I J K L M");
            printf("\x1b[20;1H  N O P Q R S T U V W X Y Z");
            printf("\x1b[22;1HDEL       NEXT      PREV");
            printf("\x1b[23;1HTap region/scope/field above");
        }else if(state.page==P3D_PAGE_MOVES){
            printf("\x1b[11;1HMove %03d of 559",move_index+1);
            if(move_catalog_ready){
                P3DMove entry;
                if(p3dMoveDexRead(move_index,&entry)){
                    printf("\x1b[13;1H%.28s",entry.name);
                    printf("\x1b[14;1H%s",move_show_effect?"Original effect:":"Original description:");
                    const char *original=p3dMoveTextField(&entry,move_show_effect);
                    if(!original||!*original){
                        printf("\x1b[15;1H(No original text)");
                    }else{
                        /* Original Move Dex data only: no synthetic fallbacks. */
                        for(size_t part=0;part<3;part++){
                            size_t offset=(size_t)move_text_offset+part*28;
                            if(strlen(original)<=offset)break;
                            printf("\x1b[%d;1H%.28s",15+(int)part*2,original+offset);
                        }
                    }
                }
            }
            printf("\x1b[21;1HX: Effect/Desc  L/R: scroll");
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
        }else if(state.page==P3D_PAGE_RECORDS){
            printf("\x1b[9;1HRecords: %s",records_tab==0?"REGIONS":records_tab==1?"RECENT":"QUIZZES");
            if(records_tab==0){
                printf("\x1b[11;1HViewed: %d / 649",p3dRecordsTotal(&records));
                printf("\x1b[13;1HKanto %d/151 Johto %d/100",
                       p3dRecordsCount(&records,0,150),p3dRecordsCount(&records,151,250));
                printf("\x1b[15;1HHoenn %d/135 Sinnoh %d/107",
                       p3dRecordsCount(&records,251,385),p3dRecordsCount(&records,386,492));
                printf("\x1b[17;1HUnova: %d / 156",p3dRecordsCount(&records,493,648));
                printf("\x1b[19;1HFavorites: %d  Photos: %u",
                       state.favorites_count,(unsigned)records_photo_total());
            }else if(records_tab==1){
                for(int i=0;i<5;i++){
                    int row=(records_recent_cursor/5)*5+i;
                    if(row>=P3D_RECORD_RECENT ||
                       records.recent[row]==P3D_RECORD_NO_SPECIES)break;
                    printf("\x1b[%d;1H%c Pokemon #%03d",11+i*2,
                           row==records_recent_cursor?'>':' ',
                           records.recent[row]+1);
                }
            }else{
                printf("\x1b[11;1HCompleted: %u",(unsigned)records.rounds);
                for(int i=0;i<7;i++)
                    printf("\x1b[%d;1H%d: %u runs  best %d",
                           13+i*2,i+1,(unsigned)records.runs[i],
                           records.best[i]==0xffu?-1:(int)records.best[i]);
            }
            printf("\x1b[23;1HL/R: tabs  X/Fav Y/Quiz");
        }else if(state.page==P3D_PAGE_SETTINGS){
            printf("\x1b[13;1HAuto rotate: %s",state.rotate?"ON":"OFF");
            printf("\x1b[14;1HGeometry: %s",prefer_source_chunks?"HIGH TEST":"LEGACY");
            printf("\x1b[16;1HX: preview detail");
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
    P3DCapabilities caps=p3dCapabilities(isDSiMode()?1:0,0,0);
    videoSetMode(MODE_0_3D);
    glInit();
    glEnable(GL_ANTIALIAS);
    glEnable(GL_BLEND);
    glClearDepth(GL_MAX_DEPTH);
    glClearColor(4,4,8,31);
    /* Mode 0 exposes BG3 as a tiled text background for consoleInit. */
    videoSetModeSub(MODE_0_2D);
    vramSetBankA(VRAM_A_MAIN_BG);
    /* Dedicated 128 KiB texture VRAM; bank A remains the upper text BG. */
    vramSetBankB(VRAM_B_TEXTURE);
    vramSetBankC(VRAM_C_SUB_BG);
    consoleInit(&top_console,3,BgType_Text4bpp,BgSize_T_256x256,
                31,0,true,true);
    consoleInit(&bottom_console,3,BgType_Text4bpp,BgSize_T_256x256,
                31,0,false,true);
    /* The 3D engine displays through main BG0. On menu pages its
     * opaque clear color otherwise covers the upper BG3 text console.
     * Raise BG3 above BG0; model pages hide BG3 explicitly. */
    bgSetPriority(3,0);
    REG_BG0CNT=(REG_BG0CNT & ~3) | 3;
    /* Print a boot sentinel BEFORE any filesystem initialization. If the
     * emulator capture remains blank, the fault precedes normal game logic. */
    consoleSelect(&top_console);
    printf("POKEDEX DS BOOT\n");
    consoleSelect(&bottom_console);
    printf("Initializing game...\n");
    swiWaitForVBlank();
    /* Diagnostic color pulse: direct backdrop registers should be visible
     * even if the text console or game filesystems never become ready.
     * Keep the early console text visible after this short boot probe. */
    BG_PALETTE[0]=RGB15(0,20,0);
    BG_PALETTE_SUB[0]=RGB15(0,0,20);
    for(int probe=0;probe<45;probe++)swiWaitForVBlank();
    BG_PALETTE[0]=RGB15(0,0,0);
    BG_PALETTE_SUB[0]=RGB15(0,0,0);
    /* Mount the ROM filesystem before accessing original pages, models, or moves. */
    nitro_ready=nitroFSInit(NULL)?1:0;
    if(nitro_ready){
        p3dModelMapLoad(&species_models,"nitro:/models/species_map.p3sm");
        p3dFormMapLoad(&alternate_models,"nitro:/models/forms.p3fm");
        p3dFormNamesLoad(&form_names,"nitro:/models/form_names.p3fn");
    }
    p3dMenuReset(&state);
    p3dChallengeReset(&quiz);
    p3dRecordsReset(&records);
    /* FAT/DLDI storage is optional in DS mode; no media means volatile progress. */
    #ifdef P3D_HAVE_FAT
    storage_ready=fatInitDefault()?1:0;
    #else
    storage_ready=0; /* FAT support disabled for this build configuration */
    #endif
    /* Hardware-aware DSi detection; never claim working camera AR before
     * the DSi enhanced camera backend is actually integrated/initialized. */
    caps=p3dCapabilities(isDSiMode()?1:0,storage_ready,0);
    hardware_caps=caps;
    if(storage_ready){
        /* Bad or missing records slots leave a clean in-memory history. */
        (void)p3dRecordsLoad(P3D_SAVE_BASE,&records);
        P3DSaveState record;
        if(p3dSaveLoad(P3D_SAVE_BASE,&record)){
            if(p3dGameSaveRestore(&record,&state,&dex_index,&move_index)){
                challenge_correct_total=(int)record.challenge_correct;
                challenge_answer_total=(int)record.challenge_total;
                save_message=3;
                P3DResumeState resume;
                if(p3dResumeLoad(P3D_SAVE_BASE,&resume) &&
                   p3dResumeApply(&resume,caps,&home,&state,&highlighted)){
                    dex_index=(int)resume.dex;
                    move_index=(int)resume.move;
                    records_tab=(int)resume.records_tab;
                    album_offset=(size_t)resume.album_page*P3D_ALBUM_PAGE_MAX;
                    last_checkpoint=resume;
                    last_checkpoint_valid=1;
                }
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
        dex_text_ready=p3dDexTextInit("nitro:/data/dex_en.p3dx");
    }
    reload_preview();
    count=(int)p3dMenuEntries(caps,pages);
    /* The real original 3DS title uses private source art on both screens.
     * The asset-free developer ROM still boots directly to a test menu. */
    if(!show_original_title())render();
    while(1) {
        swiWaitForVBlank();
        challenge_seed+=0x9E3779B9u; /* Vary each game session's quiz sequence. */
        scanKeys();
        unsigned down=keysDown();
        unsigned held=keysHeld();
        int redraw=0;
        if(title_active){
            /* Idle A opens the independently chosen title Pokémon entry.
             * The usual title exit still resumes the saved page and Pokémon.
             * No input is forwarded twice to the menu underneath. */
            if(down&(KEY_A|KEY_B|KEY_START|KEY_TOUCH)){
                if(title_idle.active && (down&KEY_A) &&
                   title_idle.has_species){
                    dex_index=(int)title_idle.species;
                    selected_form=0;
                    home=0;
                    state.page=P3D_PAGE_DEX;
                    state.selected_dex=dex_index;
                }
                title_active=0;
                title_timeline.ready=0;
                title_cues.ready=0;
                p3dTitleIdleReset(&title_idle);
                /* Restore the last saved species preview on ordinary exit;
                 * on idle A load the chosen species's Pokédex entry. */
                reload_preview();
                if(title_audio_channel>=0){
                    soundKill(title_audio_channel);
                    title_audio_channel=-1;
                }
                art_page=-1;
                top_art_page=-1;
                showing_original_top_art=0;
                render();
            }else if(p3dTitleIdleAdvance(&title_idle)){
                p3dTitleIdleChooseSpecies(&title_idle);
                reload_preview();
                enter_title_idle();
                draw_title_idle_info();
            }else if(title_idle.active){
                if(p3dTitleIdleSceneDue(&title_idle)){
                    p3dTitleIdleChooseSpecies(&title_idle);
                    reload_preview();
                    update_preview_mode();
                    draw_title_idle_info();
                }
                if(++idle_refresh>=60){
                    idle_refresh=0;
                    draw_title_idle_info(); /* refresh actual console RTC */
                }
                if(preview_found){
                    render_model();
                    if(preview_animation.ready)
                        animation_tick=(animation_tick+1)%preview_animation.total_ticks;
                }
            }else if(title_timeline.ready){
                int frame=p3dTitleTimelineAdvance(&title_timeline);
                if(frame>=0){
                    if(p3dOriginalTitleFrameLoad((unsigned)frame)){
                        p3dOriginalTitleDraw();
                        play_title_cue((unsigned)frame);
                    }else title_timeline.ready=0;
                }
            }
            continue;
        }
        /* SELECT makes the text navigation available even with a full-screen
         * recovered UI image. Press SELECT again to restore original art. */
        if(down&KEY_SELECT){
            prefer_original_art=!prefer_original_art;
            /* An invisible confirmation must never remain armed when the
             * screen mode changes, including returning to the text screen. */
            album_confirm_delete=0;
            art_page=-1; /* force re-evaluation of the same page */
            top_art_page=-1; /* refresh upper artwork or dev fallback too */
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
                if((down&KEY_Y) && !(down&(KEY_A|KEY_TOUCH)) && quiz.stage!=P3D_CHALLENGE_QUESTION){
                    state.page=P3D_PAGE_TYPES;
                    redraw=1;
                }
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
                        if(result>=0 && quiz.stage==P3D_CHALLENGE_RESULTS &&
                           p3dRecordsComplete(&records,quiz.mode,quiz.score)){
                            records_dirty=1;
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
                        if(result>=0 && quiz.stage==P3D_CHALLENGE_RESULTS &&
                           p3dRecordsComplete(&records,quiz.mode,quiz.score)){
                            records_dirty=1;
                            progress_dirty=1;
                        }
                        redraw=1;
                    }
                }
            }
            if(state.page==P3D_PAGE_SEARCH){
                /* Text-mode keyboard only: never guess original-art hitboxes. */
                if((down&KEY_TOUCH) && !showing_original_art){
                    touchPosition point;
                    touchRead(&point);
                    int action=p3dSearchTouchAction(point.px,point.py);
                    if(action>='A' && action<='Z'){
                        if(p3dDexQueryAppend(state.search_query,(char)action))redraw=1;
                    }else if(action==P3D_SEARCH_TOUCH_BACKSPACE){
                        p3dDexQueryBackspace(state.search_query);
                        redraw=1;
                    }else if(action==P3D_SEARCH_TOUCH_REGION){
                        search_region=(search_region+1)%P3D_DEX_REGIONS;
                        redraw=1;
                    }else if(action==P3D_SEARCH_TOUCH_SCOPE){
                        search_scope=(search_scope+1)%P3D_DEX_SCOPE_COUNT;
                        redraw=1;
                    }else if(action==P3D_SEARCH_TOUCH_FIELD){
                        search_field=search_field==P3D_DEX_SEARCH_NAME?
                                     P3D_DEX_SEARCH_DESCRIPTION:P3D_DEX_SEARCH_NAME;
                        redraw=1;
                    }else if(dex_text_ready &&
                             (action==P3D_SEARCH_TOUCH_NEXT||
                              action==P3D_SEARCH_TOUCH_PREVIOUS)){
                        int hit=p3dDexFindScoped(state.search_query,state.selected_dex,
                                      action==P3D_SEARCH_TOUCH_NEXT?1:-1,
                                      search_field,search_region,search_scope,
                                      &records,&state);
                        if(hit>=0){
                            state.selected_dex=hit;
                            redraw=1;
                        }
                    }
                }
                if((down&KEY_R) && !(down&(KEY_A|KEY_X|KEY_Y|KEY_L))){
                    state.page=P3D_PAGE_SETTINGS;
                    redraw=1;
                }
                if((down&KEY_L) && !(down&(KEY_A|KEY_X|KEY_Y))){
                    state.page=P3D_PAGE_MOVES;
                    redraw=1;
                }
                /* X+arrows use the recovered original species-name index.
                 * Plain X still opens Favorites, and normal arrows retain
                 * the existing number-based search. */
                int source_search=(down&KEY_X) && (down&(KEY_LEFT|KEY_RIGHT|KEY_UP|KEY_DOWN));
                if((down&KEY_X) && !(down&(KEY_A|KEY_Y)) && !source_search){
                    state.page=P3D_PAGE_FAVORITES;
                    favorite_index=0;
                    redraw=1;
                }
                int next=state.selected_dex;
                if(source_search){
                    if(down&KEY_UP){state.search_letter=state.search_letter=='Z'?'A':state.search_letter+1;redraw=1;}
                    if(down&KEY_DOWN){state.search_letter=state.search_letter=='A'?'Z':state.search_letter-1;redraw=1;}
                    if(dex_text_ready && ((down&KEY_LEFT)!=0)!=((down&KEY_RIGHT)!=0)){
                        char q[2]={state.search_letter,0};
                        int hit=p3dDexFindScoped(q,state.selected_dex,
                                    (down&KEY_RIGHT)?1:-1,P3D_DEX_SEARCH_NAME,
                                    0,P3D_DEX_SCOPE_ALL,&records,&state);
                        if(hit>=0)next=hit;
                    }
                }else{
                    if(down&KEY_LEFT)next--;
                    if(down&KEY_RIGHT)next++;
                    if(down&KEY_UP)next-=10;
                    if(down&KEY_DOWN)next+=10;
                }
                if(next<0)next=0;
                if(next>648)next=648;
                if(next!=state.selected_dex){state.selected_dex=next;redraw=1;}
                if((down&KEY_Y) && !(down&KEY_A)){
                    if(p3dFavoriteToggle(&state,state.selected_dex))progress_dirty=1;
                    redraw=1;
                }
                if(down&KEY_A){
                    dex_index=state.selected_dex;
                    selected_form=0;
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
            if(state.page==P3D_PAGE_RECORDS){
                if((down&KEY_RIGHT) || (down&KEY_R)){
                    records_tab=(records_tab+1)%3;
                    records_recent_cursor=0;
                    redraw=1;
                }else if((down&KEY_LEFT) || (down&KEY_L)){
                    records_tab=(records_tab+2)%3;
                    records_recent_cursor=0;
                    redraw=1;
                }else if(records_tab==1 && (down&(KEY_UP|KEY_DOWN))){
                    int next=records_recent_cursor+((down&KEY_DOWN)?1:-1);
                    if(next>=0 && next<P3D_RECORD_RECENT &&
                       records.recent[next]!=P3D_RECORD_NO_SPECIES){
                        records_recent_cursor=next;
                        redraw=1;
                    }
                }
                if((down&KEY_Y) && !(down&(KEY_A|KEY_X))){
                    state.page=P3D_PAGE_CHALLENGE;
                    p3dChallengeReset(&quiz);
                    redraw=1;
                }else if((down&KEY_X) && !(down&KEY_A)){
                    state.page=P3D_PAGE_FAVORITES;
                    favorite_index=0;
                    redraw=1;
                }else if(down&KEY_A){
                    if(records_tab==1 &&
                       records.recent[records_recent_cursor]!=P3D_RECORD_NO_SPECIES){
                        dex_index=(int)records.recent[records_recent_cursor];
                        selected_form=0;
                        state.page=P3D_PAGE_DEX;
                        reload_preview();
                        redraw=1;
                    }else if(records_tab==0){
                        state.page=P3D_PAGE_ALBUM;
                        album_offset=0;
                        album_selected=0;
                        album_confirm_delete=0;
                        redraw=1;
                    }
                }
            }
            if(state.page==P3D_PAGE_SETTINGS){
                if((down&KEY_X) && !(down&(KEY_A|KEY_TOUCH))){
                    prefer_source_chunks=!prefer_source_chunks;
                    reload_preview();
                    redraw=1;
                }
                if((down&KEY_Y) && !(down&(KEY_A|KEY_TOUCH))){
                    state.selected_dex=dex_index;
                    state.page=P3D_PAGE_SEARCH;
                    redraw=1;
                }
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
                if((down&KEY_Y) && !(down&(KEY_A|KEY_X))){
                    state.page=P3D_PAGE_CHALLENGE;
                    p3dChallengeReset(&quiz);
                    redraw=1;
                }
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
                if((down&KEY_Y) && !(down&(KEY_A|KEY_X))){
                    if(state.favorites_count>0){
                        state.selected_dex=state.favorites[favorite_index];
                    }else{
                        state.selected_dex=dex_index;
                    }
                    state.page=P3D_PAGE_SEARCH;
                    redraw=1;
                }
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
                    selected_form=0;
                    state.page=P3D_PAGE_DEX;
                    reload_preview();
                    progress_dirty=1;
                    redraw=1;
                }
            }
            /* Selecting a favorite is a navigation action. Do not process
             * Pokédex A/LEFT/RIGHT input again on the same frame; otherwise
             * X+A could immediately remove the just-opened favorite. */
            if(state.page==P3D_PAGE_DEX && (down&KEY_X) && !(down&(KEY_A|KEY_Y))){
                state.selected_dex=dex_index;
                state.page=P3D_PAGE_SEARCH;
                redraw=1;
            }
            if(state.page==P3D_PAGE_DEX && !(down&KEY_X)){
                /* Cycle only existing verified optional animation files;
                 * reset playback at the new keyframe sequence. */
                if(preview_found && preview_animation_library.ready &&
                   ((down&KEY_UP)!=0)!=((down&KEY_DOWN)!=0)){
                    int direction=(down&KEY_DOWN)?1:-1;
                    if(p3dAnimationLibraryStep(&preview_animation_library,
                                               &preview_animation,
                                               "nitro:/animations",direction)){
                        animation_tick=0;
                        redraw=1;
                    }
                }
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
                if((down&KEY_Y)){selected_form=p3dFormNext(&alternate_models,dex_index,selected_form);reload_preview();redraw=1;}
                if((down&KEY_LEFT)&&dex_index>0){dex_index--;selected_form=0;reload_preview();progress_dirty=1;redraw=1;}
                if((down&KEY_RIGHT)&&dex_index<648){dex_index++;selected_form=0;reload_preview();progress_dirty=1;redraw=1;}
            }
            /* In text navigation mode, the bottom corners also browse entries.
             * Original-art mode retains its artwork without guessed hitboxes. */
            if(!showing_original_art && (down&KEY_TOUCH) && state.page!=P3D_PAGE_SEARCH){
                touchPosition point;
                touchRead(&point);
                if(point.py>=150 && point.py<192){
                    int direction=point.px<64?-1:(point.px>=192?1:0);
                    if(state.page==P3D_PAGE_DEX && direction){
                        int next=dex_index+direction;
                        if(next>=0 && next<649){
                            dex_index=next;selected_form=0;reload_preview();
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
                if((down&KEY_X) && !(down&(KEY_Y|KEY_A|KEY_TOUCH))){
                    move_show_effect=!move_show_effect;
                    move_text_offset=0;
                    redraw=1;
                }
                if((down&KEY_Y) && !(down&(KEY_A|KEY_X))){
                    state.selected_dex=dex_index;
                    state.page=P3D_PAGE_SEARCH;
                    redraw=1;
                }
                /* L and R are dedicated to description scrolling, but a
                 * simultaneous shoulder press must not scroll twice. */
                int scroll_dir=((down&KEY_R)!=0)-((down&KEY_L)!=0);
                /* The lower-screen center scrolls descriptions without
                 * conflicting with bottom-corner move navigation. */
                if((down&KEY_TOUCH) && !showing_original_art){
                    touchPosition point;
                    touchRead(&point);
                    if(point.px>=64 && point.px<192 &&
                       point.py>=112 && point.py<152)
                        scroll_dir=-1;
                    else if(point.px>=64 && point.px<192 &&
                            point.py>=152 && point.py<184)
                        scroll_dir=1;
                }
                if(move_catalog_ready && scroll_dir){
                    P3DMove entry;
                    if(p3dMoveDexRead(move_index,&entry)){
                        const char *original=p3dMoveTextField(&entry,move_show_effect);
                        int offset=p3dMoveTextScroll(move_text_offset,original,scroll_dir);
                        if(offset!=move_text_offset){move_text_offset=offset;redraw=1;}
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
        /* The DS cannot intercept a hard power-off. Save after a short
         * quiet interval rather than pretending to save on shutdown.
         * Dual-slot CRC records preserve the last active page on restart. */
        if(storage_ready){
            if(checkpoint_ticks<60)checkpoint_ticks++;
            if(checkpoint_ticks>=60){
                P3DResumeState view=current_resume();
                if(progress_dirty||!last_checkpoint_valid||
                   memcmp(&view,&last_checkpoint,sizeof(view))!=0){
                    if(save_progress())progress_dirty=0;
                }else checkpoint_ticks=0;
            }
        }
        if(display_preview){
            render_model();
            if(preview_animation.ready)animation_tick=(animation_tick+1)%preview_animation.total_ticks;
        }
    }
}
