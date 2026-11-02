/* Asset-free cross-language C207 P3VX fixture acceptance probe. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "verified_vertex_stream.h"

#define LIMIT (16u + 64u * 8u + 8192u * 6u)

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *file = fopen(argv[1], "rb");
    if (!file) return 3;
    if (fseek(file, 0, SEEK_END) != 0) { fclose(file); return 3; }
    long size = ftell(file);
    if (size < 16 || (unsigned long)size > LIMIT ||
        fseek(file, 0, SEEK_SET) != 0) { fclose(file); return 3; }
    uint8_t *bytes = malloc((size_t)size);
    if (!bytes) { fclose(file); return 4; }
    int result = 5;
    if (fread(bytes, 1, (size_t)size, file) == (size_t)size) {
        P3DPrimitiveVertices meshes[64];
        int16_t xyz[8192 * 3];
        size_t decoded = 0;
        if (p3dVerifiedVerticesDecode(bytes, (size_t)size, 14, meshes, 64,
                                      xyz, 8192 * 3, &decoded) &&
            decoded == 1 && meshes[0].mesh_id == 0 &&
            meshes[0].vertex_count == 3 &&
            xyz[0] == 1024 && xyz[2] == -2048 &&
            xyz[3] == 4096 && xyz[4] == 8192 && xyz[5] == 12288)
            result = 0;
    }
    free(bytes);
    fclose(file);
    return result;
}
