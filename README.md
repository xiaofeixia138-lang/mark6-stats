# 香港六合彩统计

Streamlit V1，用于上传开奖数据、查看统计并调整策略参数。

线上应用：https://mark6-stats-xiaofeixia.streamlit.app

## 数据格式

支持 CSV、XLSX 和 XLSM。六个正码必须拆成六列。列名可使用以下任一形式：

| 内部字段 | 可用列名 |
|---|---|
| 期号 | `draw_no`、`issue`、`期号`、`开奖期号` |
| 日期 | `draw_date`、`date`、`开奖日期` |
| 正码 | `n1` 到 `n6`、`号码1` 到 `号码6`、`正码1` 到 `正码6` |
| 特别号码 | `special`、`bonus`、`特别号码`、`特码` |

期号和日期可以缺失。特别号码可以缺失，但相关统计和命中判断会受影响。

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m streamlit run app.py
```

## 测试

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

## 部署说明

Streamlit Community Cloud 不保证本地文件持久化，因此 V1 不写入 SQLite。上传的数据在当前浏览器会话中有效。长期历史数据可以在以后接入 Supabase/PostgreSQL。

在 Streamlit Community Cloud 中：

1. 使用 GitHub 登录。
2. 选择本仓库。
3. 主文件选择 `app.py`。
4. 部署后使用生成的 `*.streamlit.app` 地址。

回测只使用目标期之前的数据，不构成收益预测，也未计算投注成本和奖金分配。
