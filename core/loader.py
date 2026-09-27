from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd


MAIN_NUMBER_ALIASES = [
    ("n1", "number1", "num1", "号码1", "號碼1", "正码1", "正碼1", "开奖号码1", "開獎號碼1"),
    ("n2", "number2", "num2", "号码2", "號碼2", "正码2", "正碼2", "开奖号码2", "開獎號碼2"),
    ("n3", "number3", "num3", "号码3", "號碼3", "正码3", "正碼3", "开奖号码3", "開獎號碼3"),
    ("n4", "number4", "num4", "号码4", "號碼4", "正码4", "正碼4", "开奖号码4", "開獎號碼4"),
    ("n5", "number5", "num5", "号码5", "號碼5", "正码5", "正碼5", "开奖号码5", "開獎號碼5"),
    ("n6", "number6", "num6", "号码6", "號碼6", "正码6", "正碼6", "开奖号码6", "開獎號碼6"),
]

DRAW_NO_ALIASES = (
    "draw_no",
    "issue",
    "draw",
    "period",
    "期号",
    "期號",
    "期数",
    "期數",
    "开奖期号",
    "開獎期號",
)
DATE_ALIASES = ("draw_date", "date", "开奖日期", "開獎日期", "日期")
SPECIAL_ALIASES = (
    "special",
    "bonus",
    "extra",
    "特别号码",
    "特別號碼",
    "特别号",
    "特別號",
    "特码",
    "特碼",
)

OUTPUT_COLUMNS = ["draw_no", "draw_date", "n1", "n2", "n3", "n4", "n5", "n6", "special"]


def _normalise_label(value: Any) -> str:
    label = str(value).strip().lower()
    return re.sub(r"[\s_\-（）()]+", "", label)


def _find_column(columns: list[Any], aliases: tuple[str, ...]) -> Any | None:
    normalised = {_normalise_label(column): column for column in columns}
    for alias in aliases:
        column = normalised.get(_normalise_label(alias))
        if column is not None:
            return column
    return None


def read_draws_file(source: Any, filename: str | None = None) -> pd.DataFrame:
    """Read CSV or Excel content from an UploadedFile or file path."""
    name = filename or getattr(source, "name", "") or str(source)
    suffix = Path(name).suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        return pd.read_excel(source)
    if suffix == ".xls":
        return pd.read_excel(source)

    raw = source.getvalue() if hasattr(source, "getvalue") else Path(source).read_bytes()
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return pd.read_csv(BytesIO(raw), encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValueError(f"无法识别文件编码：{last_error}")


def normalise_draws(data: pd.DataFrame) -> pd.DataFrame:
    """Convert common Chinese or English column layouts into the internal schema."""
    if data.empty:
        raise ValueError("文件没有数据行。")

    columns = list(data.columns)
    rename_map: dict[Any, str] = {}

    draw_no_column = _find_column(columns, DRAW_NO_ALIASES)
    if draw_no_column is not None:
        rename_map[draw_no_column] = "draw_no"

    date_column = _find_column(columns, DATE_ALIASES)
    if date_column is not None:
        rename_map[date_column] = "draw_date"

    for output_column, *aliases in MAIN_NUMBER_ALIASES:
        source_column = _find_column(columns, (output_column, *aliases))
        if source_column is None:
            raise ValueError(f"缺少号码列：{output_column}。请将六个正码拆成六列。")
        rename_map[source_column] = output_column

    special_column = _find_column(columns, SPECIAL_ALIASES)
    if special_column is not None:
        rename_map[special_column] = "special"

    result = data.rename(columns=rename_map).copy()
    if "draw_no" not in result:
        result["draw_no"] = range(1, len(result) + 1)
    if "draw_date" not in result:
        result["draw_date"] = pd.NaT
    if "special" not in result:
        result["special"] = pd.NA

    result["draw_no"] = result["draw_no"].astype(str).str.strip()
    result["draw_date"] = pd.to_datetime(result["draw_date"], errors="coerce")

    number_columns = [f"n{index}" for index in range(1, 7)]
    for column in number_columns + ["special"]:
        result[column] = pd.to_numeric(result[column], errors="coerce")

    result = result.dropna(subset=number_columns).copy()
    for column in number_columns + ["special"]:
        result[column] = result[column].astype("Int64")

    valid_main = result[number_columns].apply(
        lambda row: row.between(1, 49).all() and row.nunique() == 6,
        axis=1,
    )
    result = result.loc[valid_main].copy()
    result.loc[~result["special"].between(1, 49), "special"] = pd.NA

    if result.empty:
        raise ValueError("清洗后没有有效数据。六个正码必须为 1 到 49，且每期不能重复。")

    result = result[OUTPUT_COLUMNS]
    if result["draw_date"].notna().any():
        result = result.sort_values(["draw_date", "draw_no"], na_position="last")
    result = result.drop_duplicates(subset=["draw_no"], keep="last").reset_index(drop=True)
    return result


def make_demo_draws(draw_count: int = 120) -> pd.DataFrame:
    """Create deterministic demo rows for interface checks only."""
    rows: list[dict[str, Any]] = []
    state = 20260927
    for index in range(draw_count):
        numbers: list[int] = []
        while len(numbers) < 7:
            state = (1103515245 * state + 12345) % (2**31)
            value = state % 49 + 1
            if value not in numbers:
                numbers.append(value)
        rows.append(
            {
                "draw_no": f"TEST-{index + 1:03d}",
                "draw_date": pd.Timestamp("2025-01-01") + pd.Timedelta(days=index),
                **{f"n{number_index + 1}": numbers[number_index] for number_index in range(6)},
                "special": numbers[6],
            }
        )
    return pd.DataFrame(rows)
