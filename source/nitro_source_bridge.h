#ifndef P3D_NITRO_SOURCE_BRIDGE_H
#define P3D_NITRO_SOURCE_BRIDGE_H
#include <stddef.h>
#include <stdint.h>

/* C335: optional Nitro Engine + DSMA path for independently verified
 * ORIGINAL-source P3VX/P3IX geometry. Never creates replica Pokemon.
 * A P3NE hash binds the converted display list/DSM to the source pair.
 * The source evidence MUST be independently checked in private first. */
#define P3D_NITRO_MANIFEST_SIZE 36u
#define P3D_NITRO_MAX_MODEL_BYTES 262144u
#define P3D_NITRO_MAX_ANIM_BYTES 262144u
#define P3D_NITRO_MAX_BONES 28u
#define P3D_NITRO_MAX_ANIM_FRAMES 256u

enum { P3D_NITRO_STATIC=1, P3D_NITRO_ANIMATED=2 };
typedef struct {
    uint16_t resource;
    uint8_t kind;
    uint32_t source_vx_crc, source_ix_crc;
    uint32_t model_size, model_crc, anim_size, anim_crc;
} P3DNitroManifest;

/* Pure, host-testable preflight; a valid CRC is not Nintendo provenance. */
uint32_t p3dNitroCrc32(const void *bytes,size_t length);
int p3dNitroManifestValidate(const void *raw,size_t size,uint16_t resource,
    const void *source_vx,size_t vx_size,const void *source_ix,size_t ix_size,
    P3DNitroManifest *out);
int p3dNitroPayloadValidate(const P3DNitroManifest *manifest,
    const void *model,size_t model_size,const void *anim,size_t anim_size);

/* The existing libnds renderer, text consoles and source model loader stay
 * in control. Nitro Engine's MODEL/ANIMATION subsystems are optional only. */
int p3dNitroBridgeInit(void);
void p3dNitroBridgeUnload(void);
int p3dNitroBridgeLoad(uint16_t resource,const void *vx,size_t vx_size,
    const void *ix,size_t ix_size);
int p3dNitroBridgeDraw(void);
void p3dNitroBridgeFrame(void);
int p3dNitroBridgeAnimated(void);
#endif
