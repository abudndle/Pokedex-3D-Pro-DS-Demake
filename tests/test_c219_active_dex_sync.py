"""C219 source-contract regression for synchronized active Pokédex navigation."""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "source" / "main.c").read_text()

class ActiveDexSynchronizationTests(unittest.TestCase):
    def test_button_navigation_uses_bounded_helper_and_syncs_checkpoint_state(self):
        self.assertIn("p3dDexNavigate(dex_index,-1)", SOURCE)
        self.assertIn("p3dDexNavigate(dex_index,1)", SOURCE)
        self.assertIn("dex_index=next;state.selected_dex=dex_index", SOURCE)

    def test_touch_navigation_uses_same_bounded_helper(self):
        self.assertIn("int next=p3dDexNavigate(dex_index,direction);", SOURCE)
        self.assertIn("dex_index=next;state.selected_dex=dex_index;", SOURCE)

if __name__ == "__main__":
    unittest.main()
