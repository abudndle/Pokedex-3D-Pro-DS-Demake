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
#include "bookmark_session.h"
#include "menu_layout.h"
#include "menu_navigation.h"
#include "dsi_features.h"
#include "challenge.h"
#include "challenge_text.h"
#include "game_save_bridge.h"
#include "resume_state.h"
#include "title_idle.h"
#include "preview_stream.h"
#include "verified_geometry_pair.h"
#include "verified_primitive_draw.h"
#include "verified_vertex_uv.h"
#include "verified_primitive_uv_draw.h"
#include "original_skeleton.h"
#include "source_track_bindings.h"
#include "species_model_map.h"
#include "form_model_map.h"
#include "form_names.h"
#include "model_animation.h"
#include "animation_playback.h"
#include "model_animation_library.h"
#include "model_material_texture.h"
#include "source_material_map.h"
#include "source_material_texture_match.h"
#include "source_material_texture_match.h"
#include "source_shader_caps.h"
#include "source_material_words.h"
#include "source_color_ranges.h"
#include "texture_asset.h"
#include "preview_texture_set.h"
#include "ds_material_uv_draw.h"
#include "original_ui_page.h"
#include "original_home_hotspots.h"
#include "title_timeline.h"
#include "title_audio.h"
#include "move_dex.h"
#include "move_text_view.h"
#include "dex_text.h"
#include "species_details.h"
#include "nitro_source_bridge.h"
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
static uint32_t challenge_seed=0x13579BDFu;
static int favorite_index=0;
static int storage_ready=0;
static P3DBookmarkSettings bookmark_settings;
static unsigned bookmark_cursor=0;
static int nitro_ready=0;
static int save_message=0;
static int progress_dirty=0;
static P3DResumeState last_checkpoint;
static int last_checkpoint_valid=0;
static unsigned checkpoint_ticks=0;
static int preview_ready=0;
static int preview_found=0;
/* Optional private source-verified P3VX/P3IX geometry; no inferred textures. */
static P3DVerifiedGeometryPair source_geometry_pair;
static int source_geometry_ready=0;
/* C301: paired UV bytes are not proof of original sampler/material roles. */
static P3DVerifiedVertexUv source_geometry_uv;
static int source_geometry_uv_ready=0;
/* Original C5 node hierarchy only; no animation or skinning is inferred. */
static P3DOriginalSkeleton preview_skeleton;
/* C151: original track owners are preflighted only; no unverified motion. */
static P3DSourceTrackBindings preview_track_bindings;
static P3DAnimationClip preview_animation;
static P3DAnimationLibrary preview_animation_library;
static P3DMaterialMap preview_materials;
static P3DSourceMaterialMap preview_source_materials;
static P3DSourceShaderCaps preview_source_shaders;
static P3DSourceMaterialWords preview_source_words;
static P3DSourceColorRanges preview_color_ranges;
static P3DTextureManifest preview_textures;
static int material_references_ready=0;
/* C127: complete source-checked face map, never a guessed sampler role. */
static int source_face_textures[600];
static int source_face_map_ready=0;
static P3DTexturePixels preview_pixels;
static int texture_payload_ready=0;
static P3DPreviewTextureSet preview_gl_textures;
/* Native material ranges must refer to exact original-source triangle order. */
static P3DMaterialMap native_materials;
static P3DSourceMaterialMap native_source_materials;
static P3DSourceShaderCaps native_shader_caps;
static P3DSourceMaterialWords native_source_words;
static P3DSourceColorRanges native_color_ranges;
static P3DTextureManifest native_textures;
static P3DDsMaterialTextureCache native_texture_cache;
static char native_texture_directory[80];
static char native_texture_path[112];
static int native_material_ready=0;
static const char *native_texture_resolve(void *opaque,unsigned texture_id){
    (void)opaque;
    int n=snprintf(native_texture_path,sizeof(native_texture_path),
                   "%s/t%03u.p3px",native_texture_directory,texture_id);
    return n>0&&(unsigned)n<sizeof(native_texture_path)
        ?native_texture_path:NULL;
}

static P3DAnimationPlayback animation_playback;
static P3DModelMap species_models;
static P3DFormMap alternate_models;
static P3DFormNames form_names;
static int selected_form=0;
static int move_catalog_ready=0;
static int dex_text_ready=0;
/* C333 optional real-source sidecar. Never substitute guessed species data. */
static P3DSpeciesDetails dex_details;
static int dex_details_ready=0;
static int dex_detail_tab=0; /* 0 original entry, 1-4 optional details */
static int search_region=0;
static int search_scope=0;
static int search_field=P3D_DEX_SEARCH_NAME;
/* C231: numeric browsing remains usable if original text is unavailable,
 * but active text/region/scope filters require an actual matching entry. */
