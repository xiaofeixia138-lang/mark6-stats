from __future__ import annotations

import unittest

from core.loader import make_demo_draws, normalise_draws
from core.strategy import StrategyConfig, backtest_strategy, prize_tier, select_numbers


class StrategyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.draws = normalise_draws(make_demo_draws(80))

    def test_prize_tier_rules(self) -> None:
        self.assertEqual(prize_tier(6, False), "头奖")
        self.assertEqual(prize_tier(5, True), "二奖")
        self.assertEqual(prize_tier(5, False), "三奖")
        self.assertEqual(prize_tier(3, True), "六奖")
        self.assertEqual(prize_tier(2, True), "未中奖")

    def test_selects_six_unique_numbers(self) -> None:
        picks = select_numbers(self.draws, StrategyConfig(history_window=30), count=6)
        self.assertEqual(len(picks), 6)
        self.assertEqual(len(set(picks)), 6)

    def test_backtest_uses_requested_draw_count(self) -> None:
        results = backtest_strategy(
            self.draws,
            StrategyConfig(history_window=30, backtest_draws=18),
        )
        self.assertEqual(len(results), 18)


if __name__ == "__main__":
    unittest.main()

