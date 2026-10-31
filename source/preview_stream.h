#ifndef C7_PREVIEW_STREAM_H
#define C7_PREVIEW_STREAM_H
#ifdef __cplusplus
extern "C" {
#endif
int previewStreamInit(void);
int previewStreamLoad(int resource_index);
int previewStreamHasModel(void);
int previewStreamHasUv(void);
int previewStreamTriangleCount(void);
int previewStreamOriginalTriangleCount(void);
/* With verified texture+UV only, use white vertices to avoid tinting RGB555. */
void previewStreamDrawMode(int textured);
void previewStreamDraw(void);
#ifdef __cplusplus
}
#endif
#endif
