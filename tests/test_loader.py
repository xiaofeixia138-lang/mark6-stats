from __future__ import annotations

import unittest

import pandas as pd

from core.loader import normalise_draws


class LoaderTests(unittest.TestCase):
    def test_normalises_chinese_columns(self) -> None:
        source = pd.DataFrame(
            [
                {
                    "期号": "2026-001",
                    "开奖日期": "2026-01-01",
                    "号码1": 1,
                    "号码2": 2,
                    "号码3": 3,
                    "号码4": 4,
                    "号码5": 5,
                    "号码6": 6,
                    "特别号码": 7,
                }
            ]
        )

        result = normalise_draws(source)

        self.assertEqual(list(result.columns), ["draw_no", "draw_date", "n1", "n2", "n3", "n4", "n5", "n6", "special"])
        self.assertEqual(result.iloc[0]["draw_no"], "2026-001")
        self.assertEqual(result.iloc[0]["special"], 7)

    def test_rejects_duplicate_main_numbers(self) -> None:
        source = pd.DataFrame(
            [
                {
                    "draw_no": "A1",
                    "n1": 1,
                    "n2": 1,
                    "n3": 3,
                    "n4": 4,
                    "n5": 5,
                    "n6": 6,
                }
            ]
        )

        with self.assertRaisesRegex(ValueError, "清洗后没有有效数据"):
            normalise_draws(source)


if __name__ == "__main__":
    unittest.main()

