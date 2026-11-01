#include <assert.h>
#include <stdio.h>
#include "model_materials.h"
#include "model_textures.h"
#include "source_material_map.h"
#include "source_material_texture_match.h"

int main(int argc,char **argv){
    static P3DMaterialMap candidate;
    static P3DTextureManifest textures;
    static P3DSourceMaterialMap source;
    assert(argc==6);
    assert(p3dMaterialMapLoad(&candidate,argv[1],4));
    assert(p3dTextureManifestLoad(&textures,argv[2]));
    assert(p3dSourceMaterialLoad(&source,argv[3],25,4));
    assert(source.ready && source.count==2);
    assert(p3dSourceMaterialTextureReferencesMatch(
        &source,&candidate,&textures,25,4));
    /* C125: triangle-level candidates preserve the exact approved C5
       draw range, never selecting an unrelated manifest texture. */
    assert(p3dSourceCandidateTextureForTriangle(
        &source,&candidate,&textures,25,4,0)==2);
    assert(p3dSourceCandidateTextureForTriangle(
        &source,&candidate,&textures,25,4,1)==2);
    assert(p3dSourceCandidateTextureForTriangle(
        &source,&candidate,&textures,25,4,2)==2);
    assert(p3dSourceCandidateTextureForTriangle(
        &source,&candidate,&textures,25,4,3)==7);
    assert(p3dSourceCandidateTextureForTriangle(
        &source,&candidate,&textures,25,4,4)==-1);
    assert(p3dSourceCandidateTextureForTriangle(
        &source,&candidate,&textures,26,4,0)==-1);
    /* C126: all-face map must agree with the original C5 material
       spans and clear stale output before any rejected mapping. */
    int face_textures[5]={99,99,99,99,99};
    assert(p3dSourceCandidateTextureMap(
        &source,&candidate,&textures,25,4,face_textures,5));
    assert(face_textures[0]==2&&face_textures[1]==2&&
           face_textures[2]==2&&face_textures[3]==7&&face_textures[4]==-1);
    /* C139: the ACTUAL native draw-range binding predicate must reject
     * every unverified source face, texture ID and sampler/UV combination.
     * A valid source reference alone is not proof of the diffuse sampler. */
#define READY(first,n,tex,role,uv) p3dSourceCandidateTextureRangeReady(\
        face_textures,5,4,(first),(n),(tex),(role),(uv))
    assert(READY(0,1,2,1,1));
    assert(READY(0,3,2,1,1));
    assert(READY(1,2,2,1,1));
    assert(READY(3,1,7,1,1));
    assert(!READY(2,2,2,1,1));  /* cross original source texture boundary */
    assert(!READY(3,1,2,1,1));  /* wrong source texture on final face */
    assert(!READY(0,3,7,1,1));
    assert(!READY(0,3,2,0,1));  /* shader colormap role unverified */
    assert(!READY(0,3,2,1,0));  /* missing or unsafe paired source UV */
    assert(!READY(0,0,2,1,1));
    assert(!READY(4,1,7,1,1));
    assert(!READY(3,2,7,1,1));
    assert(!READY(0,5,2,1,1));
    assert(!READY((unsigned)-1,1,2,1,1));
    assert(!READY(0,(unsigned)-1,2,1,1));
    assert(!READY(0,3,P3D_SOURCE_MATERIAL_NO_TEXTURE,1,1));
    assert(!READY(0,3,(unsigned)-1,1,1));
    assert(!p3dSourceCandidateTextureRangeReady(NULL,5,4,0,3,2,1,1));
    assert(!p3dSourceCandidateTextureRangeReady(face_textures,3,4,0,3,2,1,1));
    assert(!p3dSourceCandidateTextureRangeReady(face_textures,601,4,0,3,2,1,1));
    assert(!p3dSourceCandidateTextureRangeReady(face_textures,5,601,0,3,2,1,1));
    assert(!p3dSourceCandidateTextureRangeReady(face_textures,5,0,0,3,2,1,1));
    face_textures[2]=-1;
    assert(!READY(0,3,2,1,1)); /* partially cleared source map */
    face_textures[2]=2;
