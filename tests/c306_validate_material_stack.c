/* C306 synthetic fixture integrity checked using real native C loaders.
 * No 3DS proprietary materials, meshes, or textures are included. */
#include <stdio.h>
#include <stdlib.h>
#include "verified_geometry_pair.h"
#include "verified_vertex_uv.h"
#include "verified_material_uv_draw.h"
#include "source_material_words.h"
#include "source_color_ranges.h"
#include "ds_material_texture_cache.h"
#include "texture_asset.h"

static P3DVerifiedGeometryPair geometry;
static P3DVerifiedVertexUv uv;
static P3DMaterialMap materials;
static P3DTextureManifest textures;
static P3DSourceMaterialMap source;
static P3DSourceShaderCaps caps;
static P3DSourceMaterialWords words;
static P3DSourceColorRanges approved;
static unsigned drawn;

static int sink(void *ctx,uint16_t mesh,unsigned tri,unsigned texture,
    const P3DPrimitiveUvVertex *a,const P3DPrimitiveUvVertex *b,
    const P3DPrimitiveUvVertex *c){
    (void)ctx;(void)mesh;(void)tri;
    if(!a||!b||!c||!a->xyz||!b->xyz||!c->xyz||!texture)return 0;
    ++drawn;
    return 1;
}
static void path(char *out,size_t n,const char *root,const char *category,
                 unsigned model,const char *ext){
    int k=snprintf(out,n,"%s/%s/p%03u.%s",root,category,model,ext);
    if(k<0||(size_t)k>=n)exit(100);
}
#define REQUIRE(expr) do{if(!(expr)){fprintf(stderr,   "C306 native preflight failure: model %u line %d: %s\\n",model,__LINE__,#expr);   return 1;}}while(0)
static int probe(const char *root,unsigned model){
    char f[256];
    char vx[256],ix[256];
    path(vx,sizeof(vx),root,"geometry",model,"p3vx");
    path(ix,sizeof(ix),root,"geometry",model,"p3ix");
    REQUIRE(p3dVerifiedGeometryPairLoad(&geometry,vx,ix,(uint16_t)model));
    path(f,sizeof(f),root,"geometry",model,"p3vu");
    REQUIRE(p3dVerifiedVertexUvLoad(&uv,f,&geometry));
    path(f,sizeof(f),root,"materials",model,"p3mt");
    REQUIRE(p3dMaterialMapLoad(&materials,f,(unsigned)geometry.triangles));
    path(f,sizeof(f),root,"materials",model,"p3tx");
    REQUIRE(p3dTextureManifestLoad(&textures,f));
    path(f,sizeof(f),root,"materials",model,"p3mr");
    REQUIRE(p3dSourceMaterialLoad(&source,f,model,(unsigned)geometry.triangles));
    path(f,sizeof(f),root,"materials",model,"p3sc");
    REQUIRE(p3dSourceShaderCapsLoad(&caps,f,model));
    path(f,sizeof(f),root,"materials",model,"p3sw");
    REQUIRE(p3dSourceMaterialWordsLoad(&words,f,model));
    REQUIRE(p3dSourceMaterialWordsMatch(&words,&caps,&source,model,
                                      (unsigned)geometry.triangles));
    REQUIRE(p3dSourceColorRangesBuild(&approved,&words,&caps,&source,
                   &materials,&textures,model,(unsigned)geometry.triangles));
    REQUIRE(approved.ready && approved.approved==materials.count);
    REQUIRE(p3dDsMaterialTextureBudgetValid(&materials,&textures,
                                            (unsigned)geometry.triangles));
    drawn=0;
    REQUIRE(p3dVerifiedMaterialUvDraw(&geometry,&uv,&source,&materials,
                                    &textures,&caps,sink,NULL));
    REQUIRE(drawn==geometry.triangles);
    fprintf(stdout,"C306: native verified model %u material/UV triangles %u: PASS\\n",
            model,drawn);
    return 0;
}
int main(int argc,char **argv){
    if(argc!=2)return 2;
    if(probe(argv[1],2)||probe(argv[1],3))return 1;
    return 0;
}
