#ifndef P3D_DSI_CAMERA_SESSION_H
#define P3D_DSI_CAMERA_SESSION_H
#include <stddef.h>
#include <stdint.h>
/* Platform-neutral safety boundary. Does not access DSi hardware itself. */
typedef enum {
    P3D_CAMERA_UNAVAILABLE=0, P3D_CAMERA_CLOSED,
    P3D_CAMERA_OPEN, P3D_CAMERA_STREAMING, P3D_CAMERA_ERROR
} P3DCameraState;
typedef enum { P3D_CAMERA_RGB565=1 } P3DCameraFormat;
typedef struct {
    uint16_t width, height, stride_bytes;
    P3DCameraFormat format;
    const void *pixels;
    size_t bytes;
} P3DCameraFrame;
/* A real DSi ARM7/ARM9 implementation must supply these callbacks. */
typedef struct {
    int (*open)(void *ctx);
    int (*read)(void *ctx, P3DCameraFrame *frame);
    void (*close)(void *ctx);
    void *ctx;
} P3DCameraBackend;
typedef struct {
    P3DCameraBackend backend;
    P3DCameraState state;
    unsigned frames_received;
    int owns_device;
} P3DCameraSession;
void p3dCameraSessionInit(P3DCameraSession *session);
int p3dCameraSessionOpen(P3DCameraSession *session, int is_dsi, P3DCameraBackend backend);
int p3dCameraSessionRead(P3DCameraSession *session, P3DCameraFrame *out);
void p3dCameraSessionClose(P3DCameraSession *session);
int p3dCameraFrameValid(const P3DCameraFrame *frame);
#endif
