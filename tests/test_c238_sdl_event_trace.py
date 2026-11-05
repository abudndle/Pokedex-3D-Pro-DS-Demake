"""C238 synthetic LD_PRELOAD/SDL2 ABI diagnostic tests; no game assets."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).with_name("c238_sdl_event_trace.c")


@unittest.skipUnless(shutil.which("cc"), "C compiler unavailable")
class C238TraceTests(unittest.TestCase):
    def test_sdl2_event_and_glib_key_reads_are_observed_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hook = root / "hook.so"
            fake = root / "libfake.so"
            main = root / "test_main"
            (root / "fake.c").write_text(r"""
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
int SDL_PollEvent(void *event) {
    static int called = 0;
    if (called++) return 0;
    memset(event, 0, 56);
    uint32_t type=0x300, scan=7;
    int32_t sym=(int32_t)atoi(getenv("C238_TEST_SYM") ? getenv("C238_TEST_SYM") : "100");
    memcpy((char *)event, &type, 4);
    memcpy((char *)event+16, &scan, 4);
    memcpy((char *)event+20, &sym, 4);
    return 1;
}
int g_key_file_load_from_file(void *a, const char *b, int c, void *d) {
    (void)a; (void)b; (void)c; (void)d; return 1;
}
int g_key_file_has_group(void *a, const char *b) {
    (void)a; (void)b; return 1;
}
int g_key_file_get_integer(void *a, const char *b, const char *c, void *d) {
    (void)a; (void)b; (void)c; (void)d; return 98;
}
""")
            (root / "main.c").write_text(r"""
#include <stdint.h>
#include <stdio.h>
extern int SDL_PollEvent(void *);
extern int g_key_file_load_from_file(void *, const char *, int, void *);
extern int g_key_file_get_integer(void *, const char *, const char *, void *);
extern int g_key_file_has_group(void *, const char *);
int main(void) {
    unsigned char event[56] = {0};
    int load = g_key_file_load_from_file(0,"isolated",0,0);
    int group = g_key_file_has_group(0,"KEYS");
    int key = g_key_file_get_integer(0,"KEYS","B",0);
    int ret = SDL_PollEvent(event);
    int32_t sym = 0;
    __builtin_memcpy(&sym, event+20, 4);
    printf("load=%d group=%d key=%d ret=%d sym=%d\\n",load,group,key,ret,sym);
    return 0;
}
""")
            for cmd in (
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fPIC",
                 "-shared", str(SOURCE), "-ldl", "-o", str(hook)],
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fPIC",
                 "-shared", str(root / "fake.c"), "-o", str(fake)],
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                 str(root / "main.c"), "-L", str(root), "-lfake",
                 "-Wl,-rpath," + str(root), "-o", str(main)],
            ):
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            env = {**os.environ, "LD_PRELOAD": str(hook), "P3D_C238_TRACE": "1"}
            proc = subprocess.run([str(main)], env=env, capture_output=True,
                                  text=True, check=True)
            self.assertIn("load=1 group=1 key=98 ret=1 sym=100", proc.stdout)
            self.assertIn("C238 GLib config_loaded=1", proc.stderr)
            self.assertIn("C238 GLib has_group=KEYS result=1", proc.stderr)
            self.assertIn("C238 GLib KEYS B=98", proc.stderr)
            self.assertIn("C238 SDL event=down scancode=7 sym=100", proc.stderr)
            env.pop("P3D_C238_TRACE")
            proc = subprocess.run([str(main)], env=env, capture_output=True,
                                  text=True, check=True)
            self.assertEqual(proc.stderr, "")
            self.assertIn("sym=100", proc.stdout)
            for original, expected in (("100", "229"), ("98", "0"),
                                       ("107", "0"), ("105", "13")):
                env = {**os.environ, "LD_PRELOAD": str(hook),
                       "P3D_C238_TRACE": "1", "P3D_C240_ADAPT_0913": "1",
                       "C238_TEST_SYM": original}
                proc = subprocess.run([str(main)], env=env,
                                      capture_output=True, text=True, check=True)
                self.assertIn("sym=" + expected, proc.stdout)
                self.assertIn("C240 DeSmuME 0.9.13 SDL key remap " + original
                              + " -> " + expected, proc.stderr)


if __name__ == "__main__":
    unittest.main()
