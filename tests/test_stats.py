from __future__ import annotations

import unittest

from core.loader import make_demo_draws, normalise_draws
from core.stats import color_for_number, number_frequency, number_omission


class StatsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.draws = normalise_draws(make_demo_draws(20))

    def test_color_mapping_covers_all_numbers(self) -> None:
        colors = [color_for_number(number) for number in range(1, 50)]
        self.assertEqual(set(colors), {"红波", "蓝波", "绿波"})

    def test_frequency_total_matches_draw_count(self) -> None:
        frequency = number_frequency(self.draws, include_special=True)
        self.assertEqual(int(frequency["frequency"].sum()), 20 * 7)

    def test_latest_number_has_zero_omission(self) -> None:
        omission = number_omission(self.draws, include_special=True).set_index("number")
        latest = self.draws.iloc[-1]
        self.assertEqual(int(omission.loc[int(latest["n1"]), "omission"]), 0)


if __name__ == "__main__":
    unittest.main()

