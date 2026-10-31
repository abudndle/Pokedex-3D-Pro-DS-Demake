#include "texture_pixels.h"
#include <stdio.h>
#include <string.h>

static unsigned rd16(const unsigned char *p) {
    return (unsigned)p[0] | ((unsigned)p[1] << 8);
}

/* P3PX v1 is legacy direct color; v2 stores DS A1 RGB555 (bit 15 alpha).
 * Both carry exactly width*height LE 16-bit words. No alpha is invented. */
int p3dTexturePixelsLoad(P3DTexturePixels *image, const char *path) {
    unsigned char h[10], pixel[2];
    FILE *f;
    unsigned version, w, hgt;
    if (!image) return 0;
    image->ready = 0;
    image->width = 0;
    image->height = 0;
    if (!path) return 0;
    f = fopen(path, "rb");
    if (!f) return 0;
    if (fread(h, 1, sizeof(h), f) != sizeof(h) ||
        memcmp(h, "P3PX", 4) != 0) {
        fclose(f);
        return 0;
    }
    version = rd16(h + 4);
    w = rd16(h + 6);
    hgt = rd16(h + 8);
    if ((version != 1 && version != 2) ||
        w < 8 || hgt < 8 || w > 256 || hgt > 256 ||
        (w & (w - 1)) || (hgt & (hgt - 1))) {
        fclose(f);
        return 0;
    }
    for (unsigned i = 0; i < w * hgt; ++i) {
        if (fread(pixel, 1, 2, f) != 2) {
            fclose(f);
            return 0;
        }
        image->pixels[i] = (uint16_t)rd16(pixel);
    }
    if (fgetc(f) != EOF || ferror(f)) {
        fclose(f);
        return 0;
    }
    fclose(f);
    image->width = (uint16_t)w;
    image->height = (uint16_t)hgt;
    image->ready = 1;
    return 1;
}
