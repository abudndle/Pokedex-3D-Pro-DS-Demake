#include "nitro_source_bridge.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint16_t get16(const unsigned char *p){
    return (uint16_t)((unsigned)p[0]|((unsigned)p[1]<<8));
}
static uint32_t get32(const unsigned char *p){
    return (uint32_t)get16(p)|((uint32_t)get16(p+2)<<16);
}
uint32_t p3dNitroCrc32(const void *bytes,size_t n){
    const unsigned char *p=(const unsigned char *)bytes;
    uint32_t crc=0xffffffffu;
    if(!p)return 0;
    for(size_t i=0;i<n;i++){
        crc^=p[i];
        for(unsigned bit=0;bit<8;bit++)
            crc=(crc>>1)^((crc&1u)?0xedb88320u:0);
    }
    return ~crc;
}
static int valid_resource(uint16_t id){
    return id<=733u && !(id>=721u && id<=724u);
}
int p3dNitroManifestValidate(const void *raw,size_t size,uint16_t resource,
    const void *source_vx,size_t vx_size,const void *source_ix,size_t ix_size,
    P3DNitroManifest *out){
    const unsigned char *p=(const unsigned char *)raw;
    P3DNitroManifest m;
    if(out)memset(out,0,sizeof(*out));
    if(!out || !p || size!=P3D_NITRO_MANIFEST_SIZE ||
       !source_vx || !source_ix || !vx_size || !ix_size ||
       !valid_resource(resource) || memcmp(p,"P3NE",4)!=0 ||
       p[4]!=1 || (p[5]!=P3D_NITRO_STATIC && p[5]!=P3D_NITRO_ANIMATED) ||
       get16(p+6)!=resource || get32(p+32)!=p3dNitroCrc32(p,32))
        return 0;
    memset(&m,0,sizeof(m));
    m.resource=resource;m.kind=p[5];
    m.source_vx_crc=get32(p+8);m.source_ix_crc=get32(p+12);
    m.model_size=get32(p+16);m.model_crc=get32(p+20);
    m.anim_size=get32(p+24);m.anim_crc=get32(p+28);
    if(m.source_vx_crc!=p3dNitroCrc32(source_vx,vx_size) ||
       m.source_ix_crc!=p3dNitroCrc32(source_ix,ix_size) ||
       m.model_size<8 || m.model_size>P3D_NITRO_MAX_MODEL_BYTES ||
       (m.model_size&3u) ||
       (m.kind==P3D_NITRO_STATIC && (m.anim_size||m.anim_crc)) ||
       (m.kind==P3D_NITRO_ANIMATED &&
        (m.anim_size<8||m.anim_size>P3D_NITRO_MAX_ANIM_BYTES||
         (m.anim_size&3u))))return 0;
    *out=m;
    return 1;
}
/* The pinned md5_to_dsma converter packs four opcodes per FIFO command
 * word, followed by their parameters in opcode order. Check its geometry
 * commands and make sure restore slots belong to the paired animation. */
static int animated_list_valid(const unsigned char *data,size_t size,uint32_t bones){
    size_t pos=4;
    while(pos<size){
        uint32_t commands=get32(data+pos);
        pos+=4;
        for(unsigned i=0;i<4;i++,commands>>=8){
            unsigned opcode=commands&0xffu;
            unsigned words;
            switch(opcode){
            case 0x00: /* NOP */
            case 0x41: /* END */
                words=0;break;
            case 0x14: /* MTX_RESTORE */
            case 0x20: /* COLOR */
            case 0x21: /* NORMAL */
            case 0x22: /* TEXCOORD */
            case 0x24: case 0x25: case 0x26: case 0x27: case 0x28: /* Short vertices */
            case 0x40: /* BEGIN */
                words=1;break;
            case 0x23: /* VTX_16 */
                words=2;break;
            default:
                return 0;
            }
            if(words>(size-pos)/4u)return 0;
            if(opcode==0x14){
                uint32_t slot=get32(data+pos);
                /* Slot 1 is used for the converter's optional normal overlay. */
                if(slot!=1u&&(slot<31u-bones||slot>30u))return 0;
            }
            pos+=words*4u;
        }
    }
    return 1;
}

