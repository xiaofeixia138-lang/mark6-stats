from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.stats import color_for_number, number_frequency, number_omission, number_summary


@dataclass(frozen=True)
class StrategyConfig:
    history_window: int = 100
    backtest_draws: int = 100
    include_special: bool = True
    frequency_weight: float = 0.4
    omission_weight: float = 0.3
    recency_weight: float = 0.3
    excluded_colors: tuple[str, ...] = ()
    excluded_tails: tuple[int, ...] = ()


def _normalise(series: pd.Series) -> pd.Series:
    maximum = float(series.max()) if not series.empty else 0.0
    if maximum <= 0:
        return series.astype(float)
    return series.astype(float) / maximum


def score_numbers(draws: pd.DataFrame, config: StrategyConfig) -> pd.DataFrame:
    if draws.empty:
        raise ValueError("没有可用于选号的数据。")

    history = draws.tail(config.history_window).reset_index(drop=True)
    frequency = number_frequency(history, config.include_special, window=None).set_index("number")
    omission = number_omission(history, config.include_special, window=None).set_index("number")

    recency_counts: dict[int, float] = {number: 0.0 for number in range(1, 50)}
    draw_count = len(history)
    for row_index, row in history.iterrows():
        values = [int(row[f"n{index}"]) for index in range(1, 7)]
        if config.include_special and pd.notna(row["special"]):
            values.append(int(row["special"]))
        age = draw_count - 1 - row_index
        weight = 0.94**age
        for number in set(values):
            recency_counts[number] += weight

    scored = pd.DataFrame(
        {
            "number": range(1, 50),
            "frequency": [frequency.loc[number, "frequency"] for number in range(1, 50)],
            "omission": [omission.loc[number, "omission"] for number in range(1, 50)],
            "recency": [recency_counts[number] for number in range(1, 50)],
        }
    )
    scored["frequency_score"] = _normalise(scored["frequency"])
    scored["omission_score"] = _normalise(scored["omission"])
    scored["recency_score"] = _normalise(scored["recency"])
    scored["score"] = (
        scored["frequency_score"] * config.frequency_weight
        + scored["omission_score"] * config.omission_weight
        + scored["recency_score"] * config.recency_weight
    )
    scored["color"] = scored["number"].map(color_for_number)
    scored["tail"] = scored["number"].mod(10)
    scored = scored.loc[
        ~scored["color"].isin(config.excluded_colors) & ~scored["tail"].isin(config.excluded_tails)
    ].copy()
    return scored.sort_values(["score", "number"], ascending=[False, True]).reset_index(drop=True)


def select_numbers(draws: pd.DataFrame, config: StrategyConfig, count: int = 6) -> list[int]:
    scored = score_numbers(draws, config)
    if len(scored) < count:
        raise ValueError(f"排除条件后只剩 {len(scored)} 个号码，无法选择 {count} 个。")
    return scored.head(count)["number"].astype(int).tolist()


def prize_tier(main_hits: int, hit_special: bool) -> str:
    if main_hits == 6:
        return "头奖"
    if main_hits == 5 and hit_special:
        return "二奖"
    if main_hits == 5:
        return "三奖"
    if main_hits == 4 and hit_special:
        return "四奖"
    if main_hits == 4:
        return "五奖"
    if main_hits == 3 and hit_special:
        return "六奖"
    if main_hits == 3:
        return "七奖"
    return "未中奖"


def backtest_strategy(draws: pd.DataFrame, config: StrategyConfig) -> pd.DataFrame:
    if len(draws) <= config.history_window:
        raise ValueError("历史数据不足，至少要比统计窗口多一期。")

    start_index = max(config.history_window, len(draws) - config.backtest_draws)
    records: list[dict[str, object]] = []
    for target_index in range(start_index, len(draws)):
        history = draws.iloc[target_index - config.history_window : target_index]
        picks = select_numbers(history, config, count=6)
        target = draws.iloc[target_index]
        main_numbers = {int(target[f"n{index}"]) for index in range(1, 7)}
        special = int(target["special"]) if pd.notna(target["special"]) else None
        main_hits = len(main_numbers.intersection(picks))
        hit_special = special in picks if special is not None else False
        records.append(
            {
                "draw_no": target["draw_no"],
                "draw_date": target["draw_date"],
                "picks": " ".join(f"{number:02d}" for number in sorted(picks)),
                "main_hits": main_hits,
                "hit_special": hit_special,
                "prize_tier": prize_tier(main_hits, hit_special),
            }
        )
    return pd.DataFrame(records)


def backtest_summary(results: pd.DataFrame) -> dict[str, float | int]:
    if results.empty:
        return {
            "draw_count": 0,
            "average_hits": 0.0,
            "three_plus_rate": 0.0,
            "winning_tickets": 0,
        }
    return {
        "draw_count": len(results),
        "average_hits": float(results["main_hits"].mean()),
        "three_plus_rate": float((results["main_hits"] >= 3).mean() * 100),
        "winning_tickets": int((results["prize_tier"] != "未中奖").sum()),
    }


def latest_recommendation(draws: pd.DataFrame, config: StrategyConfig) -> pd.DataFrame:
    selected = score_numbers(draws, config).head(6).copy()
    selected["rank"] = range(1, len(selected) + 1)
    return selected[["rank", "number", "color", "score", "frequency", "omission", "recency"]]

