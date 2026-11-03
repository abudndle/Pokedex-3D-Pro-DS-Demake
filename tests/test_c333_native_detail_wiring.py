"""C333 structural regression: optional metadata must render on touchscreen."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class NativeDetailViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(ROOT/'source/main.c').read_text()
        cls.render=cls.source.split('static void render(void) {',1)[1].split('int main(void)',1)[0]

    def test_detail_text_is_only_on_bottom_screen(self):
        render=self.render
        top=render.index('consoleSelect(&top_console)')
        bottom=render.index('consoleSelect(&bottom_console)')
        details=render.index('Original detail unavailable')
        self.assertLess(top,bottom)
        self.assertLess(bottom,details)
        self.assertNotIn('Original detail unavailable',render[top:bottom])
        self.assertIn('p3dSpeciesDetailTabName',render[bottom:details])

    def test_original_bitmap_not_used_for_unverified_detail_hitboxes(self):
        self.assertIn('!(page==P3D_PAGE_DEX && dex_detail_tab)',self.source)
        self.assertIn('point.py>=160 && point.py<176',self.source)
        self.assertIn('point.py>=176',self.source)

    def test_state_tracks_form_specific_data_and_reloads(self):
        self.assertIn('p3dSpeciesDetailPath(details_path,dex_index,selected_form)',self.source)
        self.assertIn('p3dSpeciesDetailsLoad(',self.source)
        self.assertIn('view.dex_detail_tab=(uint8_t)',self.source)
        self.assertIn('dex_detail_tab=(int)resume.dex_detail_tab',self.source)

    def test_missing_private_record_must_not_fake_nintendo_stats(self):
        self.assertIn('if(!dex_details_ready)',self.render)
        self.assertIn('Original detail unavailable',self.render)
        self.assertIn('Original stats unavailable',self.render)
        self.assertIn('Original learnset unavailable',self.render)

if __name__=='__main__':unittest.main()
