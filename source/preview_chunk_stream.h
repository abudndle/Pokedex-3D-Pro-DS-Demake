#ifndef P3D_PREVIEW_CHUNK_STREAM_H
#define P3D_PREVIEW_CHUNK_STREAM_H
#include <stdint.h>
#include <stdio.h>
#define P3D_CHUNK_TRIANGLES 600u
#define P3D_CHUNK_MAX 3u
#define P3D_CHUNK_RECORD_BYTES 33u
#define P3D_CHUNK_MAX_TOTAL (P3D_CHUNK_TRIANGLES * P3D_CHUNK_MAX)
/* P3CS: original-derived source triangles, streamed 600 per read. Texture
 * bindings are NOT implied by geometry or P3CS. Keep original assets private. */
typedef struct {
    uint32_t first_triangle, offset, crc32;
    uint16_t triangles;
} P3DChunkInfo;
typedef struct {
    FILE *file;
    uint16_t model_id, chunk_count;
    uint32_t total_triangles, original_triangles;
    P3DChunkInfo chunks[P3D_CHUNK_MAX];
    int ready;
} P3DChunkStream;
/* Call on a zero-initialized stream; safely closes an existing open file. */
void p3dChunkClose(P3DChunkStream *stream);
int p3dChunkOpen(P3DChunkStream *stream,const char *path,unsigned model_id);
int p3dChunkRead(P3DChunkStream *stream,unsigned index,
                 int16_t xyz[P3D_CHUNK_TRIANGLES*9],
                 int16_t uv[P3D_CHUNK_TRIANGLES*6],
                 unsigned char rgb[P3D_CHUNK_TRIANGLES*3]);
#endif
