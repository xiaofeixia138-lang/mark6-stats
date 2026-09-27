from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from core.loader import make_demo_draws, normalise_draws, read_draws_file
from core.stats import (
    COLOR_ORDER,
    NUMBER_COLORS,
    color_summary,
    main_sum_series,
    number_frequency,
    number_omission,
    number_summary,
    tail_summary,
)
from core.strategy import (
    StrategyConfig,
    backtest_strategy,
    backtest_summary,
    latest_recommendation,
)


st.set_page_config(
    page_title="香港六合彩统计",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1180px; padding-top: 1.2rem; padding-bottom: 3rem;}
    [data-testid="stMetricValue"] {font-size: 1.35rem;}
    .number-row {display: flex; flex-wrap: wrap; gap: .45rem; margin: .5rem 0 1rem;}
    .ball {
        width: 2.35rem; height: 2.35rem; border-radius: 50%;
        display: inline-flex; align-items: center; justify-content: center;
        color: white; font-weight: 700; font-size: .95rem;
        box-shadow: inset 0 -2px 0 rgba(0,0,0,.12);
    }
    .ball-red {background: #C43B3B;}
    .ball-blue {background: #3157A4;}
    .ball-green {background: #2F7D5A;}
    .ball-special {outline: 3px solid #F2C94C; outline-offset: 2px;}
    .small-note {color: #667085; font-size: .86rem;}
    @media (max-width: 640px) {
        .block-container {padding-left: .85rem; padding-right: .85rem;}
        h1 {font-size: 1.65rem !important;}
        .ball {width: 2.1rem; height: 2.1rem; font-size: .86rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


WINDOW_OPTIONS = {
    "最近30期": 30,
    "最近50期": 50,
    "最近100期": 100,
    "最近200期": 200,
    "全部数据": None,
}


def ball_class(number: int, special: bool = False) -> str:
    if number in {1, 2, 7, 8, 12, 13, 18, 19, 23, 24, 29, 30, 34, 35, 40, 45, 46}:
        color_class = "ball-red"
    elif number in {3, 4, 9, 10, 14, 15, 20, 25, 26, 31, 36, 37, 41, 42, 47, 48}:
        color_class = "ball-blue"
    else:
        color_class = "ball-green"
    return f"ball {color_class}{' ball-special' if special else ''}"


def render_balls(numbers: list[int], special: int | None = None) -> None:
    balls = "".join(f'<span class="{ball_class(number)}">{number:02d}</span>' for number in numbers)
    if special is not None:
        balls += f'<span class="{ball_class(special, special=True)}">{special:02d}</span>'
    st.markdown(f'<div class="number-row">{balls}</div>', unsafe_allow_html=True)


def current_draws() -> pd.DataFrame:
    return st.session_state.get("draws", pd.DataFrame())


def show_data_required() -> None:
    st.info("请先在“数据”页上传开奖文件，或载入演示数据。")


@st.cache_data(show_spinner=False)
def cached_number_summary(draws: pd.DataFrame, include_special: bool, window: int | None) -> pd.DataFrame:
    return number_summary(draws, include_special, window)


@st.cache_data(show_spinner=False)
def cached_frequency(draws: pd.DataFrame, include_special: bool, window: int | None) -> pd.DataFrame:
    return number_frequency(draws, include_special, window)


@st.cache_data(show_spinner=False)
def cached_omission(draws: pd.DataFrame, include_special: bool, window: int | None) -> pd.DataFrame:
    return number_omission(draws, include_special, window)


@st.cache_data(show_spinner=False)
def cached_color_summary(draws: pd.DataFrame, include_special: bool, window: int | None) -> pd.DataFrame:
    return color_summary(draws, include_special, window)


@st.cache_data(show_spinner=False)
def cached_tail_summary(draws: pd.DataFrame, include_special: bool, window: int | None) -> pd.DataFrame:
    return tail_summary(draws, include_special, window)


@st.cache_data(show_spinner=False)
def cached_sum_series(draws: pd.DataFrame, window: int | None) -> pd.DataFrame:
    return main_sum_series(draws, window)


@st.cache_data(show_spinner=False)
def cached_recommendation(draws: pd.DataFrame, config: StrategyConfig) -> pd.DataFrame:
    return latest_recommendation(draws, config)


@st.cache_data(show_spinner=False)
def cached_backtest(draws: pd.DataFrame, config: StrategyConfig) -> pd.DataFrame:
    return backtest_strategy(draws, config)


st.title("香港六合彩统计")
st.caption("开奖统计、策略参数调整与历史回测")

data_tab, stats_tab, strategy_tab = st.tabs(["数据", "统计", "策略回测"])

with data_tab:
    uploaded_file = st.file_uploader("上传开奖数据", type=["csv", "xlsx", "xlsm"])
    file_signature = None
    if uploaded_file is not None:
        file_signature = f"{uploaded_file.name}:{uploaded_file.size}"

    if uploaded_file is not None and st.session_state.get("file_signature") != file_signature:
        try:
            raw_data = read_draws_file(uploaded_file, uploaded_file.name)
            st.session_state.draws = normalise_draws(raw_data)
            st.session_state.file_signature = file_signature
            st.success(f"已载入 {len(st.session_state.draws)} 期开奖数据。")
        except Exception as exc:
            st.error(str(exc))

    demo_col, clear_col = st.columns(2)
    with demo_col:
        if st.button("载入演示数据", width="stretch"):
            st.session_state.draws = normalise_draws(make_demo_draws())
            st.session_state.file_signature = None
            st.rerun()
    with clear_col:
        if st.button("清空当前数据", width="stretch"):
            st.session_state.draws = pd.DataFrame()
            st.session_state.file_signature = None
            st.rerun()

    draws = current_draws()
    if draws.empty:
        st.info("支持中英文列名，需要六个正码列；特别号码、期号和日期可选。")
    else:
        latest = draws.iloc[-1]
        metric_columns = st.columns(3)
        metric_columns[0].metric("已载入期数", f"{len(draws):,}")
        metric_columns[1].metric("最新期号", str(latest["draw_no"]))
        date_label = latest["draw_date"].strftime("%Y-%m-%d") if pd.notna(latest["draw_date"]) else "未提供"
        metric_columns[2].metric("最新日期", date_label)

        st.subheader("最新一期")
        main_numbers = [int(latest[f"n{index}"]) for index in range(1, 7)]
        special = int(latest["special"]) if pd.notna(latest["special"]) else None
        render_balls(main_numbers, special)

        display_columns = ["draw_no", "draw_date", "n1", "n2", "n3", "n4", "n5", "n6", "special"]
        st.dataframe(
            draws[display_columns].sort_values("draw_date", ascending=False, na_position="last").head(100),
            hide_index=True,
            width="stretch",
        )

with stats_tab:
    draws = current_draws()
    if draws.empty:
        show_data_required()
    else:
        control_left, control_right = st.columns([2, 1])
        with control_left:
            selected_window_label = st.radio(
                "统计范围",
                options=list(WINDOW_OPTIONS),
                index=1,
                horizontal=True,
            )
        with control_right:
            include_special = st.checkbox("特别号码计入统计", value=True)

        window = WINDOW_OPTIONS[selected_window_label]
        summary = cached_number_summary(draws, include_special, window)
        frequency = cached_frequency(draws, include_special, window)
        omission = cached_omission(draws, include_special, window)

        statistic_type = st.radio(
            "统计类型",
            options=["号码频率", "遗漏", "波色", "尾数", "和值"],
            horizontal=True,
        )

        if statistic_type == "号码频率":
            chart = px.bar(
                frequency,
                x="number",
                y="frequency",
                color="color",
                color_discrete_map=NUMBER_COLORS,
                labels={"number": "号码", "frequency": "出现次数", "color": "波色"},
            )
            chart.update_xaxes(dtick=1)
            chart.update_layout(height=430, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(chart, width="stretch")
            st.dataframe(
                frequency.sort_values("frequency", ascending=False).head(15),
                hide_index=True,
                width="stretch",
            )
        elif statistic_type == "遗漏":
            top_omission = omission.sort_values(["omission", "number"], ascending=[False, True]).head(15)
            chart = px.bar(
                top_omission,
                x="number",
                y="omission",
                color="color",
                color_discrete_map=NUMBER_COLORS,
                labels={"number": "号码", "omission": "遗漏期数", "color": "波色"},
            )
            chart.update_xaxes(dtick=1)
            chart.update_layout(height=430, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(chart, width="stretch")
            st.dataframe(top_omission, hide_index=True, width="stretch")
        elif statistic_type == "波色":
            color_data = cached_color_summary(draws, include_special, window)
            chart = px.bar(
                color_data,
                x="color",
                y="frequency",
                color="color",
                color_discrete_map=NUMBER_COLORS,
                labels={"color": "波色", "frequency": "出现次数"},
                text="percentage",
            )
            chart.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            chart.update_layout(height=430, showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(chart, width="stretch")
            st.dataframe(color_data, hide_index=True, width="stretch")
        elif statistic_type == "尾数":
            tail_data = cached_tail_summary(draws, include_special, window)
            chart = px.bar(
                tail_data,
                x="tail",
                y="frequency",
                labels={"tail": "尾数", "frequency": "出现次数"},
            )
            chart.update_layout(height=430, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(chart, width="stretch")
            st.dataframe(tail_data, hide_index=True, width="stretch")
        else:
            sum_data = cached_sum_series(draws, window)
            chart = px.histogram(
                sum_data,
                x="主号和值",
                nbins=30,
                labels={"主号和值": "六个正码之和"},
            )
            chart.update_layout(height=430, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(chart, width="stretch")

        st.subheader("号码总表")
        st.dataframe(summary, hide_index=True, width="stretch")

with strategy_tab:
    draws = current_draws()
    if draws.empty:
        show_data_required()
    elif len(draws) < 11:
        st.warning("至少需要 11 期数据才能进行策略回测。")
    else:
        preset = st.selectbox("策略预设", options=["均衡", "热号", "遗漏", "近期"], index=0)
        defaults = {
            "均衡": (0.4, 0.3, 0.3),
            "热号": (0.65, 0.05, 0.30),
            "遗漏": (0.10, 0.70, 0.20),
            "近期": (0.20, 0.10, 0.70),
        }[preset]

        available_windows = [value for value in (30, 50, 100, 200) if value < len(draws)]
        if not available_windows:
            available_windows = [10]
        history_window = st.select_slider(
            "历史窗口",
            options=available_windows,
            value=max(available_windows),
        )
        max_backtest = max(1, min(500, len(draws) - history_window))
        backtest_draws = st.slider(
            "回测期数",
            min_value=1,
            max_value=max_backtest,
            value=min(100, max_backtest),
        )

        frequency_weight = st.slider(
            "频率权重",
            min_value=0.0,
            max_value=1.0,
            value=defaults[0],
            step=0.05,
            key=f"{preset}_frequency_weight",
        )
        omission_weight = st.slider(
            "遗漏权重",
            min_value=0.0,
            max_value=1.0,
            value=defaults[1],
            step=0.05,
            key=f"{preset}_omission_weight",
        )
        recency_weight = st.slider(
            "近期权重",
            min_value=0.0,
            max_value=1.0,
            value=defaults[2],
            step=0.05,
            key=f"{preset}_recency_weight",
        )

        excluded_colors = st.multiselect("排除波色", options=COLOR_ORDER, default=[])
        excluded_tails = st.multiselect("排除尾数", options=list(range(10)), default=[])
        include_special = st.checkbox("特别号码参与评分与命中判断", value=True)
        total_weight = frequency_weight + omission_weight + recency_weight

        if total_weight <= 0:
            st.error("至少需要一个权重大于 0。")
        else:
            config = StrategyConfig(
                history_window=history_window,
                backtest_draws=backtest_draws,
                include_special=include_special,
                frequency_weight=frequency_weight / total_weight,
                omission_weight=omission_weight / total_weight,
                recency_weight=recency_weight / total_weight,
                excluded_colors=tuple(excluded_colors),
                excluded_tails=tuple(excluded_tails),
            )

            try:
                recommendation = cached_recommendation(draws, config)
                backtest = cached_backtest(draws, config)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.subheader("下一期候选号码")
                render_balls(recommendation["number"].astype(int).tolist())
                st.dataframe(
                    recommendation.assign(score=lambda frame: frame["score"].round(4)),
                    hide_index=True,
                    width="stretch",
                )

                summary = backtest_summary(backtest)
                metrics = st.columns(3)
                metrics[0].metric("回测期数", summary["draw_count"])
                metrics[1].metric("平均命中", f"{summary['average_hits']:.2f} 个")
                metrics[2].metric("命中3个及以上", f"{summary['three_plus_rate']:.1f}%")

                tier_order = ["头奖", "二奖", "三奖", "四奖", "五奖", "六奖", "七奖", "未中奖"]
                tier_counts = (
                    backtest["prize_tier"]
                    .value_counts()
                    .reindex(tier_order, fill_value=0)
                    .rename_axis("奖级")
                    .reset_index(name="次数")
                )
                st.dataframe(tier_counts, hide_index=True, width="stretch")
                st.dataframe(
                    backtest.sort_values("draw_date", ascending=False, na_position="last"),
                    hide_index=True,
                    width="stretch",
                )
                st.download_button(
                    "下载回测结果",
                    data=backtest.to_csv(index=False).encode("utf-8-sig"),
                    file_name="mark6_backtest.csv",
                    mime="text/csv",
                    width="stretch",
                )
                st.caption("回测只使用目标期之前的数据，不代表未来收益，也未计算奖金和投注成本。")
