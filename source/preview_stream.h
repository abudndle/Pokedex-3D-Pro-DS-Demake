#ifndef C7_PREVIEW_STREAM_H
#define C7_PREVIEW_STREAM_H
#ifdef __cplusplus
extern "C" {
#endif
int previewStreamInit(void);
int previewStreamLoad(int resource_index);
int previewStreamHasModel(void);
int previewStreamTriangleCount(void);
int previewStreamOriginalTriangleCount(void);
void previewStreamDraw(void);
#ifdef __cplusplus
}
#endif
#endif