static int search_filtered(void){
    return state.search_query[0]!=0 || search_region!=0 ||
           search_scope!=P3D_DEX_SCOPE_ALL ||
           search_field!=P3D_DEX_SEARCH_NAME;
}
static int search_actionable(void){
    return !search_filtered() || (dex_text_ready &&
        p3dDexSelectionMatches(state.search_query,state.selected_dex,
            search_field,search_region,search_scope,&records,&state));
}
static void refresh_search_selection(void){
    if(search_filtered() && dex_text_ready)
        (void)p3dDexRefreshSelection(state.search_query,&state.selected_dex,
            search_field,search_region,search_scope,&records,&state);
}
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
static P3DHomeHotspots original_home_hotspots;
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
    original_art_available=prefer_original_art&&nitro_ready&&
        !(page==P3D_PAGE_DEX && dex_detail_tab) &&
        p3dOriginalUiPageLoad(page);
    /* Source 3DS icons are not located at development text-menu rows.
     * Only authentic privately measured original art hitboxes may route
     * touches on original HOME artwork; keyboard navigation always works. */
    if(page==P3D_PAGE_HOME){
        (void)p3dHomeHotspotsLoad(&original_home_hotspots,
                                 "nitro:/ui/home_hotspots.p3hm");
    }else original_home_hotspots.ready=0;
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
    /* Optional form-specific metadata is never reconstructed from model
     * resources or public species databases. An absent private sidecar
     * becomes an explicitly unavailable detail screen. */
    p3dSpeciesDetailsClear(&dex_details);
    dex_details_ready=0;
    if(nitro_ready && !title_active && dex_index>=0 && dex_index<649){
        char details_path[80];
        if(p3dSpeciesDetailPath(details_path,dex_index,selected_form))
            dex_details_ready=p3dSpeciesDetailsLoad(
                details_path,dex_index,selected_form,&dex_details);
    }
    /* Source-locked Nitro Engine/DSMA model is released before switching
     * form/species; never carry an old Pokémon into the new entry. */
    p3dNitroBridgeUnload();
    /* Free all prior per-material VRAM allocations on species/form changes. */
    p3dPreviewTextureSetRelease(&preview_gl_textures);
    p3dDsMaterialTextureCacheDestroy(&native_texture_cache);
    native_material_ready=0;
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
    int legacy_preview_found=preview_ready&&resource>=0&&previewStreamLoad(resource);
    /* C248: native P3VX/P3IX can be staged without a legacy DS3M/P3CS
     * preview directory. Attempt only with mounted NitroFS and a resolved
     * model resource; the paired native reader still validates both files.
     * CRC/bounds prove transport, NOT original 3DS renderer provenance.
     * Missing/corrupt pairs fall back to a loaded legacy preview if present. */
    p3dVerifiedGeometryPairClear(&source_geometry_pair);
    p3dVerifiedVertexUvClear(&source_geometry_uv);
    source_geometry_uv_ready=0;
    source_geometry_ready=0;
    if(nitro_ready&&resource>=0){
        char vertex_path[80],index_path[80];
        snprintf(vertex_path,sizeof(vertex_path),
                 "nitro:/geometry/p%03d.p3vx",resource);
        snprintf(index_path,sizeof(index_path),
                 "nitro:/geometry/p%03d.p3ix",resource);
        source_geometry_ready=p3dVerifiedGeometryPairLoad(
            &source_geometry_pair,vertex_path,index_path,(uint16_t)resource);
        if(source_geometry_ready){
            snprintf(vertex_path,sizeof(vertex_path),
                     "nitro:/geometry/p%03d.p3vu",resource);
            source_geometry_uv_ready=p3dVerifiedVertexUvLoad(
                &source_geometry_uv,vertex_path,&source_geometry_pair);
        }
    }
    preview_found=legacy_preview_found||source_geometry_ready;
    /* Reuse verified original P3VX/P3IX, not procedural geometry.
     * A private P3NE sidecar binds the Nitro Engine display-list/DSMA
     * conversion to these exact pair bytes; absence is harmless. */
    if(source_geometry_ready)
        (void)p3dNitroBridgeLoad((uint16_t)resource,
            source_geometry_pair.vx,source_geometry_pair.vx_size,
            source_geometry_pair.ix,source_geometry_pair.ix_size);
    /* Native material indices must cover exact P3VX/P3IX source triangles,
     * not the independently reduced DS3M order. The conservative source
     * draw gate currently supports at most 600 triangles. */
    if(nitro_ready && source_geometry_ready && source_geometry_uv_ready &&
       source_geometry_pair.triangles<=600u){
        unsigned count=(unsigned)source_geometry_pair.triangles;
        P3DSourceMaterialWords *words=&native_source_words;
        snprintf(clip_path,sizeof(clip_path),"nitro:/materials/p%03d.p3mt",resource);
        if(p3dMaterialMapLoad(&native_materials,clip_path,count)){
            snprintf(clip_path,sizeof(clip_path),"nitro:/materials/p%03d.p3tx",resource);
            if(p3dTextureManifestLoad(&native_textures,clip_path)){
                snprintf(clip_path,sizeof(clip_path),"nitro:/materials/p%03d.p3mr",resource);
                if(p3dSourceMaterialLoad(&native_source_materials,clip_path,
                                         (unsigned)resource,count)){
                    snprintf(clip_path,sizeof(clip_path),"nitro:/materials/p%03d.p3sc",resource);
                    if(p3dSourceShaderCapsLoad(&native_shader_caps,clip_path,
                                               (unsigned)resource)){
                        snprintf(clip_path,sizeof(clip_path),
                                 "nitro:/materials/p%03d.p3sw",resource);
                        if(p3dSourceMaterialWordsLoad(words,clip_path,(unsigned)resource)
                           && p3dSourceMaterialWordsMatch(
                               words,&native_shader_caps,&native_source_materials,
                               (unsigned)resource,count)
                           && p3dSourceColorRangesBuild(
                               &native_color_ranges,words,&native_shader_caps,
                               &native_source_materials,&native_materials,
                               &native_textures,(unsigned)resource,count)
                           && native_color_ranges.approved==native_materials.count
                           && native_color_ranges.count==native_materials.count
                           && p3dModelMaterialTexturesMatchMesh(
                               &native_materials,&native_textures,count)){
                            snprintf(native_texture_directory,
                                     sizeof(native_texture_directory),
                                     "nitro:/textures/p%03d",resource);
                            native_material_ready=p3dDsMaterialTextureCacheInit(
                                &native_texture_cache,&native_textures,
                                native_texture_resolve,NULL);
                            /* C312: copy the entire validated material set
                             * during model loading rather than while GX
                             * rasterizes its first textured model frame. */
                            if(native_material_ready &&
                               !p3dDsMaterialUvPrepare(
                                   &source_geometry_pair,&source_geometry_uv,
                                   &native_source_materials,&native_materials,
                                   &native_textures,&native_shader_caps,
                                   &native_texture_cache,&preview_pixels)){
                                p3dDsMaterialTextureCacheDestroy(
                                    &native_texture_cache);
                                native_material_ready=0;
                            }
                        }
                    }
                }
            }
        }
    }
    p3dOriginalSkeletonClear(&preview_skeleton);
    p3dSourceTrackBindingsClear(&preview_track_bindings);
    preview_animation.ready=0;
    preview_animation_library.ready=0;
    preview_materials.ready=0;
    preview_source_materials.ready=0;
    preview_source_shaders.ready=0;
    preview_source_words.ready=0;
    preview_color_ranges.ready=0;
    preview_textures.ready=0;
    material_references_ready=0;
    source_face_map_ready=0;
    texture_payload_ready=0;
    preview_pixels.ready=0;
    p3dPlaybackReset(&animation_playback);
    if(preview_found){
        /* C149: optional private original node table, read-only. The source
         * hierarchy is not sufficient to deform source geometry without
         * original skin weights, node-to-mesh bindings and action clips. */
        snprintf(clip_path,sizeof(clip_path),"nitro:/skeleton/p%03d.p3sk",resource);
        if(p3dOriginalSkeletonLoad(&preview_skeleton,clip_path,(unsigned)resource)){
            /* Private P3TB v1 names, original owner indices and CRC must
             * match the exact selected P3SK. This is a data association,
             * not permission to animate or skin geometry. */
            snprintf(clip_path,sizeof(clip_path),"nitro:/track_bindings/p%03d.p3tb",resource);
            (void)p3dSourceTrackBindingsLoad(&preview_track_bindings,
                                              &preview_skeleton,clip_path,(unsigned)resource);
        }
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
            /* C127: validate all source-backed face texture assignments before
             * permitting any native texture upload. Unknown sampler roles
             * still remain disabled by the existing color-range gate. */
            if(material_references_ready)
                source_face_map_ready=p3dSourceCandidateTextureMap(
                    &preview_source_materials,&preview_materials,
                    &preview_textures,(unsigned)resource,
                    (unsigned)previewStreamTriangleCount(),
                    source_face_textures,600);
            if(!source_face_map_ready)material_references_ready=0;
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
    int next_preview=preview_found &&
        ((!home && state.page==P3D_PAGE_DEX) ||
         (title_active && title_idle.active));
    /* C252: a 3D frame remains in the hardware BG0 framebuffer until the
     * next glFlush. When a mapped model is followed by an unavailable model
     * or HOME, render_model() stops flushing and its last triangle can stay
     * visible over the text console indefinitely. Present one EMPTY frame
     * on the preview -> non-preview transition; never draw guessed geometry
     * or clear every idle menu frame. The actual emulator screenshot gate
     * must prove the previous triangle is gone. */
    if(display_preview && !next_preview){
        glDisable(GL_TEXTURE_2D);
        glBindTexture(0,0);
        glFlush(0);
    }
    display_preview=next_preview;
}
static void render_model(void){
    if(!display_preview)return;
    glViewport(0,0,255,191);
    glMatrixMode(GL_PROJECTION);glLoadIdentity();
    gluPerspective(50,256.0/192.0,0.1,20.0);
    glMatrixMode(GL_MODELVIEW);glLoadIdentity();
    glTranslatef32(0,0,floattof32(-3));
    glRotateYi(model_yaw);
    if(preview_animation.ready && !source_geometry_ready){
        P3DAnimationFrame pose;
        if(p3dAnimationPoseAt(&preview_animation,animation_playback.tick,&pose)){
            glRotateXi(pose.pitch);
            glRotateYi(pose.yaw);
            glRotateZi(pose.roll);
        }
    }
    glPolyFmt(POLY_ALPHA(31)|POLY_CULL_NONE);
    if(source_geometry_ready){
        /* Optional Nitro Engine/DSMA uses the converted ORIGINAL source
         * geometry. Keep verified source-material texturing ahead of a
         * converted untextured display list, and retain old GL fallback. */
        if(!native_material_ready && p3dNitroBridgeDraw()){
            glFlush(0);
            return;
        }
        /* Source indices and 4.12 XYZ were validated as one private pair.
         * No source sampler, skin weights or animation role is inferred. */
        uint32_t drawn=0;
        glDisable(GL_TEXTURE_2D);
        glBindTexture(0,0);
        glColor3b(192,224,232);
        int native_draw_ok=0;
        if(native_material_ready){
            glEnable(GL_TEXTURE_2D);
            glColor3b(255,255,255);
            native_draw_ok=p3dDsMaterialUvDraw(
                &source_geometry_pair,&source_geometry_uv,
                &native_source_materials,&native_materials,&native_textures,
                &native_shader_caps,&native_texture_cache,&preview_pixels,&drawn);
            if(!native_draw_ok){
                /* C306: texturing is a GPU-wide display control. Turning
                 * it off immediately after submitting polygon commands
                 * makes the deferred rasterizer sample solid white.
                 * Retain mapping through glFlush and the displayed frame;
                 * only clear it for a real untextured fallback. */
                glDisable(GL_TEXTURE_2D);
                glBindTexture(0,0);
                /* C305: a failed upload invalidates the entire texture cache.
                 * Disable repeated attempts until the next model reload,
                 * leaving the verified untextured geometry fallback active. */
                p3dDsMaterialTextureCacheDestroy(&native_texture_cache);
                native_material_ready=0;
            }
        }
        if(!native_draw_ok){
            drawn=0;
            glColor3b(192,224,232);
            native_draw_ok=source_geometry_uv_ready
            ?p3dVerifiedPrimitiveUvDraw(&source_geometry_pair,
                                        &source_geometry_uv,&drawn)
            :p3dVerifiedPrimitiveDraw(source_geometry_pair.ix,
                source_geometry_pair.ix_size,source_geometry_pair.model,
                source_geometry_pair.meshes,source_geometry_pair.mesh_count,
                &drawn);
        }
        if(!native_draw_ok){
            /* Fail closed if the verified geometry changes or cannot draw. */
            p3dVerifiedGeometryPairClear(&source_geometry_pair);
            source_geometry_ready=0;
            if(previewStreamHasModel())previewStreamDraw();
        }
        glFlush(0);
        return;
    }
    if(preview_gl_textures.ready){
        /* A texture manifest alone does not prove that material ranges form
         * an exact partition of the preview mesh. Never silently omit or
         * double-draw triangles if a private manifest has gaps/overlaps or
         * unordered ranges; preserve the complete untextured geometry. */
        unsigned covered=0;
        int partition_valid=preview_materials.count>0;
        const unsigned triangle_total=(unsigned)previewStreamTriangleCount();
        for(unsigned i=0;i<preview_materials.count;i++){
            const P3DMaterialRange *range=&preview_materials.ranges[i];
            if(range->first_triangle != covered ||
               range->triangle_count == 0 ||
               range->triangle_count > triangle_total-covered){
                partition_valid=0;
                break;
            }
            covered += range->triangle_count;
        }
        if(!partition_valid || covered != triangle_total){
            glDisable(GL_TEXTURE_2D);
            glBindTexture(0,0);
            previewStreamDraw();
            glFlush(0);
            return;
        }
        /* C115: draw EVERY original triangle exactly once. Only material
         * ranges supported by original-source C5 simple-colormap references
         * use a color texture. Unknown original bump/effect/dual-sampler
         * ranges keep their original geometry and untextured face colors. */
        for(unsigned i=0;i<preview_materials.count;i++){
            const P3DMaterialRange *range=&preview_materials.ranges[i];
            /* C139: the renderer itself repeats the source face, sampler
             * capability and exact normalized UV checks immediately before
             * binding GL texture state. Unsafe ranges remain untextured. */
            int source_colormap_approved=preview_color_ranges.ready &&
                i<preview_color_ranges.count && preview_color_ranges.enabled[i];
            int normalized_paired_uv=previewStreamHasUv() &&
                previewStreamUvRangeUnit(range->first_triangle,
                                         range->triangle_count);
            int range_ready=source_face_map_ready &&
                p3dSourceCandidateTextureRangeReady(
                    source_face_textures,600,
                    (unsigned)previewStreamTriangleCount(),
                    range->first_triangle,range->triangle_count,
                    range->texture_id,
                    source_colormap_approved,normalized_paired_uv);
            const P3DPreviewTexture *tex=range_ready?
                p3dPreviewTextureSetFind(&preview_gl_textures,range->texture_id):NULL;
            if(tex && tex->gl_id>0){
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
    view.selected_form=(uint16_t)selected_form;
    view.album_selected=(uint8_t)album_selected;
    view.records_recent_cursor=(uint8_t)records_recent_cursor;
    view.move_show_effect=(uint8_t)(move_show_effect!=0);
    view.search_region=(uint8_t)search_region;
    view.search_scope=(uint8_t)search_scope;
    view.search_field=(uint8_t)search_field;
    view.move_text_offset=(uint16_t)move_text_offset;
    view.menu_cursor=(uint16_t)state.cursor;
    view.favorite_cursor=(uint8_t)state.favorite_cursor;
    memcpy(view.search_query,state.search_query,sizeof(view.search_query));
    view.search_letter=(uint8_t)state.search_letter;
    view.challenge_mode=(uint8_t)quiz.mode_cursor;
    view.type_attack=(uint8_t)attack_type;
    view.type_defend=(uint8_t)defend_type;
    view.type_defend2_plus_one=(uint8_t)(defend_type2+1);
    view.favorites_selected=(uint8_t)favorite_index;
    view.dex_detail_tab=(uint8_t)(!home && state.page==P3D_PAGE_DEX?
                                  dex_detail_tab:0);
    /* An active question/review is a real resume state, not just a mode.
     * The exact seed, asked set, choices and already-counted totals travel
     * together in the CRC-protected optional P3RV v4 checkpoint. */
    if(!home && state.page==P3D_PAGE_CHALLENGE &&
       (quiz.stage==P3D_CHALLENGE_QUESTION ||
        quiz.stage==P3D_CHALLENGE_REVIEW)){
        view.quiz_active=1;
        view.quiz=quiz;
        view.challenge_answer_total=(uint32_t)challenge_answer_total;
        view.challenge_correct_total=(uint32_t)challenge_correct_total;
        view.challenge_recorded_rounds=records.rounds;
    }
    return view;
}
/* Commit page/selection immediately when it changes. The independent
 * CRC P3RV checkpoint survives even if older P3SV progress is missing. */
static int save_resume_checkpoint(void){
    P3DResumeState view;
    if(!storage_ready)return 0;
    view=current_resume();
    if(last_checkpoint_valid &&
       memcmp(&view,&last_checkpoint,sizeof(view))==0)return 1;
    if(!p3dResumeStore(P3D_SAVE_BASE,&view))return 0;
    last_checkpoint=view;
    last_checkpoint_valid=1;
    checkpoint_ticks=0;
    return 1;
}
static int save_progress(void){
    P3DSaveState record;
    if(!storage_ready){save_message=2;return 0;}
    if(!p3dGameSaveCapture(&record,&state,dex_index,move_index,challenge_correct_total,challenge_answer_total)){
        save_message=2;
        return 0;
    }
    int saved=p3dSaveStore(P3D_SAVE_BASE,&record)?1:0;
    if(saved && !save_resume_checkpoint())saved=0;
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
            printf("START: %s\n",dex_detail_tab?"close details":"details");
            if(dex_detail_tab)
                printf("Details %s %d/4 (L/R)\n",
                       p3dSpeciesDetailTabName(dex_detail_tab),dex_detail_tab);
            printf("LEFT/RIGHT: browse entries\n");
            printf("Form: %s",selected_form?"alternate":"base");
            if(selected_form){
                const char *name=p3dFormName(&form_names,dex_index,selected_form);
                if(name)printf(" %s",name);
                else printf(" #%d",selected_form);
            }
            printf("\nY: cycle verified forms\n");
            if(preview_found){
                printf("Source mesh: %lu tris\n",
                       source_geometry_ready ? (unsigned long)source_geometry_pair.triangles
                                             : (unsigned long)previewStreamTriangleCount());
                if(source_geometry_ready)printf("Native material: %s\n",native_material_ready?"strict candidate":"untextured fallback");
                printf("Material refs: %s\n",material_references_ready?"verified":"unavailable");
                printf("Texture data: %s\n",texture_payload_ready?"verified":"unavailable");
                printf("Native textures: %u\n",preview_gl_textures.count);
            }
            else printf("Source mesh unavailable\n");
            if(preview_found){
                if(preview_animation.ready && source_geometry_ready)
                    printf("Source geometry: animation not verified\n");
                else if(preview_animation.ready){
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
                if(search_actionable() && p3dDexTextRead(state.selected_dex,&entry))
                    printf("Original name: %.28s\n",entry.name);
                else printf("No matching original entry\n");
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
            if(search_actionable()){
                printf("A: open this Pokemon\n");
                printf("Y: toggle favorite (%s)\n",p3dFavoriteContains(&state,state.selected_dex)?"saved":"not saved");
            }else printf("A/Y: select a matching entry\n");
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
            printf("A: Pokemon Search  Y: Challenge\n");
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
            }else if(quiz.stage==P3D_CHALLENGE_REVIEW){
                printf("%s\n",quiz.selected==quiz.correct?"Correct!":"Incorrect");
                P3DChallengeText original;
                if(quiz.mode==P3D_CHALLENGE_TEXT_MODE &&
                   p3dChallengeTextLoad(&original,&quiz)){
                    printf("Your answer: %.28s\n",original.names[quiz.selected]);
                    printf("Correct answer: %.28s\n",original.names[quiz.correct]);
                }else{
                    printf("Your answer: Pokemon #%03d\n",quiz.choices[quiz.selected]+1);
                    printf("Correct answer: #%03d\n",quiz.pokemon+1);
                }
                printf("Score: %d / %d\n",quiz.score,quiz.question+1);
                printf("A: %s\n",quiz.question+1==P3D_CHALLENGE_QUESTIONS?
                       "show results":"next question");
            }else{
                printf("Question %d / %d\n",quiz.question+1,P3D_CHALLENGE_QUESTIONS);
                if(quiz.mode==P3D_CHALLENGE_TEXT_MODE){
                    P3DChallengeText original;
                    if(p3dChallengeTextLoad(&original,&quiz)){
                        char first[29],second[29];
                        p3dChallengeClue(original.clue,quiz.clue_page,first,second);
                        printf("Original Pokedex clue %d/%d:\n",quiz.clue_page+1,original.pages);
                        printf("%.28s\n%.28s\n",first,second);
                        printf("L/R: clue page\n");
                        for(int i=0;i<P3D_CHALLENGE_OPTIONS;i++)
                            printf("%c %d: %.23s\n",quiz.selected==i?'>':' ',i+1,original.names[i]);
                    }else{
                        printf("Original P3DX clue/options missing.\n");
                        printf("Answers disabled (no substitutes).\n");
                    }
                }else{
                    printf("Choose Pokemon number:\n");
                    for(int i=0;i<P3D_CHALLENGE_OPTIONS;i++)
                        printf("%c %d: #%03d\n",quiz.selected==i?'>':' ',i+1,quiz.choices[i]+1);
                }
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
        if(state.page==P3D_PAGE_DEX && dex_detail_tab){
            printf("\x1b[10;1H%s %d/4 - #%03d",
                   p3dSpeciesDetailTabName(dex_detail_tab),
                   dex_detail_tab,dex_index+1);
            if(!dex_details_ready){
                printf("\x1b[12;1HOriginal detail unavailable");
                printf("\x1b[14;1HNo source-verified P3SD");
                printf("\x1b[15;1Hfor this species/form");
            }else if(dex_detail_tab==1){
                if(dex_details.fields&P3D_DETAIL_STATS){
                    printf("\x1b[12;1HHP:%3u   ATK:%3u  DEF:%3u",
                           dex_details.stats[0],dex_details.stats[1],dex_details.stats[2]);
                    printf("\x1b[14;1HSPA:%3u  SPD:%3u  SPE:%3u",
                           dex_details.stats[3],dex_details.stats[4],dex_details.stats[5]);
                }else printf("\x1b[12;1HOriginal stats unavailable");
            }else if(dex_detail_tab==2){
                if(dex_details.fields&P3D_DETAIL_ABILITIES){
                    for(unsigned i=0;i<dex_details.abilities_count;i++)
                        printf("\x1b[%u;1HAbility ID %u",12u+i*2u,
                               dex_details.ability_ids[i]);
                    if(!dex_details.abilities_count)
                        printf("\x1b[12;1HNo verified ability IDs");
                }else printf("\x1b[12;1HOriginal abilities unavailable");
            }else if(dex_detail_tab==3){
                if(dex_details.fields&P3D_DETAIL_EVOLUTIONS){
                    for(unsigned i=0;i<dex_details.evolutions_count;i++)
                        printf("\x1b[%u;1HTo Pokemon #%03u",12u+i*2u,
                               dex_details.evolutions[i]+1);
                    if(!dex_details.evolutions_count)
                        printf("\x1b[12;1HNo listed evolutions");
                }else printf("\x1b[12;1HOriginal evolution unavailable");
            }else if(dex_detail_tab==4){
                if(dex_details.fields&P3D_DETAIL_MOVES){
                    for(unsigned i=0;i<dex_details.moves_count;i++){
                        unsigned index=dex_details.move_indices[i];
                        P3DMove move;
                        if(move_catalog_ready&&p3dMoveDexRead((int)index,&move))
                            printf("\x1b[%u;1H%03u %.23s",12u+i*2u,index+1,move.name);
                        else printf("\x1b[%u;1HMove reference #%03u",12u+i*2u,index+1);
                    }
                    if(!dex_details.moves_count)
                        printf("\x1b[12;1HNo verified learnset refs");
                }else printf("\x1b[12;1HOriginal learnset unavailable");
            }
            printf("\x1b[19;1HSTART/B: entry  L/R: tabs");
            printf("\x1b[21;1H< PREV TAB      NEXT TAB >");
            printf("\x1b[23;1H< SPECIES       SPECIES >");
        }else if(state.page==P3D_PAGE_DEX){
            if(dex_text_ready){
                P3DDexText entry;
                if(p3dDexTextRead(dex_index,&entry)){
                    printf("\x1b[11;1H%.28s",entry.name);
                    printf("\x1b[21;1HHeight %.10s Wt %.8s",entry.height,entry.weight);
                    printf("\x1b[23;1H%.28s",entry.description);
                }
            }
            if(preview_animation.ready && !source_geometry_ready)
                printf("\x1b[12;1H[%-6s]      [Restart]",
                       animation_playback.paused?"Resume":"Pause");
            printf("\x1b[13;1HPokemon %03d of 649",dex_index+1);
            printf("\x1b[15;1HLEFT/RIGHT: browse");
            if(selected_form){
                const char *name=p3dFormName(&form_names,dex_index,selected_form);
                if(name)printf("\x1b[17;1HForm: %.24s",name);
                else printf("\x1b[17;1HAlternate form #%d",selected_form);
            }
            else printf("\x1b[17;1HBase form");
            printf("\x1b[19;1HY: next verified form");
            printf("\x1b[24;1HSTART: original data details");
        }else if(state.page==P3D_PAGE_SEARCH){
            printf("\x1b[9;1H%.28s",state.search_query[0]?state.search_query:"NAME / TEXT SEARCH");
            /* One-based console rows share exact touch coordinates in C83. */
            printf("\x1b[%d;1HRegion: %.8s",P3D_SEARCH_REGION_ROW,
                   p3dDexRegionName(search_region));
            printf("\x1b[%d;17HScope: %.9s",P3D_SEARCH_REGION_ROW,
                   p3dDexScopeName(search_scope));
            printf("\x1b[%d;1HField: %s",P3D_SEARCH_FIELD_ROW,
                   search_field==P3D_DEX_SEARCH_NAME?"NAME":"DESCRIPTION");
            if(dex_text_ready){
                P3DDexText entry;
                if(search_actionable() && p3dDexTextRead(state.selected_dex,&entry))
                    printf("\x1b[%d;1H#%03d %.23s",P3D_SEARCH_RESULT_ROW,
                           state.selected_dex+1,entry.name);
                else printf("\x1b[%d;1HNo matching original entry",P3D_SEARCH_RESULT_ROW);
            }else printf("\x1b[%d;1HOriginal text unavailable",P3D_SEARCH_RESULT_ROW);
            printf("\x1b[%d;1H  A B C D E F G H I J K L M",P3D_SEARCH_KEYBOARD_ROW);
            printf("\x1b[%d;1H  N O P Q R S T U V W X Y Z",P3D_SEARCH_KEYBOARD_ROW+2);
            printf("\x1b[%d;1HDEL       NEXT      PREV",P3D_SEARCH_ACTIONS_ROW);
            printf("\x1b[24;1HTap region/scope/field above");
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
            printf("\x1b[22;1HA: Search  Y: Challenge");
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
            printf("\x1b[17;1HBookmarks: %s",bookmark_settings.active_list?"Moves":"Pokemon");
            const P3DBookmarkList *visible_bookmarks=bookmark_settings.active_list?
                &bookmark_settings.moves:&bookmark_settings.pokemon;
            printf("\x1b[18;1HCount: %u / %u",visible_bookmarks->count,
                   P3D_BOOKMARK_CAPACITY);
            if(visible_bookmarks->count && bookmark_cursor<visible_bookmarks->count)
                printf("\x1b[19;1HSelected: %u (ID %u)",bookmark_cursor+1,
                       (unsigned)visible_bookmarks->ids[bookmark_cursor]+1);
            else printf("\x1b[19;1HNo saved bookmarks");
            printf("\x1b[20;1HL/R: list  UP/DOWN: slot");
            printf("\x1b[21;1HSELECT: %s",
                   visible_bookmarks->editing?"delete":"open");
            printf("\x1b[22;1HY: edit  START: add");
            if(!storage_ready)printf("\x1b[23;1HStorage unavailable");
            else if(bookmark_settings.dirty)printf("\x1b[23;1HBookmark save pending");
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
            }else if(quiz.stage==P3D_CHALLENGE_REVIEW){
                printf("\x1b[11;1H%s",quiz.selected==quiz.correct?"Correct!":"Incorrect");
                P3DChallengeText original;
                if(quiz.mode==P3D_CHALLENGE_TEXT_MODE &&
                   p3dChallengeTextLoad(&original,&quiz)){
                    printf("\x1b[13;1HAnswer: %.23s",original.names[quiz.correct]);
                    printf("\x1b[15;1HYou chose: %.21s",original.names[quiz.selected]);
                }else{
                    printf("\x1b[13;1HAnswer: Pokemon #%03d",quiz.pokemon+1);
                    printf("\x1b[15;1HYou chose: #%03d",quiz.choices[quiz.selected]+1);
                }
                printf("\x1b[19;2HA / tap: %s",quiz.question+1==P3D_CHALLENGE_QUESTIONS?
                       "results":"continue");
            }else{
                printf("\x1b[8;1HQuestion %d / %d",quiz.question+1,P3D_CHALLENGE_QUESTIONS);
                P3DChallengeText original;
                if(quiz.mode==P3D_CHALLENGE_TEXT_MODE){
                    if(p3dChallengeTextLoad(&original,&quiz)){
                        for(int i=0;i<P3D_CHALLENGE_OPTIONS;i++)
                            printf("\x1b[%d;2H%c %.24s",11+i*3,
                                   quiz.selected==i?'>':' ',original.names[i]);
                        printf("\x1b[23;1HTap answer or press A");
                    }else{
                        printf("\x1b[12;1HOriginal P3DX text missing");
                        printf("\x1b[14;1HQuiz answers disabled");
                    }
                }else{
                    for(int i=0;i<P3D_CHALLENGE_OPTIONS;i++)
                        printf("\x1b[%d;2H%c Pokemon #%03d",11+i*3,
                               quiz.selected==i?'>':' ',quiz.choices[i]+1);
                    printf("\x1b[23;1HTap answer or press A");
                }
            }
        }else{
            printf("\x1b[13;1HFeature implementation pending");
        }
        if(state.page==P3D_PAGE_CHALLENGE &&
           (quiz.stage==P3D_CHALLENGE_QUESTION ||
            quiz.stage==P3D_CHALLENGE_REVIEW))
            printf("\x1b[24;1HB: Return to menu");
        else printf("\x1b[17;1HPress B to go back");
    }
}
int main(void) {
    P3DCapabilities caps=p3dCapabilities(isDSiMode()?1:0,0,0);
    videoSetMode(MODE_0_3D);
    glInit();
    /* Only Nitro Engine model + DSMA animation subsystems; NE_Init3D()
     * would reset the existing top 3D/bottom text screen layout. */
    (void)p3dNitroBridgeInit();
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
    p3dBookmarkSettingsInit(&bookmark_settings);
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
        (void)p3dBookmarkSessionLoad(&bookmark_settings,P3D_SAVE_BASE);
        /* Bad or missing records slots leave a clean in-memory history. */
        (void)p3dRecordsLoad(P3D_SAVE_BASE,&records);
        P3DSaveState record;
        if(p3dSaveLoad(P3D_SAVE_BASE,&record)){
            if(p3dGameSaveRestore(&record,&state,&dex_index,&move_index)){
                challenge_correct_total=(int)record.challenge_correct;
                challenge_answer_total=(int)record.challenge_total;
                save_message=3;
            }
        }
        /* P3RV is independent of legacy P3SV/P3RC: an intact last-screen
         * checkpoint can restore a page even if progress is not available. */
        P3DResumeState resume;
        if(p3dResumeRestoreBoot(P3D_SAVE_BASE,&resume,caps,
                                &home,&state,&highlighted)){
            dex_index=(int)resume.dex;
            dex_detail_tab=(int)resume.dex_detail_tab;
            move_index=(int)resume.move;
            records_tab=(int)resume.records_tab;
            album_offset=(size_t)resume.album_page*P3D_ALBUM_PAGE_MAX;
            album_selected=resume.album_selected;
            records_recent_cursor=resume.records_recent_cursor;
            move_show_effect=resume.move_show_effect;
            move_text_offset=resume.move_text_offset;
            search_region=resume.search_region;
            search_scope=resume.search_scope;
            search_field=resume.search_field;
            memcpy(state.search_query,resume.search_query,
                   sizeof(state.search_query));
            state.search_letter=resume.search_letter?
                resume.search_letter:'A';
            /* C332: recover exactly the validated question/review. The
             * saved v4 answer totals may be ahead of old P3SV after power
             * loss; never add a REVIEW answer twice on boot. If P3SV has
             * since advanced beyond this checkpoint, fail back to picker. */
            quiz.mode_cursor=resume.challenge_mode;
            if(!home && state.page==P3D_PAGE_CHALLENGE &&
               p3dResumeCanRestoreQuiz(&resume,
                   (uint32_t)challenge_correct_total,
                   (uint32_t)challenge_answer_total,records.rounds)){
                quiz=resume.quiz;
                challenge_answer_total=(int)resume.challenge_answer_total;
                challenge_correct_total=(int)resume.challenge_correct_total;
                challenge_seed=quiz.seed;
                progress_dirty=1; /* Repair lagging P3SV if necessary. */
            }else{
                if(quiz.mode_cursor>=p3dChallengeAvailableModes(
                       challenge_answer_total))
                    quiz.mode_cursor=p3dChallengeAvailableModes(
                       challenge_answer_total)-1;
            }
            attack_type=resume.type_attack;
            defend_type=resume.type_defend;
            defend_type2=(int)resume.type_defend2_plus_one-1;
            favorite_index=resume.favorites_selected;
            if(favorite_index>=state.favorites_count)favorite_index=0;
            /* A saved form must exist in the actual recovered original
             * source map for this species; otherwise retain the base form. */
            selected_form=resume.selected_form &&
                p3dFormResolve(&alternate_models,dex_index,
                               resume.selected_form)>=0
                            ?resume.selected_form:0;
            last_checkpoint=resume;
            last_checkpoint_valid=1;
        }
    }
    /* libfat mounts the default writable device as fat:/; create the album
     * directory only when the device is actually available. */
    if(storage_ready)album_ready=p3dPhotoAlbumOpen(&photo_album,"fat:/Pokedex 3D Pro/Photos");
    if(last_checkpoint_valid && state.page==P3D_PAGE_ALBUM){
        /* Removed/deleted photos may invalidate a saved album selection. */
        char names[P3D_ALBUM_PAGE_MAX][32];
        size_t total=0;
        size_t shown=album_ready?
            p3dPhotoAlbumPage(&photo_album,names,P3D_ALBUM_PAGE_MAX,
                               album_offset,&total):0;
        if(!shown){
            album_offset=0;
            album_selected=0;
        }else if(album_selected>=shown){
            album_selected=shown-1;
        }
    }
    if(nitro_ready){
        preview_ready=previewStreamInit();
        /* Moves must remain available even if a model preview is missing. */
        move_catalog_ready=p3dMoveDexInit("nitro:/moves.p3dm");
        dex_text_ready=p3dDexTextInit("nitro:/data/dex_en.p3dx");
    }
    if(last_checkpoint_valid && state.page==P3D_PAGE_MOVES){
        /* Prevent a stale saved scroll after the private move text changes. */
        P3DMove entry;
        if(move_catalog_ready && p3dMoveDexRead(move_index,&entry))
            move_text_offset=p3dMoveTextScroll(
                move_text_offset,p3dMoveTextField(&entry,move_show_effect),0);
        else move_text_offset=0;
    }
    if(last_checkpoint_valid && state.page==P3D_PAGE_RECORDS &&
       (records_recent_cursor>=P3D_RECORD_RECENT ||
        records.recent[records_recent_cursor]==P3D_RECORD_NO_SPECIES))
        records_recent_cursor=0;
    reload_preview();
    count=(int)p3dMenuEntries(caps,pages);
    /* Reset/power-on with a valid checkpoint opens that same active page,
     * bypassing title. New games still use the genuine original 3DS title
     * when the private source art is present. */
    if(last_checkpoint_valid || !show_original_title())render();
    while(1) {
        swiWaitForVBlank();
        p3dNitroBridgeFrame();
        challenge_seed+=0x9E3779B9u; /* Vary each game session's quiz sequence. */
        scanKeys();
        unsigned down=keysDown();
        unsigned held=keysHeld();
#ifdef P3D_EMULATOR_DIAGNOSTICS
        /* C237: asset-free CI only, never enabled in original-asset ROMs.
         * Capture actual ARM9 libnds key state while X11 keys are held.
         * This is a diagnostic, not proof of a correct button mapping. */
        static unsigned c237_frame=0;
        if((++c237_frame % 5u)==0u || down){
            consoleSelect(&top_console);
            printf("\x1b[23;1Hdbg f%05lu d%04X h%04X  ",
                   (unsigned long)(c237_frame%100000u),down,held);
        }
#endif
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
                (void)save_resume_checkpoint();
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
                    p3dPlaybackAdvance(&animation_playback,&preview_animation,
                                      !source_geometry_ready);
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
        if((down&KEY_SELECT) && (home || state.page!=P3D_PAGE_SETTINGS)){
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
        if((down&KEY_START)&&progress_dirty && (home || state.page!=P3D_PAGE_SETTINGS)){
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
                int hit=-1;
                if(showing_original_art){
                    int page=p3dHomeHotspotsHit(&original_home_hotspots,
                                                point.px,point.py);
                    for(int i=0;i<count;i++)
                        if(page>=0 && pages[i]==(P3DPage)page){hit=i;break;}
                }else{
                    /* Text fallback positions are never used on source art. */
                    hit=p3dMenuTouchIndex(point.px,point.py,count,highlighted);
                }
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
                if(state.page==P3D_PAGE_DEX && dex_detail_tab){
                    dex_detail_tab=0;
                    art_page=-1;
                }else if(state.page==P3D_PAGE_ALBUM && album_confirm_delete){
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
                int touch_x=-1,touch_y=-1;
                /* The source-art bitmap has no verified text-mode hitboxes.
                 * Capture touch only on the visible text fallback screen. */
                if(!showing_original_art && (down&KEY_TOUCH)){
                    touchPosition point;
                    touchRead(&point);
                    touch_x=point.px;
                    touch_y=point.py;
                }
                /* Only picker/results can navigate to Type Matchups.
                 * Consume this key so destination's Y handler cannot run
                 * again in this same frame (Types -> Challenge bounce). */
                if((down&KEY_Y) && !(down&(KEY_A|KEY_TOUCH)) &&
                   (quiz.stage==P3D_CHALLENGE_PICKER||
                    quiz.stage==P3D_CHALLENGE_RESULTS)){
                    state.page=P3D_PAGE_TYPES;
                    down=0;
                    redraw=1;
                }else if(quiz.stage==P3D_CHALLENGE_PICKER||
                         quiz.stage==P3D_CHALLENGE_RESULTS){
                    if((down&KEY_A) && !(down&KEY_TOUCH)){
                        /* Preserve region selected in picker / replay. */
                        int mode=quiz.mode_cursor;
                        if(p3dChallengeBeginSession(&quiz,mode,&challenge_seed,
                                             challenge_answer_total))
                            redraw=1;
                    }
                }else if(quiz.stage==P3D_CHALLENGE_REVIEW){
                    /* Repeated A/touch while reviewing may only advance
                     * once. The final question's review precedes results. */
                    if(((down&KEY_A) && !(down&KEY_TOUCH))||
                       p3dChallengeTouchContinue(touch_x,touch_y)){
                        if((quiz.mode==P3D_CHALLENGE_TEXT_MODE?
                            p3dChallengeTextContinue(&quiz):
                            p3dChallengeContinue(&quiz))){
                            if(quiz.stage==P3D_CHALLENGE_RESULTS &&
                               p3dRecordsComplete(&records,quiz.mode,quiz.score)){
                                records_dirty=1;
                                progress_dirty=1;
                                /* Finish the prior round before a new one can
                                 * snapshot its P3RC round generation. P3RV
                                 * v3 clears active review before P3RC commits,
                                 * preventing an older v4 review from being
                                 * replayed as a second completed round. */
                                if(save_progress())progress_dirty=0;
                            }
                            redraw=1;
                        }
                    }
                }else if(quiz.stage==P3D_CHALLENGE_QUESTION){
                    int choice=-1;
                    if(quiz.mode==P3D_CHALLENGE_TEXT_MODE &&
                       (down&(KEY_L|KEY_R)) && !(down&(KEY_A|KEY_TOUCH)) &&
                       !((down&KEY_L) && (down&KEY_R))){
                        int direction=(down&KEY_R)?1:-1;
                        if(p3dChallengeTextPageStep(&quiz,direction))redraw=1;
                    }
                    if((down&KEY_UP) && quiz.selected>0){
                        quiz.selected--;
                        redraw=1;
                    }
                    if((down&KEY_DOWN) && quiz.selected<P3D_CHALLENGE_OPTIONS-1){
                        quiz.selected++;
                        redraw=1;
                    }
                    /* Touch and A cannot submit two answers in one VBlank.
                     * The first choice starts exactly at console row 11:
                     * 80px, followed by three 24px-high label rows. */
                    if(down&KEY_TOUCH)
                        choice=p3dChallengeTouchChoice(touch_x,touch_y);
                    else if(down&KEY_A)
                        choice=quiz.selected;
                    if(choice>=0){
                        int result=quiz.mode==P3D_CHALLENGE_TEXT_MODE?
                            p3dChallengeTextAnswer(&quiz,choice):
                            p3dChallengeAnswer(&quiz,choice);
                        if(result>=0 && challenge_answer_total<100000000){
                            challenge_answer_total++;
                            if(result)challenge_correct_total++;
                            progress_dirty=1;
                        }
                        if(result>=0)redraw=1;
                    }
                }
            }

            if(state.page==P3D_PAGE_SEARCH){
                /* One touch cannot also open a stale entry or a destination page.
                 * Bitmap artwork has NO text keyboard hitboxes. */
                int search_touched=(down&KEY_TOUCH)!=0;
                int search_navigation=0;
                if(search_touched && !showing_original_art){
                    touchPosition point;
                    touchRead(&point);
                    int action=p3dSearchTouchAction(point.px,point.py);
                    if(action>='A' && action<='Z'){
                        if(p3dDexQueryAppend(state.search_query,(char)action))
                            redraw=1;
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
                        if(hit>=0)state.selected_dex=hit;
                        redraw=1;
                    }
                    if(action && action!=P3D_SEARCH_TOUCH_NEXT &&
                       action!=P3D_SEARCH_TOUCH_PREVIOUS)
                        refresh_search_selection();
                }
                if(!search_touched){
                    if((down&KEY_R) && !(down&(KEY_A|KEY_X|KEY_Y|KEY_L))){
                        state.page=P3D_PAGE_SETTINGS;
                        search_navigation=1;
                        redraw=1;
                    }else if((down&KEY_L) && !(down&(KEY_A|KEY_X|KEY_Y))){
                        state.page=P3D_PAGE_MOVES;
                        search_navigation=1;
                        redraw=1;
                    }
                    /* X+arrows keep the existing original name-initial jump.
                     * Numeric arrows still browse when no X key is held. */
                    int source_search=(down&KEY_X) &&
                        (down&(KEY_LEFT|KEY_RIGHT|KEY_UP|KEY_DOWN));
                    if(!search_navigation && (down&KEY_X) &&
                       !(down&(KEY_A|KEY_Y)) && !source_search){
                        state.page=P3D_PAGE_FAVORITES;
                        favorite_index=0;
                        search_navigation=1;
                        redraw=1;
                    }
                    if(!search_navigation){
                        int next=state.selected_dex;
                        if(source_search){
                            if(down&KEY_UP){
                                state.search_letter=state.search_letter=='Z'?
                                    'A':state.search_letter+1;
                                redraw=1;
                            }
                            if(down&KEY_DOWN){
                                state.search_letter=state.search_letter=='A'?
                                    'Z':state.search_letter-1;
                                redraw=1;
                            }
                            if(dex_text_ready &&
                               ((down&KEY_LEFT)!=0)!=((down&KEY_RIGHT)!=0)){
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
                        if(next!=state.selected_dex){
                            state.selected_dex=next;
                            redraw=1;
                        }
                        if((down&KEY_Y) && !(down&KEY_A) && search_actionable()){
                            if(p3dFavoriteToggle(&state,state.selected_dex))
                                progress_dirty=1;
                            refresh_search_selection();
                            redraw=1;
                        }
                        if((down&KEY_A) && search_actionable()){
                            dex_index=state.selected_dex;
                            selected_form=0;
                            state.page=P3D_PAGE_DEX;
                            search_navigation=1;
                            reload_preview();
                            progress_dirty=1;
                            redraw=1;
                        }
                    }
                }
                /* Search navigation is fully consumed in this frame: no
                 * accidental Dex favorite toggle, animation change, or
                 * Move Dex/Settings controls from the same press. */
                if(search_navigation)down=0;
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
                if(down&(KEY_L|KEY_R)){
                    p3dBookmarkSettingsSelectList(&bookmark_settings,
                        bookmark_settings.active_list?0:1);
                    bookmark_cursor=0;
                    redraw=1;
                }
                if((down&KEY_START) && storage_ready){
                    /* Retry any pending failed write before adding another entry. */
                    if(bookmark_settings.dirty){
                        (void)p3dBookmarkSessionFlush(&bookmark_settings,P3D_SAVE_BASE);
                        redraw=1;
                    }else{
                        unsigned id=bookmark_settings.active_list?(unsigned)move_index:(unsigned)dex_index;
                        (void)p3dBookmarkSessionAdd(&bookmark_settings,P3D_SAVE_BASE,
                                                   bookmark_settings.active_list,id);
                        redraw=1;
                    }
                }
                if(down&(KEY_UP|KEY_DOWN)){
                    unsigned count=bookmark_settings.active_list?
                        bookmark_settings.moves.count:bookmark_settings.pokemon.count;
                    if(count){bookmark_cursor=(bookmark_cursor+count+
                        ((down&KEY_UP)?count-1:1))%count;redraw=1;}
                }
                if((down&KEY_Y) && !(down&(KEY_A|KEY_TOUCH))){
                    int editing=bookmark_settings.active_list?
                        bookmark_settings.moves.editing:bookmark_settings.pokemon.editing;
                    p3dBookmarkSettingsEdit(&bookmark_settings,!editing);
                    redraw=1;
                }
                if((down&KEY_SELECT) && storage_ready){
                    int opened=p3dBookmarkSessionSelect(&bookmark_settings,&state,
                        storage_ready?P3D_SAVE_BASE:NULL,bookmark_cursor);
                    if(opened==-1){
                        /* Deletion changed the in-memory list, but the FAT flush failed.
                           Keep the cursor valid and expose the pending save warning. */
                        unsigned count=bookmark_settings.active_list?
                            bookmark_settings.moves.count:bookmark_settings.pokemon.count;
                        if(bookmark_cursor>=count)bookmark_cursor=count?count-1:0;
                        redraw=1;
                    }
                    if(opened==2){
                        unsigned count=bookmark_settings.active_list?
                            bookmark_settings.moves.count:bookmark_settings.pokemon.count;
                        if(bookmark_cursor>=count)bookmark_cursor=count?count-1:0;
                        redraw=1;
                    }
                    if(opened==1){
                        if(state.page==P3D_PAGE_DEX)dex_index=state.selected_dex;
                        else if(state.page==P3D_PAGE_MOVES)move_index=state.move_index;
                        reload_preview();redraw=1;
                    }
                }
                if((down&KEY_X) && !(down&(KEY_A|KEY_TOUCH))){
                    prefer_source_chunks=!prefer_source_chunks;
                    reload_preview();
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
                /* Source-backed original text Search is reachable from the
                 * Type Chart without losing the selected national species.
                 * Clear stale region, scope and description filters so the
                 * destination never displays a different old query result.
                 * Consume the key to prevent same-frame search actions. */
                if((down&KEY_A) && !(down&(KEY_Y|KEY_X|KEY_TOUCH)) &&
                   p3dTypeChartOpenSearch(&state,dex_index)){
                    search_region=P3D_DEX_SCOPE_ALL;
                    search_scope=P3D_DEX_SCOPE_ALL;
                    search_field=P3D_DEX_SEARCH_NAME;
                    down=0;
                    redraw=1;
                }
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
                if((down&KEY_START) && !(down&(KEY_B|KEY_TOUCH))){
                    dex_detail_tab=dex_detail_tab?0:1;
                    art_page=-1; /* details are visible on text, not source art */
                    redraw=1;
                }
                if(dex_detail_tab && ((down&KEY_L)!=0)!=((down&KEY_R)!=0)){
                    int delta=(down&KEY_R)?1:-1;
                    dex_detail_tab=(dex_detail_tab+delta+3)%4+1;
                    art_page=-1;
                    redraw=1;
                }
                /* Cycle only existing verified optional animation files;
                 * reset playback at the new keyframe sequence. */
                if(preview_found && preview_animation_library.ready &&
                   ((down&KEY_UP)!=0)!=((down&KEY_DOWN)!=0)){
                    int direction=(down&KEY_DOWN)?1:-1;
                    if(p3dAnimationLibraryStep(&preview_animation_library,
                                               &preview_animation,
                                               "nitro:/animations",direction)){
                        p3dPlaybackReset(&animation_playback);
                        redraw=1;
                    }
                }
                /* Held shoulder buttons rotate continuously rather than taking
                 * only one step per press.  The model is drawn each frame, so
                 * rotation needs no expensive full-console redraw. */
                if(preview_found){
                    if(!dex_detail_tab && (held&KEY_L) && !(held&KEY_R))
                        model_yaw=(model_yaw-256)&32767;
                    else if(!dex_detail_tab && (held&KEY_R) && !(held&KEY_L))
                        model_yaw=(model_yaw+256)&32767;
                    else if(state.rotate && !(held&KEY_L) && !(held&KEY_R))
                        model_yaw=(model_yaw+64)&32767;
                }
                if(down&KEY_A){if(p3dFavoriteToggle(&state,dex_index))progress_dirty=1;redraw=1;}
                if((down&KEY_Y)){selected_form=p3dFormNext(&alternate_models,dex_index,selected_form);reload_preview();redraw=1;}
                if((down&KEY_LEFT) && !(down&KEY_RIGHT)){
                    if(p3dDexNavigateSync(&dex_index,&state.selected_dex,-1)){selected_form=0;reload_preview();progress_dirty=1;redraw=1;}
                }
                if((down&KEY_RIGHT) && !(down&KEY_LEFT)){
                    int next=p3dDexNavigate(dex_index,1);
                    if(next!=dex_index){dex_index=next;selected_form=0;reload_preview();progress_dirty=1;redraw=1;}
                }
            }
            /* In text navigation mode, the bottom corners also browse entries.
             * Original-art mode retains its artwork without guessed hitboxes. */
            if(!showing_original_art && (down&KEY_TOUCH) && state.page!=P3D_PAGE_SEARCH){
                touchPosition point;
                touchRead(&point);
                /* C230: controls are visible ONLY on the fallback text Dex UI.
                 * Block combined keypad/touch input and source geometry without
                 * independently verified skeletal animation. */
                if(state.page==P3D_PAGE_DEX && !dex_detail_tab &&
                   !(down&(KEY_A|KEY_B|KEY_X|KEY_Y|KEY_LEFT|KEY_RIGHT|
                           KEY_UP|KEY_DOWN|KEY_SELECT|KEY_START)) &&
                   p3dPlaybackTouch(&animation_playback,&preview_animation,
                                    !source_geometry_ready,!showing_original_art,
                                    point.px,point.py))
                    redraw=1;
                if(state.page==P3D_PAGE_DEX && dex_detail_tab &&
                   point.py>=160 && point.py<176){
                    int delta=point.px>=128?1:-1;
                    dex_detail_tab=(dex_detail_tab+delta+3)%4+1;
                    art_page=-1;redraw=1;
                }
                if(point.py>=150 && point.py<192 &&
                   (state.page!=P3D_PAGE_DEX || !dex_detail_tab ||
                    point.py>=176)){
                    int direction=point.px<64?-1:(point.px>=192?1:0);
                    if(state.page==P3D_PAGE_DEX && direction){
                        if(p3dDexNavigateSync(&dex_index,&state.selected_dex,direction)){
                            selected_form=0;reload_preview();
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
        if(redraw){
            render();
            /* Flush a changed screen/selection immediately instead of
             * waiting for the old one-second progress flush interval. */
            (void)save_resume_checkpoint();
        }
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
            p3dPlaybackAdvance(&animation_playback,&preview_animation,
                               !source_geometry_ready);
        }
    }
}