#undef READY

    assert(!p3dSourceCandidateTextureMap(
        &source,&candidate,&textures,26,4,face_textures,5));
    for(unsigned i=0;i<5;i++)assert(face_textures[i]==-1);
    assert(!p3dSourceCandidateTextureMap(
        &source,&candidate,&textures,25,4,face_textures,3));
    for(unsigned i=0;i<3;i++)assert(face_textures[i]==-1);
    assert(!p3dSourceCandidateTextureMap(
        &source,&candidate,&textures,25,4,NULL,5));
    /* Reference and topology are both required, even with valid P3MT. */
    assert(!p3dSourceMaterialTextureReferencesMatch(
        &source,&candidate,&textures,26,4));
    assert(!p3dSourceMaterialTextureReferencesMatch(
        &source,&candidate,&textures,25,3));
    assert(!p3dSourceMaterialTextureReferencesMatch(
        &source,&candidate,&textures,25,0));
    assert(!p3dSourceMaterialTextureReferencesMatch(
        NULL,&candidate,&textures,25,4));
    assert(!p3dSourceMaterialTextureReferencesMatch(
        &source,NULL,&textures,25,4));
    assert(!p3dSourceMaterialTextureReferencesMatch(
        &source,&candidate,NULL,25,4));
    /* A perfectly valid candidate texture is rejected when the original
       3DS material does not actually reference its source texture ID. */
    candidate.ranges[0].texture_id=8;
    assert(p3dModelMaterialTexturesMatchMesh(&candidate,&textures,4));
    assert(!p3dSourceMaterialTextureReferencesMatch(
        &source,&candidate,&textures,25,4));
    assert(p3dSourceCandidateTextureForTriangle(
        &source,&candidate,&textures,25,4,0)==-1);
    candidate.ranges[0].texture_id=2;
    /* A name hint cannot substitute an original C5 material number. */
    candidate.ranges[1].material_id=99;
    assert(!p3dSourceMaterialTextureReferencesMatch(
        &source,&candidate,&textures,25,4));
    candidate.ranges[1].material_id=10;
    /* Candidate spans across source material boundary (face 3). */
    candidate.ranges[1].triangle_count=3;
    candidate.count=2;
    assert(!p3dSourceMaterialTextureReferencesMatch(
        &source,&candidate,&textures,25,4));
    candidate.count=3;
    candidate.ranges[1].triangle_count=2;
    /* Valid referenced source texture, but 3DS C5 shader role STILL
       unknown. Both source texture slots are treated as candidates. */
    candidate.ranges[0].texture_id=7;
    assert(p3dSourceMaterialTextureReferencesMatch(
        &source,&candidate,&textures,25,4));
    candidate.ranges[0].texture_id=2;
    /* Simulate a stale, corrupt, or manually forged P3MR map. */
    source.ranges[0].source_pass=0x0c01;
    assert(!p3dSourceMaterialTextureReferencesMatch(
        &source,&candidate,&textures,25,4));
    source.ranges[0].source_pass=0x0c02;
    source.ranges[0].source_texture0=P3D_SOURCE_MATERIAL_NO_TEXTURE;
    source.ranges[0].source_texture1=P3D_SOURCE_MATERIAL_NO_TEXTURE;
    assert(!p3dSourceMaterialTextureReferencesMatch(
        &source,&candidate,&textures,25,4));
    assert(!p3dSourceMaterialLoad(&source,argv[4],25,4));
    assert(!source.ready); /* Bad original CRC must not leave stale binding. */
    assert(!p3dSourceMaterialLoad(&source,argv[5],25,4));
    assert(!source.ready);
    puts("C109/C125/C126 source-backed triangle and atomic mesh texture map: PASS");
    return 0;
}
