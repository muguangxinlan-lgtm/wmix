# 项目交接与当前进度

## 项目是什么

离线电商数据看板项目。本地 Python 脚本读取 SQLite → 生成静态 HTML → 通过 GitHub Pages 发布。

当前仓库已经纳入 `v2`、`v3`、填表工具和导入脚本；数据库文件仍保持本地存放，不提交到 Git。

## 当前状态（2026-03-23）

### 线上版（v2）
- Git 仓库已连接：`muguangxinlan-lgtm/wmix`
- GitHub Pages 从 `main` 分支 `/ (root)` 发布
- 发布文件：`index.html`（由 `build_v2.py` 生成，Chart.js + 暗色5Tab页）
- 站点：`https://muguangxinlan-lgtm.github.io/wmix/`

### 本地版（v3）
- `build_v3.py` → `dashboard_v3.html`：全新设计，ECharts + 明亮单页滚动
- `build_form.py` → `data_entry.html`：填表工具，填完新一周数据后一键生成新看板
- v3 尚未发布到 GitHub Pages

### 两套版本的关系

v2 和 v3 完全独立，各自读同一个 SQLite 数据库，互不影响。
v3 填表工具内嵌了 `dashboard_v3.html` 模板，改看板后需重新跑 `build_form.py`。

## 文件地图

```
/Users/wmix/wmixclaude/         ← Git 仓库（GitHub Pages）
├── build_v2.py                ← v2 生成脚本
├── index.html                 ← v2 输出（线上发布）
├── build_v3.py                ← v3 看板生成脚本
├── dashboard_v3.html          ← v3 看板输出
├── build_form.py              ← 填表工具生成脚本
├── data_entry.html            ← 填表工具输出
├── import_week.py             ← JSON 导入 SQLite
├── publish_github_pages.sh
├── README.md
└── HANDOFF.md

本地数据库：
- `data/店铺每周数据汇总.sqlite`，或
- `~/Downloads/店铺每周数据汇总_2026-03-18.sqlite`
```

## 每周更新方式

### 用填表工具（推荐）
1. 浏览器打开 `/Users/wmix/wmixclaude/data_entry.html`
2. 填新一周数据 → 公式自动算 → 点"生成看板" → 下载新 HTML

### 用周度 Excel 直接更新
1. 准备最新的 `店铺每周数据汇总*.xlsx`
2. 运行：
```bash
python3 /Users/wmix/wmixclaude/xlsx_to_week_json.py ~/Downloads/店铺每周数据汇总0323.xlsx
python3 /Users/wmix/wmixclaude/import_week.py ~/Downloads/week_2026-03-16.json
python3 /Users/wmix/wmixclaude/build_v3.py
```
3. `import_week.py` 会在导入前自动备份旧数据库

### 用命令行
```bash
# 更新 v3 看板（需要先更新 SQLite 数据库）
python3 /Users/wmix/wmixclaude/build_v3.py

# 更新 v2 线上版
cd /Users/wmix/wmixclaude
python3 build_v2.py
./publish_github_pages.sh
```

## 数据库说明

`店铺每周数据汇总.sqlite`（或 Downloads 下同名快照）：
- 61周（2025-02-15 ~ 2026-03-16），6平台，3940条记录
- `structured_data` 表：每条记录 = 某平台某周某指标的数值
- `platform_weekly_summary` 表：平台周汇总（总成交/退款/净成交/自营/合作/付费/支出）
- `notes` 表：数据说明
- 字段 `是否公式` 标记了哪些是手工录入、哪些是公式计算

最近一次导入：
- 源文件：`~/Downloads/店铺每周数据汇总0323.xlsx`
- 新增周：`2026-03-16 ~ 2026-03-22`
- 备份：`~/Downloads/店铺每周数据汇总_2026-03-18.sqlite.bak_20260323_145839`

## 下一个维护者先看什么

1. `README.md` — 整体说明
2. `HANDOFF.md`（本文件）— 当前状态
3. `build_v3.py` — 最新看板脚本
4. `build_form.py` — 填表工具脚本
5. `import_week.py` — 周数据导入脚本
