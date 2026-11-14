/* C306 native loader preflight on only synthetic P3VX/P3VU/material sidecars.
 * Distinguishes malformed source witnesses from an actual DS GL render issue. */
#include "verified_geometry_pair.h"
#include "verified_vertex_uv.h"
#include "verified_material_uv_draw.h"
#include "source_material_words.h"
#include "source_color_ranges.h"
#include "ds_material_uv_draw.h"
#include "model_material_texture.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
static P3DVerifiedGeometryPair g;
static P3DVerifiedVertexUv uv;
static P3DMaterialMap m;
static P3DTextureManifest t;
static P3DSourceMaterialMap source;
static P3DSourceShaderCaps caps;
static P3DSourceMaterialWords words;
static P3DSourceColorRanges ranges;
static P3DDsMaterialTextureCache cache;
static P3DTexturePixels pixels;
static char dir[240],texture_path[280];
static unsigned begins,verts,uvs,ends,colors,neutral_binds,neutral_colors;
static int expect_neutral;
int p3dTestMaterialBegin(int id){
    assert(id>=0);
    if(id==0)neutral_binds++;
    begins++;return 1;
}
void p3dTestMaterialTexCoord(int16_t u,int16_t v){
    assert(u>=0&&u<=4096&&v>=0&&v<=4096);uvs++;
}
void p3dTestMaterialVertex(const int16_t *xyz){assert(xyz);verts++;}
void p3dTestMaterialEnd(void){ends++;}
void p3dTestMaterialColor(unsigned char r,unsigned char g,unsigned char b){
    /* This fixture approves one simple source color texture per model. */
    if(expect_neutral){assert(r==192 && g==224 && b==232);neutral_colors++;}
    else assert(r==255 && g==255 && b==255);
    colors++;
}
static const char *resolve(void *opaque,unsigned id){
    (void)opaque;
    int n=snprintf(texture_path,sizeof(texture_path),"%s/t%03u.p3px",dir,id);
    return n>0&&(unsigned)n<sizeof(texture_path)?texture_path:NULL;
}
static void path(char *out,size_t cap,const char *root,
                 const char *folder,unsigned model,const char *ext){
    int n=snprintf(out,cap,"%s/%s/p%03u.%s",root,folder,model,ext);
    assert(n>0&&(unsigned)n<cap);
}
static void expect(int good,const char *what,unsigned model){
    if(!good){fprintf(stderr,"C306 gate failed for model %u: %s\n",model,what);exit(1);}
}
static int sink(void *opaque,uint16_t mesh,unsigned triangle,
                unsigned tex,const P3DPrimitiveUvVertex *a,
                const P3DPrimitiveUvVertex *b,const P3DPrimitiveUvVertex *c){
    unsigned *count=(unsigned *)opaque;
    assert(mesh==0&&triangle==0&&a&&b&&c);
    if(expect_neutral)assert(tex==P3D_SOURCE_MATERIAL_NO_TEXTURE);
    else assert(tex>0&&tex!=P3D_SOURCE_MATERIAL_NO_TEXTURE);
    (*count)++;return 1;
}
int main(int argc,char **argv){
    char p[280],q[280];
    if(argc!=2)return 2;
    for(unsigned model=2;model<=3;model++){
        path(p,sizeof(p),argv[1],"geometry",model,"p3vx");
        path(q,sizeof(q),argv[1],"geometry",model,"p3ix");
        expect(p3dVerifiedGeometryPairLoad(&g,p,q,model),"geometry pair",model);
        path(p,sizeof(p),argv[1],"geometry",model,"p3vu");
        expect(p3dVerifiedVertexUvLoad(&uv,p,&g),"paired UV",model);
        path(p,sizeof(p),argv[1],"materials",model,"p3mt");
        expect(p3dMaterialMapLoad(&m,p,1),"P3MT",model);
        path(p,sizeof(p),argv[1],"materials",model,"p3tx");
        expect(p3dTextureManifestLoad(&t,p),"P3TX",model);
        path(p,sizeof(p),argv[1],"materials",model,"p3mr");
        expect(p3dSourceMaterialLoad(&source,p,model,1),"P3MR",model);
        path(p,sizeof(p),argv[1],"materials",model,"p3sc");
        expect(p3dSourceShaderCapsLoad(&caps,p,model),"P3SC",model);
        path(p,sizeof(p),argv[1],"materials",model,"p3sw");
        expect(p3dSourceMaterialWordsLoad(&words,p,model),"P3SW",model);
        expect(p3dSourceMaterialWordsMatch(&words,&caps,&source,model,1),
               "source words match",model);
        expect(p3dSourceColorRangesBuild(&ranges,&words,&caps,&source,
                &m,&t,model,1),"simple-color range gate",model);
        expect(ranges.approved==m.count&&ranges.count==m.count,
               "color range coverage",model);
        expect(p3dDsMaterialTextureBudgetValid(&m,&t,1),"VRAM budget",model);
        unsigned count=0;
        expect(p3dVerifiedMaterialUvDrawWithWords(&g,&uv,&source,&m,&t,
               &caps,&words,sink,&count),
               "material UV preflight",model);
        expect(count==1,"triangle count",model);
        int n=snprintf(dir,sizeof(dir),"%s/textures/p%03u",argv[1],model);
        expect(n>0&&(unsigned)n<sizeof(dir),"texture directory",model);
        expect(p3dDsMaterialTextureCacheInit(&cache,&t,resolve,NULL),
               "cache initialize",model);
        uint32_t drawn=0;
        begins=verts=uvs=ends=colors=neutral_binds=neutral_colors=0;
        expect(p3dDsMaterialUvDrawWithWords(&g,&uv,&source,&m,&t,&caps,
               &words,&cache,&pixels,&drawn),"source-word native draw",model);
        expect(drawn==1&&begins==1&&verts==3&&uvs==3&&ends==1&&colors==1,
               "draw trace",model);
        printf("C306 model %u: genuine C data gate and host material draw PASS\n",model);
        p3dDsMaterialTextureCacheDestroy(&cache);
        /* Deliberately classify a real synthetic model as unsupported
         * bump-map shader. Its source triangles must still draw, but no
         * backed texture payload may be uploaded or sampled. */
        if(model==3){
            unsigned idx=source.ranges[0].material_index;
            caps.materials[idx].flags|=P3D_SHADER_CAP_BUMPMAP;
            expect(p3dSourceColorRangesBuild(&ranges,&words,&caps,&source,
                   &m,&t,model,1) && ranges.approved==0,
                   "source shader neutral fallback",model);
            expect_neutral=1;
            count=0;
            expect(p3dVerifiedMaterialUvDrawWithWords(&g,&uv,&source,&m,&t,
                   &caps,&words,sink,&count) && count==1,
                   "neutral source triangle stream",model);
            expect(p3dDsMaterialTextureCacheInit(&cache,&t,resolve,NULL),
                   "neutral cache initialize",model);
            begins=verts=uvs=ends=colors=neutral_binds=neutral_colors=0;
            expect(p3dDsMaterialUvPrepareWithWords(&g,&uv,&source,&m,&t,
                   &caps,&words,&cache,&pixels) && cache.count==0,
                   "no unapproved texture upload",model);
            drawn=0;
            expect(p3dDsMaterialUvDrawWithWords(&g,&uv,&source,&m,&t,
                   &caps,&words,&cache,&pixels,&drawn) &&
                   drawn==1 && cache.count==0 && begins==1 && ends==1 &&
                   verts==3 && uvs==0 && neutral_binds==1 &&
                   neutral_colors==1 && colors==1,
                   "neutral geometry without UV and texture",model);
            p3dDsMaterialTextureCacheDestroy(&cache);
            expect_neutral=0;
        }
    }
    return 0;
}
