#ifndef C7_PREVIEW_STREAM_H
#define C7_PREVIEW_STREAM_H
#ifdef __cplusplus
extern "C" {
#endif
int previewStreamInit(void);
int previewStreamLoad(int resource_index);
int previewStreamHasModel(void);
int previewStreamHasUv(void);
/* Only normalized source UV coordinates inside [0,1] can be sampled without
 * knowing the original C5 GPU wrap/repeat modes. Per material face range. */
int previewStreamUvRangeUnit(int first_triangle,int triangle_count);
/* P3CS is a geometry-only diagnostic path until GPU sampler roles are proven. */
int previewStreamIsChunked(void);
/* Explicit diagnostic preference; default is legacy DS3M. */
void previewStreamPreferChunks(int enabled);
int previewStreamPrefersChunks(void);
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
