#include <assert.h>
#include <stdio.h>
#include "source_shader_caps.h"
#include "source_material_words.h"
int main(int argc,char **argv){
    static P3DMaterialMap candidate;
    static P3DTextureManifest tex;
    static P3DSourceMaterialMap source;
    static P3DSourceShaderCaps shaders;
    static P3DSourceMaterialWords words;
    assert(argc==15);
    assert(p3dMaterialMapLoad(&candidate,argv[1],3));
    assert(p3dTextureManifestLoad(&tex,argv[2]));
    assert(p3dSourceMaterialLoad(&source,argv[3],25,3));
    assert(p3dSourceShaderCapsLoad(&shaders,argv[4],25));
    assert(shaders.ready && shaders.count==13);
    assert(shaders.materials[10].flags&P3D_SHADER_CAP_COLORMAP);
    /* C113 source C5 material registers must independently agree with
     * source C90 P3MR and C112 P3SC before native texture routing. */
    assert(p3dSourceMaterialWordsLoad(&words,argv[10],25));
    assert(words.ready && words.count==13);
    assert(words.words[10][1]==0xffff0002u);
    assert(p3dSourceMaterialWordsMatch(&words,&shaders,&source,25,3));
    assert(!p3dSourceMaterialWordsMatch(&words,&shaders,&source,26,3));
    assert(!p3dSourceMaterialWordsMatch(&words,&shaders,&source,25,2));
    words.words[10][1]=0xffff0008u;
    assert(!p3dSourceMaterialWordsMatch(&words,&shaders,&source,25,3));
    words.words[10][1]=0xffff0002u;
    assert(p3dSourceMaterialWordsMatch(&words,&shaders,&source,25,3));
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
    shaders.materials[10].flags=P3D_SHADER_CAP_COLORMAP|P3D_SHADER_CAP_BUMPMAP;
    /* CF_COLORMAP plus CF_BUMPMAP is NOT a proven color-only sampler. */
    assert(!p3dSourceShaderColorReferencesMatch(
        &shaders,&source,&candidate,&tex,25,3));
    shaders.materials[10].flags=P3D_SHADER_CAP_COLORMAP|P3D_SHADER_CAP_OTHER;
    /* A source CF_COLORMAP mixed with any OTHER C5 capability is
     * not evidence for a simple original diffuse-only sampler. */
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
    assert(!p3dSourceShaderCapsLoad(&shaders,argv[8],25));
    assert(!shaders.ready); /* Legacy v1 dropped source shader flags. */
    assert(!p3dSourceShaderCapsLoad(&shaders,argv[9],25));
    assert(!shaders.ready); /* Unsupported high bits, CRC still valid. */
    assert(!p3dSourceShaderCapsLoad(&shaders,NULL,25));
    assert(!shaders.ready);
    /* Check incomplete/corrupt source operation words never retain READY.
     * A matching CRC with the wrong source slot must also fail the join. */
    assert(!p3dSourceMaterialWordsLoad(&words,argv[11],25));
    assert(!words.ready);
    assert(!p3dSourceMaterialWordsLoad(&words,argv[12],25));
    assert(!words.ready);
    assert(!p3dSourceMaterialWordsLoad(&words,argv[13],25));
    assert(!words.ready);
    assert(p3dSourceMaterialWordsLoad(&words,argv[14],25));
    assert(!p3dSourceMaterialWordsMatch(&words,&shaders,&source,25,3));
    assert(!p3dSourceMaterialWordsLoad(&words,NULL,25));
    assert(!words.ready);
    puts("C113: source C5 13-dword material provenance and shader flags: PASS");
    return 0;
}
