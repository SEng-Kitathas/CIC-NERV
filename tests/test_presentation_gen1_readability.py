import re
import unittest

from personal_cic.presentation.pages import SYSTEMS_HTML, WORLD_HTML
from personal_cic.presentation.traffic_page import TRAFFIC_HTML


class PresentationGen1ReadabilityTests(unittest.TestCase):
    def _style(self, html: str) -> str:
        return html.split('<style>', 1)[1].split('</style>', 1)[0]

    def test_all_primary_pages_have_gen1_readability_tokens(self):
        for name, html in (
            ('systems', SYSTEMS_HTML),
            ('world', WORLD_HTML),
            ('traffic', TRAFFIC_HTML),
        ):
            with self.subTest(page=name):
                compact = self._style(html).replace(' ', '')
                self.assertIn('--ui-generation:1', compact)
                self.assertIn('--fs-xs:12px', compact)
                self.assertIn('--fs-md:15px', compact)
                self.assertIn('--fs-xl:22px', compact)

    def test_primary_page_css_has_no_8_to_11_px_text_literals(self):
        tiny = re.compile(r'font-size\s*:\s*(?:8|9|10|11)px\b')
        for name, html in (
            ('systems', SYSTEMS_HTML),
            ('world', WORLD_HTML),
            ('traffic', TRAFFIC_HTML),
        ):
            with self.subTest(page=name):
                self.assertIsNone(tiny.search(self._style(html)))

    def test_navigation_surface_is_consistent(self):
        expected = (
            'SYSTEMS', 'WORLD', 'TRAFFIC',
            'HOUSE', 'SENSORS', 'SYSTEM / AI',
        )
        for name, html in (
            ('systems', SYSTEMS_HTML),
            ('world', WORLD_HTML),
            ('traffic', TRAFFIC_HTML),
        ):
            with self.subTest(page=name):
                for label in expected:
                    self.assertIn(label, html)

    def test_traffic_side_column_and_dense_rows_get_readability_space(self):
        css = self._style(TRAFFIC_HTML)
        self.assertIn('minmax(360px,.9fr)', css)
        self.assertIn('.event-row{font-size:var(--fs-xs)', css)
        self.assertIn('.event-row .headline{font-size:var(--fs-sm)', css)
        self.assertIn('.source-sub{font-size:var(--fs-xs)', css)
        self.assertIn('.intel-note{', css)
        self.assertIn('font-size:var(--fs-xs)', css)

    def test_keyboard_focus_is_visibly_preserved(self):
        for name, html in (
            ('systems', SYSTEMS_HTML),
            ('world', WORLD_HTML),
            ('traffic', TRAFFIC_HTML),
        ):
            with self.subTest(page=name):
                self.assertIn('focus-visible', self._style(html))

    def test_visual_pass_does_not_change_projection_endpoints(self):
        self.assertIn('fetch("/api/v1/systems"', SYSTEMS_HTML)
        self.assertIn("fetch('/api/v1/world'", WORLD_HTML)
        self.assertIn("fetch('/api/v1/traffic'", TRAFFIC_HTML)

    def test_traffic_future_navigation_is_present_but_non_operational(self):
        self.assertIn('<span class="future">HOUSE</span>', TRAFFIC_HTML)
        self.assertIn('<span class="future">SENSORS</span>', TRAFFIC_HTML)
        self.assertIn('<span class="future">SYSTEM / AI</span>', TRAFFIC_HTML)


if __name__ == '__main__':
    unittest.main()
