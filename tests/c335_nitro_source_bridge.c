#include "nitro_source_bridge.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#ifdef P3D_USE_NITRO_ENGINE
#include <NEMain.h>
struct NE_Model { const void *data; NE_ModelType type; };
struct NE_Animation { const void *data; };
static NE_Model model;
static NE_Animation animation;
static const void *asset_manifest,*asset_mesh,*asset_anim;
static size_t mesh_size,anim_size;
static unsigned opens,draws,deletes;
FILE *test_fopen(const char *path,const char *mode){
    assert(strcmp(mode,"rb")==0);
    const char *ext=strrchr(path,'.');
    assert(ext);
    const void *data;
    size_t size;
    if(!strcmp(ext,".p3ne")){data=asset_manifest;size=36;}
    else if(!strcmp(ext,".dsa")){data=asset_anim;size=anim_size;}
    else{data=asset_mesh;size=mesh_size;}
    opens++;
    FILE *file=tmpfile();
    assert(file && fwrite(data,1,size,file)==size && !fseek(file,0,SEEK_SET));
    return file;
}
int NE_ModelSystemReset(int count){assert(count==2);return 0;}
int NE_AnimationSystemReset(int count){assert(count==2);return 0;}
void NE_ModelSystemEnd(void){}
void NE_DisplayListSetDefaultFunction(NE_DisplayListFunction fn){assert(fn==NE_DL_CPU);}
NE_Model *NE_ModelCreate(NE_ModelType type){model=(NE_Model){.type=type};return &model;}
NE_Animation *NE_AnimationCreate(void){animation.data=NULL;return &animation;}
/* Simulate a changed payload on the engine's second filesystem read. */
int NE_ModelLoadStaticMeshFAT(NE_Model *m,const char *path){
    static const unsigned char replaced[12]={0};
    (void)path;m->data=replaced;opens++;return 1;
}
int NE_ModelLoadDSMFAT(NE_Model *m,const char *path){(void)m;(void)path;return 0;}
int NE_AnimationLoadFAT(NE_Animation *a,const char *path){(void)a;(void)path;return 0;}
int NE_ModelLoadStaticMesh(NE_Model *m,const void *bytes){
    assert(m==&model && m->type==NE_Static);m->data=bytes;return 1;
}
int NE_ModelLoadDSM(NE_Model *m,const void *bytes){
    assert(m==&model && m->type==NE_Animated);m->data=bytes;return 1;
}
int NE_AnimationLoad(NE_Animation *a,const void *bytes){assert(a==&animation);a->data=bytes;return 1;}
void NE_ModelSetAnimation(NE_Model *m,NE_Animation *a){assert(m==&model && a==&animation);}
void NE_ModelAnimStart(NE_Model *m,NE_AnimationType mode,int32_t speed){
    assert(m==&model && mode==NE_ANIM_LOOP && speed>0);
}
void NE_ModelDraw(const NE_Model *m){
    assert(m->data && !memcmp(m->data,asset_mesh,mesh_size));
    if(m->type==NE_Animated)assert(animation.data && !memcmp(animation.data,asset_anim,anim_size));
    draws++;
}
void NE_ModelAnimateAll(void){}
void NE_ModelDelete(NE_Model *m){
    if(m->data)assert(!memcmp(m->data,asset_mesh,mesh_size));
    m->data=NULL;deletes++;
}
void NE_AnimationDelete(NE_Animation *a){
    assert(a->data && !memcmp(a->data,asset_anim,anim_size));a->data=NULL;deletes++;
}
#endif
static void w16(unsigned char *b,unsigned n){b[0]=(unsigned char)n;b[1]=(unsigned char)(n>>8);}
static void w32(unsigned char *b,uint32_t n){w16(b,n);w16(b+2,n>>16);}
static void manifest(unsigned char b[36],uint16_t model,int kind,
  const void *vx,size_t vx_len,const void *ix,size_t ix_len,
  const void *mesh,size_t mesh_len,const void *anim,size_t anim_len){
 memset(b,0,36);
 memcpy(b,"P3NE",4);b[4]=1;b[5]=(unsigned char)kind;w16(b+6,model);
 w32(b+8,p3dNitroCrc32(vx,vx_len));
 w32(b+12,p3dNitroCrc32(ix,ix_len));
 w32(b+16,(uint32_t)mesh_len);w32(b+20,p3dNitroCrc32(mesh,mesh_len));
 w32(b+24,(uint32_t)anim_len);
 w32(b+28,anim_len?p3dNitroCrc32(anim,anim_len):0);
 w32(b+32,p3dNitroCrc32(b,32));
}
int main(void){
 unsigned char vx[8]={0x50,0x33,0x56,0x58,0x19,0,0,1};
 unsigned char ix[8]={0x50,0x33,0x49,0x58,0x19,0,0,1};
 unsigned char dl[12]={0};w32(dl,2);w32(dl+4,0x41);w32(dl+8,0);
 unsigned char dsa[68]={0};
 w32(dsa,1);w32(dsa+4,2);w32(dsa+8,1);
 unsigned char b[36],copy[36],changed[68];
 P3DNitroManifest m={0};
 manifest(b,25,P3D_NITRO_STATIC,vx,sizeof vx,ix,sizeof ix,
          dl,sizeof dl,NULL,0);
 assert(p3dNitroManifestValidate(b,36,25,vx,sizeof vx,ix,sizeof ix,&m));
 assert(m.kind==P3D_NITRO_STATIC&&m.model_size==sizeof dl);
 assert(p3dNitroPayloadValidate(&m,dl,sizeof dl,NULL,0));
 memcpy(copy,b,sizeof b);copy[4]=2;assert(!p3dNitroManifestValidate(copy,36,25,vx,8,ix,8,&m));
 memcpy(copy,b,sizeof b);copy[5]=3;w32(copy+32,p3dNitroCrc32(copy,32));
 assert(!p3dNitroManifestValidate(copy,36,25,vx,8,ix,8,&m));
 assert(!p3dNitroManifestValidate(b,36,24,vx,8,ix,8,&m));
 assert(!p3dNitroManifestValidate(b,36,721,vx,8,ix,8,&m));
 assert(!p3dNitroManifestValidate(b,35,25,vx,8,ix,8,&m));
 assert(!p3dNitroManifestValidate(b,37,25,vx,8,ix,8,&m));
 ix[0]^=1;assert(!p3dNitroManifestValidate(b,36,25,vx,8,ix,8,&m));ix[0]^=1;
 vx[0]^=1;assert(!p3dNitroManifestValidate(b,36,25,vx,8,ix,8,&m));vx[0]^=1;
 assert(p3dNitroManifestValidate(b,36,25,vx,8,ix,8,&m));
 dl[7]^=1;assert(!p3dNitroPayloadValidate(&m,dl,sizeof dl,NULL,0));dl[7]^=1;
 assert(!p3dNitroPayloadValidate(&m,dl,8,NULL,0));
 assert(!p3dNitroPayloadValidate(&m,dl,sizeof dl,dsa,sizeof dsa));
 manifest(b,25,P3D_NITRO_ANIMATED,vx,8,ix,8,
          dl,sizeof dl,dsa,sizeof dsa);
 assert(p3dNitroManifestValidate(b,36,25,vx,8,ix,8,&m));
 assert(p3dNitroPayloadValidate(&m,dl,sizeof dl,dsa,sizeof dsa));
 /* Official DSMA packets encode four command bytes then parameters. A
  * one-joint DSA only initializes joint matrix slot 30. */
 unsigned char joint_dl[16]={0};
 w32(joint_dl,3);w32(joint_dl+4,0x00411440); /* begin, restore, end, nop */
 w32(joint_dl+12,30);
 manifest(b,25,P3D_NITRO_ANIMATED,vx,8,ix,8,
          joint_dl,sizeof joint_dl,dsa,sizeof dsa);
 assert(p3dNitroManifestValidate(b,36,25,vx,8,ix,8,&m));
 assert(p3dNitroPayloadValidate(&m,joint_dl,sizeof joint_dl,dsa,sizeof dsa));
 w32(joint_dl+12,29); /* Valid for two joints, never populated by this DSA. */
 manifest(b,25,P3D_NITRO_ANIMATED,vx,8,ix,8,
          joint_dl,sizeof joint_dl,dsa,sizeof dsa);
 assert(p3dNitroManifestValidate(b,36,25,vx,8,ix,8,&m));
 assert(!p3dNitroPayloadValidate(&m,joint_dl,sizeof joint_dl,dsa,sizeof dsa));
 w32(joint_dl,2); /* Declared word count is valid, but restore lacks its argument. */
 manifest(b,25,P3D_NITRO_ANIMATED,vx,8,ix,8,
          joint_dl,12,dsa,sizeof dsa);
 assert(p3dNitroManifestValidate(b,36,25,vx,8,ix,8,&m));
 assert(!p3dNitroPayloadValidate(&m,joint_dl,12,dsa,sizeof dsa));
 memcpy(changed,dsa,sizeof dsa);w32(changed+8,29); /* >28 stack-bounded bones */
 manifest(b,25,P3D_NITRO_ANIMATED,vx,8,ix,8,
          dl,sizeof dl,changed,sizeof changed);
 assert(p3dNitroManifestValidate(b,36,25,vx,8,ix,8,&m));
 assert(!p3dNitroPayloadValidate(&m,dl,sizeof dl,changed,sizeof changed));
 memcpy(changed,dsa,sizeof dsa);w32(changed+4,0);
 manifest(b,25,P3D_NITRO_ANIMATED,vx,8,ix,8,
          dl,sizeof dl,changed,sizeof changed);
 assert(p3dNitroManifestValidate(b,36,25,vx,8,ix,8,&m));
 assert(!p3dNitroPayloadValidate(&m,dl,sizeof dl,changed,sizeof changed));
 memcpy(changed,dsa,sizeof dsa);w32(changed+4,257);
 manifest(b,25,P3D_NITRO_ANIMATED,vx,8,ix,8,
          dl,sizeof dl,changed,sizeof changed);
 assert(p3dNitroManifestValidate(b,36,25,vx,8,ix,8,&m));
 assert(!p3dNitroPayloadValidate(&m,dl,sizeof dl,changed,sizeof changed));
#ifdef P3D_USE_NITRO_ENGINE
 asset_manifest=b;asset_mesh=dl;mesh_size=sizeof dl;
 assert(p3dNitroBridgeInit());
 manifest(b,25,P3D_NITRO_STATIC,vx,8,ix,8,dl,sizeof dl,NULL,0);
 assert(p3dNitroBridgeLoad(25,vx,8,ix,8));
 assert(p3dNitroBridgeDraw() && opens==2 && draws==1);
 assert(!p3dNitroBridgeAnimated());
 asset_anim=dsa;anim_size=sizeof dsa;
 manifest(b,25,P3D_NITRO_ANIMATED,vx,8,ix,8,dl,sizeof dl,dsa,sizeof dsa);
 assert(p3dNitroBridgeLoad(25,vx,8,ix,8));
 assert(p3dNitroBridgeAnimated() && deletes==1);
 assert(p3dNitroBridgeDraw() && opens==5 && draws==2);
 p3dNitroBridgeUnload();
 assert(deletes==3);
#else
 assert(!p3dNitroBridgeInit()); /* host has no DS GPU; no fake success */
#endif
 assert(!p3dNitroBridgeDraw());
 assert(!p3dNitroBridgeAnimated());
 p3dNitroBridgeUnload();
 puts("C335 source-pair-locked Nitro Engine/DSMA render preflight: PASS (synthetic)");
 return 0;
}
