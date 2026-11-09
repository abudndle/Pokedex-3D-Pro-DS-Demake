"""C219 source-contract regression for synchronized active Pokédex navigation."""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "source" / "main.c").read_text()

class ActiveDexSynchronizationTests(unittest.TestCase):
    def test_button_navigation_uses_sync_helper_both_directions(self):
        # The helper updates the active entry AND the saved/selected entry together.
        self.assertIn("p3dDexNavigateSync(&dex_index,&state.selected_dex,-1)", SOURCE)
        self.assertIn("p3dDexNavigateSync(&dex_index,&state.selected_dex,1)", SOURCE)

    def test_touch_navigation_uses_same_sync_helper(self):
        self.assertIn("p3dDexNavigateSync(&dex_index,&state.selected_dex,direction)", SOURCE)

    def test_no_unsynchronized_dex_navigation_remains(self):
        # An unsynced step leaves state.selected_dex stale for resume checkpoints.
        self.assertNotIn("p3dDexNavigate(dex_index,", SOURCE)

if __name__ == "__main__":
    unittest.main()