int p3dNitroPayloadValidate(const P3DNitroManifest *m,
    const void *model,size_t model_size,const void *anim,size_t anim_size){
    const unsigned char *p=(const unsigned char *)model;
    if(!m||!p||!valid_resource(m->resource)||
       model_size!=m->model_size || model_size<8 ||
       (model_size&3u) || model_size>P3D_NITRO_MAX_MODEL_BYTES ||
       p3dNitroCrc32(p,model_size)!=m->model_crc)
        return 0;
    /* Nitro Engine static and DSMA model meshes are DS hardware display
     * lists. Word zero is the number of following GXFIFO parameter words. */
    if(get32(p)>((model_size-4u)/4u) ||
       get32(p)!=(model_size-4u)/4u)
        return 0;
    if(m->kind==P3D_NITRO_STATIC)
        return anim_size==0 && anim==NULL && !m->anim_size && !m->anim_crc;
    if(m->kind!=P3D_NITRO_ANIMATED||!anim||anim_size!=m->anim_size ||
       anim_size<8||anim_size>P3D_NITRO_MAX_ANIM_BYTES||
       (anim_size&3u) || p3dNitroCrc32(anim,anim_size)!=m->anim_crc)
        return 0;
    const unsigned char *a=(const unsigned char *)anim;
    /* Original DSMA DSA v1: version, frames, joints, then frame*joint
     * records of three fixed-point position and four quaternion words. */
    if(anim_size<12 || get32(a)!=1)return 0;
    uint32_t frames=get32(a+4),bones=get32(a+8);
    if(!frames||frames>P3D_NITRO_MAX_ANIM_FRAMES ||
       !bones||bones>P3D_NITRO_MAX_BONES ||
       12u+frames*bones*28u!=anim_size)return 0;
    return animated_list_valid(p,model_size,bones);
}
#ifdef P3D_USE_NITRO_ENGINE
#include <NEMain.h>
static int initialized;
static NE_Model *active_model;
static NE_Animation *active_animation;
static unsigned char *active_mesh_bytes,*active_animation_bytes;
static int active_animated;
static int build_path(char out[88],uint16_t id,const char *ext){
    int n=snprintf(out,88,"nitro:/models/nitro/p%03u.%s",
                   (unsigned)id,ext);
    return n>0&&n<88;
}
static int read_exact(const char *path,void *dest,size_t size){
    FILE *f=fopen(path,"rb");
    if(!f)return 0;
    int ok=fread(dest,1,size,f)==size && fgetc(f)==EOF && !ferror(f);
    if(fclose(f)!=0)ok=0;
    return ok;
}
int p3dNitroBridgeInit(void){
    if(initialized)return 1;
    /* Keep the application's 2D consoles, VRAM banks and GL context.
     * Do NOT call NE_Init3D(): it resets all of them. */
    if(NE_ModelSystemReset(2)!=0)return 0;
    if(NE_AnimationSystemReset(2)!=0){
        NE_ModelSystemEnd();
        return 0;
    }
    NE_DisplayListSetDefaultFunction(NE_DL_CPU);
    initialized=1;
    return 1;
}
void p3dNitroBridgeUnload(void){
    if(active_model){NE_ModelDelete(active_model);active_model=NULL;}
    if(active_animation){NE_AnimationDelete(active_animation);active_animation=NULL;}
    free(active_mesh_bytes);active_mesh_bytes=NULL;
    free(active_animation_bytes);active_animation_bytes=NULL;
    active_animated=0;
}
int p3dNitroBridgeLoad(uint16_t resource,const void *vx,size_t vx_size,
    const void *ix,size_t ix_size){
    char path[88];
    unsigned char raw[P3D_NITRO_MANIFEST_SIZE];
    P3DNitroManifest m;
    unsigned char *mesh=NULL,*animation=NULL;
    int ok=0;
    p3dNitroBridgeUnload();
    if(!initialized || !build_path(path,resource,"p3ne") ||
       !read_exact(path,raw,sizeof raw) ||
       !p3dNitroManifestValidate(raw,sizeof raw,resource,vx,vx_size,ix,ix_size,&m))
        return 0;
    mesh=(unsigned char *)malloc(m.model_size);
    if(!mesh)return 0;
    if(!build_path(path,resource,m.kind==P3D_NITRO_STATIC?"dl":"dsm") ||
       !read_exact(path,mesh,m.model_size))goto finish;
    if(m.kind==P3D_NITRO_ANIMATED){
        animation=(unsigned char *)malloc(m.anim_size);
        if(!animation || !build_path(path,resource,"dsa") ||
           !read_exact(path,animation,m.anim_size))goto finish;
    }
    if(!p3dNitroPayloadValidate(&m,mesh,m.model_size,animation,
                               m.kind==P3D_NITRO_STATIC?0:m.anim_size))
        goto finish;
    active_model=NE_ModelCreate(m.kind==P3D_NITRO_STATIC?NE_Static:NE_Animated);
    if(!active_model)goto finish;
    /* Nitro Engine's RAM loaders borrow these exact validated buffers. */
    if(m.kind==P3D_NITRO_STATIC){
        if(!NE_ModelLoadStaticMesh(active_model,mesh))goto finish;
    }else{
        if(!NE_ModelLoadDSM(active_model,mesh))goto finish;
        active_animation=NE_AnimationCreate();
        if(!active_animation || !NE_AnimationLoad(active_animation,animation))goto finish;
        NE_ModelSetAnimation(active_model,active_animation);
        NE_ModelAnimStart(active_model,NE_ANIM_LOOP,1<<11); /* 0.5 frame/VBL */
        active_animated=1;
    }
    active_mesh_bytes=mesh;
    active_animation_bytes=animation;
    ok=1;
finish:
    if(!ok){
        p3dNitroBridgeUnload();
        free(mesh);free(animation);
    }
    return ok;
}
int p3dNitroBridgeDraw(void){
    if(!initialized || !active_model)return 0;
    NE_ModelDraw(active_model);
    return 1;
}
void p3dNitroBridgeFrame(void){
    if(initialized && active_model && active_animated)
        NE_ModelAnimateAll();
}
int p3dNitroBridgeAnimated(void){return active_model && active_animated;}
#else
int p3dNitroBridgeInit(void){return 0;}
void p3dNitroBridgeUnload(void){}
int p3dNitroBridgeLoad(uint16_t resource,const void *vx,size_t vx_size,
    const void *ix,size_t ix_size){
    (void)resource;(void)vx;(void)vx_size;(void)ix;(void)ix_size;
    return 0;
}
int p3dNitroBridgeDraw(void){return 0;}
void p3dNitroBridgeFrame(void){}
int p3dNitroBridgeAnimated(void){return 0;}
#endif
