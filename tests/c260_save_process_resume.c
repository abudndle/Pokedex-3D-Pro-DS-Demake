/* C260: real host process restarts against the native P3SV/P3RV modules.
 * Synthetic-only: does NOT prove DLDI/FAT or emulator save media.
 */
#include "game_save_bridge.h"
#include "resume_state.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void write_state(const char *base, unsigned species, unsigned move,
                        unsigned correct, unsigned total) {
    P3DMenu menu;
    P3DSaveState save;
    P3DResumeState resume = {0};
    p3dMenuReset(&menu);
    menu.rotate = 1;
    menu.backdrop = 2;
    assert(p3dFavoriteToggle(&menu, 25) == 1);
    assert(p3dGameSaveCapture(&save, &menu, (int)species, (int)move,
                              (int)correct, (int)total));
    assert(p3dSaveStore(base, &save));
    resume.page = P3D_PAGE_DEX;
    resume.home = 0;
    resume.highlight = 1;
    resume.dex = (uint16_t)species;
    resume.selected_dex = (uint16_t)species;
    resume.move = (uint16_t)move;
    assert(p3dResumeStore(base, &resume));
}

static void verify_state(const char *base, unsigned species, unsigned move,
                         unsigned correct, unsigned total) {
    P3DMenu menu;
    P3DSaveState save;
    P3DResumeState resume;
    int dex = -1, move_index = -1, home = 1, highlighted = -1;
    p3dMenuReset(&menu);
    assert(p3dSaveLoad(base, &save));
    assert(save.challenge_correct == correct && save.challenge_total == total);
    assert(p3dGameSaveRestore(&save, &menu, &dex, &move_index));
    assert(dex == (int)species && move_index == (int)move);
    assert(menu.rotate == 1 && menu.backdrop == 2);
    assert(p3dFavoriteContains(&menu, 25));
    assert(p3dResumeRestoreBoot(base, &resume, p3dCapabilities(0, 1, 0),
                                &home, &menu, &highlighted));
    assert(home == 0 && menu.page == P3D_PAGE_DEX);
    assert(resume.dex == species && resume.move == move);
    assert(highlighted == 1);
}

static void damage(const char *base, const char *suffix) {
    char path[512];
    int len = snprintf(path, sizeof(path), "%s%s", base, suffix);
    assert(len > 0 && (size_t)len < sizeof(path));
    FILE *f = fopen(path, "wb");
    assert(f);
    assert(fwrite("torn", 1, 4, f) == 4);
    assert(fclose(f) == 0);
}

int main(int argc, char **argv) {
    assert(argc == 3);
    if (strcmp(argv[1], "write-first") == 0)
        write_state(argv[2], 24, 42, 2, 3);
    else if (strcmp(argv[1], "verify-first") == 0)
        verify_state(argv[2], 24, 42, 2, 3);
    else if (strcmp(argv[1], "write-second") == 0)
        write_state(argv[2], 151, 99, 4, 7);
    else if (strcmp(argv[1], "verify-second") == 0)
        verify_state(argv[2], 151, 99, 4, 7);
    else if (strcmp(argv[1], "damage-newest") == 0) {
        damage(argv[2], "_B.sav");
        damage(argv[2], "_resume_B.sav");
    } else return 2;
    return 0;
}
