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
/* One capture transaction: read a validated frame, stage its RGB565 pixels,
 * and fail closed on invalid destination/aliasing. The caller owns the buffer
 * and must only present it after a successful return. No hardware or VRAM
 * access is performed here. */
int p3dCameraCapturePreview(P3DCameraSession *session,
                            uint16_t *destination, size_t destination_pixels);
#endif
