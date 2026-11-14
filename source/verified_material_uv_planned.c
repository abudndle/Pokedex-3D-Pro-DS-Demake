/* C448: source-verified mixed-material native triangle stream.
 * Reuses the exact paired source mesh/UV walk; never guesses a 3DS sampler. */
#include "verified_material_uv_draw.h"
#include "source_material_texture_match.h"
#include "source_color_ranges.h"
typedef struct {
    const int *candidates;
    const uint16_t *approved;
    unsigned total,next;
    P3DVerifiedMaterialTriangleSink sink;
    void *context;
} P3DPlannedMaterialDraw;
static int planned_triangle(void *opaque,uint16_t mesh,
    const P3DPrimitiveUvVertex *a,const P3DPrimitiveUvVertex *b,
    const P3DPrimitiveUvVertex *c){
    P3DPlannedMaterialDraw *draw=(P3DPlannedMaterialDraw *)opaque;
    if(!draw||draw->next>=draw->total)return 0;
    unsigned face=draw->next++;
    unsigned id=draw->approved[face];
    if(id!=P3D_SOURCE_MATERIAL_NO_TEXTURE &&
       (draw->candidates[face]!=(int)id ||
        !p3dSourceCandidateTextureRangeReady(draw->candidates,
            draw->total,draw->total,face,1,id,1,1)))
        return 0;
    return draw->sink(draw->context,mesh,face,id,a,b,c);
}
int p3dVerifiedMaterialUvDrawWithWords(
    const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *caps,const P3DSourceMaterialWords *words,
    P3DVerifiedMaterialTriangleSink sink,void *context){
    int candidate[600];
    uint16_t approved[600];
    P3DSourceColorRanges ranges;
    P3DPlannedMaterialDraw draw;
    unsigned triangles;
    if(!geometry||!uv||!source||!materials||!textures||!caps||
       !words||!sink||!geometry->ready||!uv->ready||
       !geometry->triangles||geometry->triangles>600)return 0;
    triangles=(unsigned)geometry->triangles;
    if(source->triangle_count!=triangles ||
       !p3dSourceCandidateTextureMap(source,materials,textures,
           geometry->model,triangles,candidate,triangles) ||
       !p3dSourceColorRangesBuild(&ranges,words,caps,source,materials,
           textures,geometry->model,triangles) ||
       !p3dSourceColorRangesFacePlan(&ranges,materials,triangles,
           approved,triangles))return 0;
    draw.candidates=candidate;
    draw.approved=approved;
    draw.total=triangles;
    draw.next=0;
    draw.sink=sink;
    draw.context=context;
    return p3dVerifiedPrimitiveUvBridge(geometry,uv,planned_triangle,&draw)
        && draw.next==triangles;
}
