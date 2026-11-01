#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "model_material_texture.h"
#include "model_uv.h"
#include "preview_texture_set.h"
#include "ds_texture_upload.h"

static int next_id,attempts,deleted,fail_attempt;
static int rgba_seen,rgb_seen;
static int deleted_ids[24];

void glGenTextures(int count,int *ids){
    assert(count==1);
    *ids=++next_id;
}
void glBindTexture(int target,int texture_id){
    (void)target;(void)texture_id;
}
int glTexImage2D(int target,int level,int format,int sx,int sy,
                 int border,int params,const void *pixels){
    (void)target;(void)level;(void)border;(void)params;
    assert(sx==0 || sx==1);
    assert(sy==0);
    assert(((const unsigned short*)pixels)[0]!=0);
    if(format==GL_RGBA)rgba_seen++;
    else if(format==GL_RGB)rgb_seen++;
    else assert(0);
    attempts++;
    return attempts!=fail_attempt;
}
void glDeleteTextures(int count,const int *ids){
    assert(count==1 && ids && *ids>0);
    assert(deleted<(int)(sizeof(deleted_ids)/sizeof(deleted_ids[0])));
    deleted_ids[deleted++]=*ids;
}
int main(int argc,char **argv){
    static P3DMaterialMap mat;
    static P3DTextureManifest manifest;
    static P3DUvMap uv;
    static P3DTexturePixels pixels;
    static P3DPreviewTextureSet set;
    int before,removed;
    assert(argc==6);
    assert(p3dMaterialMapLoad(&mat,argv[1],4));
    assert(p3dTextureManifestLoad(&manifest,argv[2]));
    assert(p3dUvLoad(&uv,argv[3],4));
    assert(uv.ready && uv.triangles==4);
    assert(!p3dUvLoad(&uv,argv[3],3));
    assert(!uv.ready);
    assert(p3dUvLoad(&uv,argv[3],4));
    assert(p3dModelMaterialTexturesMatchMesh(&mat,&manifest,4));
    assert(!p3dModelMaterialTexturesMatchMesh(&mat,&manifest,3));
    assert(!p3dModelMaterialTexturesMatchMesh(&mat,&manifest,0));
    assert(p3dModelMaterialTexturesValid(&mat,&manifest));
    assert(p3dModelTextureForTriangle(&mat,&manifest,0)==2);
    assert(p3dModelTextureForTriangle(&mat,&manifest,1)==2);
    assert(p3dModelTextureForTriangle(&mat,&manifest,2)==2);
    assert(p3dModelTextureForTriangle(&mat,&manifest,3)==7);
    assert(p3dModelTextureForTriangle(&mat,&manifest,4)==-1);
    assert(p3dPreviewTextureSetLoad(&set,&pixels,&mat,&manifest,argv[4]));
    assert(set.ready && set.count==2 && attempts==2);
    assert(rgba_seen==1 && rgb_seen==1);
    assert(p3dPreviewTextureSetFind(&set,2));
    assert(p3dPreviewTextureSetFind(&set,7));
    assert(p3dPreviewTextureSetFind(&set,9)==NULL);
    assert(p3dPreviewTextureSetFind(&set,2)->gl_id!=
           p3dPreviewTextureSetFind(&set,7)->gl_id);
    assert(!pixels.ready);
    p3dPreviewTextureSetRelease(&set);
    assert(!set.ready && !set.count && deleted==2);
    assert(!p3dPreviewTextureSetFind(&set,2));
    /* Corrupt second original pixel file: first GPU texture is released,
     * never leaving a partially textured model or leaking VRAM. */
    before=attempts;removed=deleted;
    assert(!p3dPreviewTextureSetLoad(&set,&pixels,&mat,&manifest,argv[5]));
    assert(attempts==before+1 && deleted==removed+1);
    assert(!set.ready && !set.count && !pixels.ready);
    /* A GPU failure on the second distinct source texture similarly
     * deletes both the failed upload and the previous allocation. */
    fail_attempt=attempts+2;before=attempts;removed=deleted;
    assert(!p3dPreviewTextureSetLoad(&set,&pixels,&mat,&manifest,argv[4]));
    assert(attempts==before+2 && deleted==removed+2);
    assert(!set.ready && !set.count);
    fail_attempt=0;
    /* A corrupt/gapped material range must never bind the wrong pixel
     * payload even when both source P3PX texture IDs exist. */
    mat.ranges[1].first_triangle=2;
    before=attempts;
    assert(!p3dModelMaterialTexturesValid(&mat,&manifest));
    assert(!p3dModelMaterialTexturesMatchMesh(&mat,&manifest,4));
    assert(!p3dPreviewTextureSetLoad(&set,&pixels,&mat,&manifest,argv[4]));
    assert(attempts==before && !set.ready);
    mat.ranges[1].first_triangle=1;
    mat.ranges[2].first_triangle=2; /* overlap */
    assert(!p3dModelMaterialTexturesValid(&mat,&manifest));
    mat.ranges[2].first_triangle=3;
    mat.ranges[1].triangle_count=0;
    assert(!p3dModelMaterialTexturesValid(&mat,&manifest));
    mat.ranges[1].triangle_count=2;
    mat.ranges[1].texture_id=999;
    assert(!p3dModelMaterialTexturesValid(&mat,&manifest));
    mat.ranges[1].texture_id=2;
    mat.count=P3D_MATERIAL_MAX+1;
    assert(!p3dModelMaterialTexturesValid(&mat,&manifest));
    mat.count=3;
    manifest.entries[1].id=2; /* not strictly sorted */
    assert(!p3dModelMaterialTexturesValid(&mat,&manifest));
    manifest.entries[1].id=7;
    manifest.entries[0].format=9;
    assert(!p3dModelMaterialTexturesValid(&mat,&manifest));
    manifest.entries[0].format=1;
    manifest.count=P3D_TEXTURE_MAX+1;
    assert(!p3dModelMaterialTexturesValid(&mat,&manifest));
    manifest.count=2;
    /* Both textures exist, but their total >128KiB. Budget must reject
     * the whole model BEFORE creating a single GL texture. */
    manifest.entries[0].width=256;
    manifest.entries[0].height=256;
    before=attempts;
    assert(p3dModelMaterialTexturesMatchMesh(&mat,&manifest,4));
    assert(!p3dPreviewTextureSetLoad(&set,&pixels,&mat,&manifest,argv[4]));
    assert(attempts==before && !set.ready && !set.count);
    puts("C108: exact original mesh/material/UV texture bindings: PASS");
    return 0;
}
