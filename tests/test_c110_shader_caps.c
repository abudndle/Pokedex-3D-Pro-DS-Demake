#include <assert.h>
#include <stdio.h>
#include "source_shader_caps.h"
int main(int argc,char **argv){
    static P3DMaterialMap candidate;
    static P3DTextureManifest tex;
    static P3DSourceMaterialMap source;
    static P3DSourceShaderCaps shaders;
    assert(argc==8);
    assert(p3dMaterialMapLoad(&candidate,argv[1],3));
    assert(p3dTextureManifestLoad(&tex,argv[2]));
    assert(p3dSourceMaterialLoad(&source,argv[3],25,3));
    assert(p3dSourceShaderCapsLoad(&shaders,argv[4],25));
    assert(shaders.ready && shaders.count==13);
    assert(shaders.materials[10].flags&P3D_SHADER_CAP_COLORMAP);
    assert(p3dSourceShaderColorReferencesMatch(
        &shaders,&source,&candidate,&tex,25,3));
    assert(!p3dSourceShaderColorReferencesMatch(
        &shaders,&source,&candidate,&tex,25,2));
    assert(!p3dSourceShaderColorReferencesMatch(
        &shaders,&source,&candidate,&tex,26,3));
    /* A C5 source material with two distinct texture references is NOT
     * a proof of diffuse/color sampler routing. Do not guess. */
    source.ranges[0].source_texture1=7;
    shaders.materials[10].texture1=7;
    assert(p3dSourceMaterialTextureReferencesMatch(
        &source,&candidate,&tex,25,3));
    assert(!p3dSourceShaderColorReferencesMatch(
        &shaders,&source,&candidate,&tex,25,3));
    source.ranges[0].source_texture1=P3D_SOURCE_MATERIAL_NO_TEXTURE;
    shaders.materials[10].texture1=P3D_SOURCE_MATERIAL_NO_TEXTURE;
    /* A valid source material and original texture ID still do NOT
     * become color if the C5 shader lacks CF_COLORMAP. */
    shaders.materials[10].flags=P3D_SHADER_CAP_BUMPMAP;
    assert(!p3dSourceShaderColorReferencesMatch(
        &shaders,&source,&candidate,&tex,25,3));
    shaders.materials[10].flags=P3D_SHADER_CAP_COLORMAP;
    assert(p3dSourceShaderColorReferencesMatch(
        &shaders,&source,&candidate,&tex,25,3));
    shaders.materials[10].texture0=8;
    assert(!p3dSourceShaderColorReferencesMatch(
        &shaders,&source,&candidate,&tex,25,3));
    shaders.materials[10].texture0=2;
    candidate.ranges[0].texture_id=8;
    assert(!p3dSourceShaderColorReferencesMatch(
        &shaders,&source,&candidate,&tex,25,3));
    candidate.ranges[0].texture_id=2;
    /* Reject more than one source texture even with CF_COLORMAP. */
    source.ranges[1].source_texture0=P3D_SOURCE_MATERIAL_NO_TEXTURE;
    source.ranges[1].source_texture1=P3D_SOURCE_MATERIAL_NO_TEXTURE;
    shaders.materials[12].texture0=P3D_SOURCE_MATERIAL_NO_TEXTURE;
    shaders.materials[12].texture1=P3D_SOURCE_MATERIAL_NO_TEXTURE;
    assert(!p3dSourceShaderColorReferencesMatch(
        &shaders,&source,&candidate,&tex,25,3));
    assert(!p3dSourceShaderCapsLoad(&shaders,argv[4],26));
    assert(!shaders.ready);
    assert(!p3dSourceShaderCapsLoad(&shaders,argv[5],25));
    assert(!shaders.ready);
    assert(!p3dSourceShaderCapsLoad(&shaders,argv[6],25));
    assert(!shaders.ready);
    assert(!p3dSourceShaderCapsLoad(&shaders,argv[7],25));
    assert(!shaders.ready);
    assert(!p3dSourceShaderCapsLoad(&shaders,NULL,25));
    assert(!shaders.ready);
    puts("C110: verified C5 shader capabilities, ambiguous samplers fail closed: PASS");
    return 0;
}
