#include "verified_geometry_pair.h"
#include "verified_primitive_stream.h"
#include <stdio.h>
#include <string.h>
static int read_bounded(const char *path,uint8_t *data,size_t cap,size_t *size){
    FILE *file;
    size_t n;
    int trailing;
    if(!path||!data||!size)return 0;
    *size=0;
    file=fopen(path,"rb");
    if(!file)return 0;
    n=fread(data,1,cap,file);
    trailing=fgetc(file);
    if(ferror(file)||trailing!=EOF){fclose(file);return 0;}
    fclose(file);
    *size=n;
    return n>0;
}
static int accept(void *context,uint16_t mesh,const int16_t *a,
                  const int16_t *b,const int16_t *c){
    (void)context;(void)mesh;(void)a;(void)b;(void)c;
    return 1;
}
void p3dVerifiedGeometryPairClear(P3DVerifiedGeometryPair *pair){
    if(pair)memset(pair,0,sizeof(*pair));
}
int p3dVerifiedGeometryPairLoad(P3DVerifiedGeometryPair *pair,
    const char *vertex_path,const char *index_path,uint16_t model){
    size_t vx_size=0,ix_size=0,mesh_count=0;
    P3DVerifiedIndexInfo info;
    uint32_t emitted=0;
    if(!pair)return 0;
    p3dVerifiedGeometryPairClear(pair);
    if(!read_bounded(vertex_path,pair->vx,sizeof(pair->vx),&vx_size)||
       !read_bounded(index_path,pair->ix,sizeof(pair->ix),&ix_size)||
       !p3dVerifiedVerticesDecode(pair->vx,vx_size,model,pair->meshes,
           P3D_VERTEX_MAX_MESHES,pair->xyz,P3D_VERTEX_MAX_VERTICES*3u,
           &mesh_count)||
       !p3dVerifiedIndexInspect(pair->ix,ix_size,model,&info)||
       info.triangles>P3D_GEOMETRY_MAX_TRIANGLES||
       !p3dVerifiedPrimitiveBridge(pair->ix,ix_size,model,pair->meshes,
                                   mesh_count,accept,NULL,&emitted)||
       emitted!=info.triangles){
        p3dVerifiedGeometryPairClear(pair);
        return 0;
    }
    pair->mesh_count=mesh_count;
    pair->ix_size=ix_size;
    pair->triangles=emitted;
    pair->model=model;
    pair->ready=1;
    return 1;
}
