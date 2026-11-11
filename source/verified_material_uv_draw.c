#include "verified_material_uv_draw.h"
#include "source_material_texture_match.h"
#include "source_color_ranges.h"
typedef struct {
    const int *face_textures;
    unsigned triangle_count,next_triangle;
    P3DVerifiedMaterialTriangleSink sink;
    void *context;
} MaterialDrawContext;
static int material_triangle(void *opaque,uint16_t mesh_id,
    const P3DPrimitiveUvVertex *a,const P3DPrimitiveUvVertex *b,
    const P3DPrimitiveUvVertex *c){
    MaterialDrawContext *ctx=(MaterialDrawContext *)opaque;
    unsigned tri;
    int texture_id;
    if(!ctx||ctx->next_triangle>=ctx->triangle_count)return 0;
    tri=ctx->next_triangle++;
    texture_id=ctx->face_textures[tri];
    if(texture_id==P3D_SOURCE_MATERIAL_NO_TEXTURE)
        return ctx->sink(ctx->context,mesh_id,tri,(unsigned)texture_id,a,b,c);
    if(texture_id<0||
       !p3dSourceCandidateTextureRangeReady(ctx->face_textures,
          ctx->triangle_count,ctx->triangle_count,tri,1,
          (unsigned)texture_id,1,1))
        return 0;
    return ctx->sink(ctx->context,mesh_id,tri,(unsigned)texture_id,a,b,c);
}
int p3dVerifiedMaterialUvDraw(const P3DVerifiedGeometryPair *geometry,
    const P3DVerifiedVertexUv *uv,const P3DSourceMaterialMap *source,
    const P3DMaterialMap *materials,const P3DTextureManifest *textures,
    const P3DSourceShaderCaps *shader_caps,const P3DSourceMaterialWords *words,
    P3DVerifiedMaterialTriangleSink sink,void *context){
    int face_textures[600];
    MaterialDrawContext draw;
    unsigned triangles;
    if(!geometry||!uv||!source||!materials||!textures||!shader_caps||
       !sink||!geometry->ready||!uv->ready||!geometry->triangles||
       geometry->triangles>600)return 0;
    triangles=(unsigned)geometry->triangles;
    if(source->triangle_count!=triangles||
       !p3dSourceMaterialTextureReferencesMatch(source,materials,textures,
          geometry->model,triangles)||
       !p3dSourceCandidateTextureMap(source,materials,textures,
          geometry->model,triangles,face_textures,triangles))
        return 0;
    if(words){
        P3DSourceColorRanges ranges;
        if(!p3dSourceColorRangesBuild(&ranges,words,shader_caps,source,
            materials,textures,geometry->model,triangles)||!ranges.approved)return 0;
        for(unsigned i=0;i<ranges.count;i++){
            const P3DMaterialRange *range=&materials->ranges[i];
            if(!ranges.enabled[i])
                for(unsigned j=0;j<range->triangle_count;j++)
                    face_textures[range->first_triangle+j]=P3D_SOURCE_MATERIAL_NO_TEXTURE;
        }
    }else if(!p3dSourceShaderColorReferencesMatch(shader_caps,source,materials,
          textures,geometry->model,triangles))return 0;
    draw.face_textures=face_textures;
    draw.triangle_count=triangles;
    draw.next_triangle=0;
    draw.sink=sink;
    draw.context=context;
    if(!p3dVerifiedPrimitiveUvBridge(geometry,uv,material_triangle,&draw))
        return 0;
    return draw.next_triangle==triangles;
}
