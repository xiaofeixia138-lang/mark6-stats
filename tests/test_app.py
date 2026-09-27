from __future__ import annotations

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class AppSmokeTests(unittest.TestCase):
    def test_app_starts_and_loads_demo_data(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path)).run(timeout=20)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.tabs), 3)

        app.button[0].click().run(timeout=20)

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any(metric.label == "已载入期数" and metric.value == "120" for metric in app.metric))


if __name__ == "__main__":
    unittest.main()
