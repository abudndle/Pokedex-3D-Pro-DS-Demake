/* C238: asset-free DeSmuME CLI input diagnostic only.
 * LD_PRELOAD hook records actual SDL2 keysyms and GLib key-file lookup
 * results without altering the events or the original game input path.
 * The SDL2 keyboard-event offsets are verified by a synthetic ABI test.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int enabled(void) {
    const char *s = getenv("P3D_C238_TRACE");
    return s && strcmp(s, "1") == 0;
}

int SDL_PollEvent(void *event) {
    int (*original)(void *) = NULL;
    *(void **)(&original) = dlsym(RTLD_NEXT, "SDL_PollEvent");
    if (!original) {
        fputs("C238: missing SDL_PollEvent symbol\n", stderr);
        abort();
    }
    int result = original(event);
    if (enabled() && result && event) {
        uint32_t type = 0;
        memcpy(&type, (const unsigned char *)event, sizeof(type));
        if (type == 0x300u || type == 0x301u) {
            uint32_t scancode = 0;
            int32_t keysym = 0;
            memcpy(&scancode, (const unsigned char *)event + 16, sizeof(scancode));
            memcpy(&keysym, (const unsigned char *)event + 20, sizeof(keysym));
            fprintf(stderr, "C238 SDL event=%s scancode=%u sym=%d\n",
                    type == 0x300u ? "down" : "up", scancode, keysym);
            fflush(stderr);
        }
    }
    return result;
}

int g_key_file_load_from_file(void *file, const char *filename,
                              int flags, void *error) {
    int (*original)(void *, const char *, int, void *) = NULL;
    *(void **)(&original) = dlsym(RTLD_NEXT, "g_key_file_load_from_file");
    if (!original) abort();
    int result = original(file, filename, flags, error);
    if (enabled()) {
        fprintf(stderr, "C238 GLib config_loaded=%d\n", result);
        fflush(stderr);
    }
    return result;
}

int g_key_file_get_integer(void *file, const char *group,
                           const char *key, void *error) {
    int (*original)(void *, const char *, const char *, void *) = NULL;
    *(void **)(&original) = dlsym(RTLD_NEXT, "g_key_file_get_integer");
    if (!original) abort();
    int result = original(file, group, key, error);
    if (enabled() && group && key && (strcmp(group, "KEYS") == 0 || strcmp(group, "SDLKEYS") == 0)) {
        fprintf(stderr, "C238 GLib %s %s=%d\n", group, key, result);
        fflush(stderr);
    }
    return result;
}

int g_key_file_has_group(void *file, const char *group) {
    int (*original)(void *, const char *) = NULL;
    *(void **)(&original) = dlsym(RTLD_NEXT, "g_key_file_has_group");
    if (!original) abort();
    int result = original(file, group);
    if (enabled() && group) {
        fprintf(stderr, "C238 GLib has_group=%s result=%d\n", group, result);
        fflush(stderr);
    }
    return result;
}
