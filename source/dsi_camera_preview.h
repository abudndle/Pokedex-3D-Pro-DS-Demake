#ifndef P3D_DSI_CAMERA_PREVIEW_H
#define P3D_DSI_CAMERA_PREVIEW_H
#include "dsi_camera_session.h"
/* Host-testable staging only. Caller must own a separate 256x192 RGB565
 * destination. No VRAM, camera registers or graphics-mode changes here. */
#define P3D_PREVIEW_WIDTH 256u
#define P3D_PREVIEW_HEIGHT 192u
#define P3D_PREVIEW_PIXELS (P3D_PREVIEW_WIDTH * P3D_PREVIEW_HEIGHT)
int p3dCameraPreviewStage(const P3DCameraFrame *source,
                          uint16_t *destination, size_t destination_pixels);
#endif
