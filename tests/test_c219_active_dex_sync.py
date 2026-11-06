"""Exercise active/resumable Dex navigation through native APIs, not spelling."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = r'''
#include "menu_navigation.h"
#include "resume_state.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
    assert(argc==2);
    int active=25,saved=0;
    assert(p3dDexNavigateSync(&active,&saved,1)==1);
    assert(active==26&&saved==26);
    P3DResumeState state={0},loaded;
    state.page=P3D_PAGE_DEX;state.dex=(unsigned short)active;
    state.selected_dex=(unsigned short)saved;
    assert(p3dResumeStore(argv[1],&state));
    assert(p3dResumeLoad(argv[1],&loaded));
    assert(loaded.dex==26&&loaded.selected_dex==26);
    active=648;saved=25;
    assert(p3dDexNavigateSync(&active,&saved,1)==1);
    assert(active==648&&saved==648);
    assert(p3dDexNavigateSync(&active,&saved,-1)==1);
    assert(active==647&&saved==647);
    puts("Active Dex and saved selection navigation: PASS");
    return 0;
}
'''

class ActiveDexSynchronizationTests(unittest.TestCase):
    def test_navigation_and_checkpoint_keep_both_selections(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'driver.c').write_text(DRIVER)
            executable = root / 'navigation'
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-Isource', str(root / 'driver.c'),
                            'source/menu_navigation.c', 'source/menu_layout.c',
                            'source/resume_state.c', 'source/feature_menu.c',
                            'source/dsi_features.c', '-o', str(executable)],
                           cwd=ROOT, check=True)
            result = subprocess.run([str(executable), str(root / 'pokedex')],
                                    check=True, text=True, capture_output=True)
            self.assertIn('PASS', result.stdout)

if __name__ == "__main__":
    unittest.main()
