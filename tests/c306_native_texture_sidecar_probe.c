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
static unsigned begins,verts,uvs,ends;
int p3dTestMaterialBegin(int id){ assert(id>0);begins++;return 1; }
void p3dTestMaterialTexCoord(int16_t u,int16_t v){
    assert(u>=0&&u<=4096&&v>=0&&v<=4096);uvs++;
}
void p3dTestMaterialVertex(const int16_t *xyz){assert(xyz);verts++;}
void p3dTestMaterialEnd(void){ends++;}
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
    assert(mesh==0&&triangle==0&&tex>0&&a&&b&&c);
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
        expect(p3dVerifiedMaterialUvDraw(&g,&uv,&source,&m,&t,&caps,sink,&count),
               "material UV preflight",model);
        expect(count==1,"triangle count",model);
        int n=snprintf(dir,sizeof(dir),"%s/textures/p%03u",argv[1],model);
        expect(n>0&&(unsigned)n<sizeof(dir),"texture directory",model);
        expect(p3dDsMaterialTextureCacheInit(&cache,&t,resolve,NULL),
               "cache initialize",model);
        uint32_t drawn=0;
        begins=verts=uvs=ends=0;
        /* Texture IDs are model-local. A cache from another manifest must
         * not supply its 8-wide payload for a validated 16-wide texture. */
        P3DTextureManifest other=t;
        other.entries[0].width=16;
        expect(!p3dDsMaterialUvDraw(&g,&uv,&source,&m,&other,&caps,
                                    &cache,&pixels,&drawn),"reject foreign texture cache",model);
        expect(!drawn&&!begins&&!cache.count&&cache.ready,
               "foreign texture cache has no side effects",model);
        expect(p3dDsMaterialUvDraw(&g,&uv,&source,&m,&t,&caps,
                                   &cache,&pixels,&drawn),"native draw",model);
        expect(drawn==1&&begins==1&&verts==3&&uvs==3&&ends==1,
               "draw trace",model);
        printf("C306 model %u: genuine C data gate and host material draw PASS\n",model);
        p3dDsMaterialTextureCacheDestroy(&cache);
    }
    return 0;
}
