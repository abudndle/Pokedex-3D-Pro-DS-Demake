#include "nitro_source_bridge.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
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
 assert(!p3dNitroBridgeInit()); /* host has no DS GPU; no fake success */
 assert(!p3dNitroBridgeDraw());
 assert(!p3dNitroBridgeAnimated());
 p3dNitroBridgeUnload();
 puts("C335 source-pair-locked Nitro Engine/DSMA render preflight: PASS (synthetic)");
 return 0;
}
