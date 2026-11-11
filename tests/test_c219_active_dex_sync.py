"""C219 source-contract regression for synchronized active Pokédex navigation."""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "source" / "main.c").read_text()

class ActiveDexSynchronizationTests(unittest.TestCase):
    def test_button_navigation_syncs_both_directions(self):
        self.assertIn("p3dDexNavigateSync(&dex_index,&state.selected_dex,-1)", SOURCE)
        self.assertIn("p3dDexNavigateSync(&dex_index,&state.selected_dex,1)", SOURCE)
        self.assertNotIn("int next=p3dDexNavigate(dex_index,1);", SOURCE)

    def test_touch_navigation_uses_same_synchronized_helper(self):
        self.assertIn(
            "p3dDexNavigateSync(&dex_index,&state.selected_dex,direction)",
            SOURCE,
        )

if __name__ == "__main__":
    unittest.main()
