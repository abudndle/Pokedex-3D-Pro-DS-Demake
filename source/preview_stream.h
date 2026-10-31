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
/* Texture dimensions convert normalized 4.12 source UVs to DS texel-space 12.4. */
/* Draw a contiguous material range; bounds-checked before any GL call. */
void previewStreamDrawRange(int first_triangle,int triangle_count,int texture_width,int texture_height);
void previewStreamDrawMode(int texture_width,int texture_height);
void previewStreamDraw(void);
#ifdef __cplusplus
}
#endif
#endif
