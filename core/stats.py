from __future__ import annotations

from collections import Counter

import pandas as pd


RED_NUMBERS = {1, 2, 7, 8, 12, 13, 18, 19, 23, 24, 29, 30, 34, 35, 40, 45, 46}
BLUE_NUMBERS = {3, 4, 9, 10, 14, 15, 20, 25, 26, 31, 36, 37, 41, 42, 47, 48}
GREEN_NUMBERS = {5, 6, 11, 16, 17, 21, 22, 27, 28, 32, 33, 38, 39, 43, 44, 49}

COLOR_ORDER = ["红波", "蓝波", "绿波"]
NUMBER_COLORS = {"红波": "#C43B3B", "蓝波": "#3157A4", "绿波": "#2F7D5A"}


def _window(draws: pd.DataFrame, window: int | None) -> pd.DataFrame:
    if window is None or window <= 0 or window >= len(draws):
        return draws
    return draws.tail(window)


def color_for_number(number: int) -> str:
    if number in RED_NUMBERS:
        return "红波"
    if number in BLUE_NUMBERS:
        return "蓝波"
    if number in GREEN_NUMBERS:
        return "绿波"
    raise ValueError(f"无效号码：{number}")


def draw_numbers(draws: pd.DataFrame, include_special: bool = True) -> pd.Series:
    columns = [f"n{index}" for index in range(1, 7)]
    values: list[int] = []
    for row in draws[columns].itertuples(index=False, name=None):
        values.extend(int(number) for number in row if pd.notna(number))
    if include_special and "special" in draws:
        values.extend(int(number) for number in draws["special"].dropna())
    return pd.Series(values, dtype="int64")


def number_frequency(
    draws: pd.DataFrame,
    include_special: bool = True,
    window: int | None = None,
) -> pd.DataFrame:
    selected = _window(draws, window)
    counts = Counter(draw_numbers(selected, include_special=include_special).tolist())
    total = sum(counts.values())
    return pd.DataFrame(
        {
            "number": range(1, 50),
            "frequency": [counts.get(number, 0) for number in range(1, 50)],
        }
    ).assign(
        percentage=lambda frame: frame["frequency"] / total * 100 if total else 0.0,
        color=lambda frame: frame["number"].map(color_for_number),
    )


def number_omission(
    draws: pd.DataFrame,
    include_special: bool = True,
    window: int | None = None,
) -> pd.DataFrame:
    selected = _window(draws, window).reset_index(drop=True)
    last_seen: dict[int, int] = {}
    for row_index, row in selected.iterrows():
        values = [int(row[f"n{index}"]) for index in range(1, 7)]
        if include_special and pd.notna(row["special"]):
            values.append(int(row["special"]))
        for number in set(values):
            last_seen[number] = row_index

    draw_count = len(selected)
    return pd.DataFrame(
        {
            "number": range(1, 50),
            "omission": [
                draw_count if number not in last_seen else draw_count - 1 - last_seen[number]
                for number in range(1, 50)
            ],
        }
    ).assign(color=lambda frame: frame["number"].map(color_for_number))


def number_summary(
    draws: pd.DataFrame,
    include_special: bool = True,
    window: int | None = None,
) -> pd.DataFrame:
    frequency = number_frequency(draws, include_special, window)
    omission = number_omission(draws, include_special, window)
    return frequency.merge(omission[["number", "omission"]], on="number", how="left")


def color_summary(draws: pd.DataFrame, include_special: bool = True, window: int | None = None) -> pd.DataFrame:
    selected = _window(draws, window)
    numbers = draw_numbers(selected, include_special=include_special)
    counts = numbers.map(color_for_number).value_counts()
    total = int(counts.sum())
    return pd.DataFrame(
        {
            "color": COLOR_ORDER,
            "frequency": [int(counts.get(color, 0)) for color in COLOR_ORDER],
        }
    ).assign(percentage=lambda frame: frame["frequency"] / total * 100 if total else 0.0)


def tail_summary(draws: pd.DataFrame, include_special: bool = True, window: int | None = None) -> pd.DataFrame:
    selected = _window(draws, window)
    numbers = draw_numbers(selected, include_special=include_special)
    counts = numbers.mod(10).value_counts()
    total = int(counts.sum())
    return pd.DataFrame(
        {
            "tail": [str(number) for number in range(10)],
            "frequency": [int(counts.get(number, 0)) for number in range(10)],
        }
    ).assign(percentage=lambda frame: frame["frequency"] / total * 100 if total else 0.0)


def main_sum_series(draws: pd.DataFrame, window: int | None = None) -> pd.DataFrame:
    selected = _window(draws, window).copy()
    selected["主号和值"] = selected[[f"n{index}" for index in range(1, 7)]].sum(axis=1)
    return selected[["draw_no", "draw_date", "主号和值"]]

