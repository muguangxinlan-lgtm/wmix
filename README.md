# 电商数据看板

说明：仓库现已同时纳入 `v2`、`v3`、填表工具和导入脚本；SQLite 数据库仍保留在仓库外或本地 `data/` 目录，不直接提交到 Git。

## 整体架构

```
┌─────────────┐      ┌──────────────┐      ┌────────────────┐
│  填表工具     │      │   SQLite     │      │   看板视图      │
│  (录入数据)   │ ──→  │   数据库     │  ──→ │  (可视化展示)    │
└─────────────┘      └──────────────┘      └────────────────┘
data_entry.html      .sqlite 文件          dashboard_v3.html
       ↓                   ↑                 或任何 build 输出
  week_日期.json           │
       ↓                   │
  import_week.py ──────────┘
```

三者完全解耦。改看板不影响填表，改填表不影响看板，唯一交集是 SQLite 数据库。

## 每周更新流程

```bash
# 方式 A：浏览器打开填表工具，填写新一周数据，点「导出 JSON」
open /Users/wmix/wmixclaude/data_entry.html

# 把导出的 JSON 写入数据库
python3 /Users/wmix/wmixclaude/import_week.py ~/Downloads/week_2026-03-16.json

# 方式 B：直接从周度 Excel 提取最新一周 JSON
python3 /Users/wmix/wmixclaude/xlsx_to_week_json.py ~/Downloads/店铺每周数据汇总0323.xlsx

# 再把生成的 JSON 写入数据库（会自动先备份数据库）
python3 /Users/wmix/wmixclaude/import_week.py ~/Downloads/week_2026-03-16.json

# 最后用任意脚本生成看板
python3 /Users/wmix/wmixclaude/build_v3.py
```

当前数据库已更新到 `2026-03-16 ~ 2026-03-22`，共 `61` 周、`3940` 条 `structured_data`、`279` 条 `platform_weekly_summary`。

## 文件清单

### 数据录入（跟数据库打交道，不绑定任何看板）

| 文件 | 说明 |
|------|------|
| `build_form.py` | 生成填表工具的脚本。读 SQLite 取上周参考值，输出 `data_entry.html` |
| `data_entry.html` | 填表工具页面。浏览器打开，填数据，导出 JSON |
| `xlsx_to_week_json.py` | 从 `店铺每周数据汇总*.xlsx` 中提取最新未导入的一周，输出周 JSON |
| `import_week.py` | 把填表工具导出的 JSON 写入 SQLite。自动备份，有重复检测 |

### 看板视图（只读数据库，跟填表无关）

| 文件 | 说明 |
|------|------|
| `build_v3.py` | v3 看板生成脚本。读 SQLite → 输出 `dashboard_v3.html` |
| `dashboard_v3.html` | v3 看板。ECharts · 明亮单页滚动 · 8个区域 |
| `build_v2.py` | v2 看板生成脚本。读 SQLite → 输出 `index.html` |
| `index.html` | v2 看板。Chart.js · 暗色5Tab页 · GitHub Pages 线上版 |

### 数据库

| 文件 | 说明 |
|------|------|
| `data/店铺每周数据汇总.sqlite` 或 `~/Downloads/店铺每周数据汇总_2026-03-18.sqlite` | 本地 SQLite 数据源，不提交到 Git |

三张表：
- `structured_data` — 全量指标明细（每条 = 某平台某周某指标的数值，标记手工/公式）
- `platform_weekly_summary` — 平台周汇总（总成交/退款/净成交/自营/合作/付费/支出）
- `notes` — 数据说明备注

### 发布

| 文件 | 说明 |
|------|------|
| `publish_github_pages.sh` | 一键生成 v2 + 推送 GitHub Pages |

- 仓库：`https://github.com/muguangxinlan-lgtm/wmix`
- 站点：`https://muguangxinlan-lgtm.github.io/wmix/`

## 填表工具说明

只需填手工数据，公式字段灰色显示、自动计算：

| 平台 | 手填 | 自动算 |
|------|------|--------|
| 小红书 | 13项（总成交、退款、付费成交/消耗、店播3项、渠道6项） | 净成交、付费投产、店播投产、自然流 |
| 抖店 | ~20项（总成交、退款、7个账号成交+投产、支出、渠道6项） | 净成交、各账号消耗、付费合计、自营付费/自然流 |
| 淘宝 | ~10项（总成交、退款、各付费计划成交/消耗、达播、淘客支出） | 净成交、各计划投产、渠道分拆、费用汇总 |
| 微信/B站/天猫 | 各4项（总成交、退款、自营、合作） | 净成交 |

填表工具特性：
- 每个输入框下方显示上周参考值
- 输入实时自动保存到浏览器 localStorage
- 「复制上周数据」按钮可一键填入上周值
- 导出的 JSON 包含 `structured_data` 和 `platform_weekly_summary` 两张表的完整行

## 重新生成工具本身

如果数据库结构变化（比如新增平台或字段），需要重新生成填表工具：

```bash
python3 /Users/wmix/wmixclaude/build_form.py    # 重新生成 data_entry.html
```

这只是重新生成填表页面，不影响看板。

## 遗留文件

| 文件 | 说明 |
|------|------|
| `build_dashboard.py` | v1 生成脚本，保留参考 |
| `dashboard.html` | v1 输出 |
| `serve_dashboard.py` | 本地 Mac 服务器方案（已弃用） |
| `launch_dashboard_server.sh` | 本地服务启动脚本（已弃用） |

## 数据库放置约定

- 推荐把数据库放到仓库外，例如 `~/Downloads/店铺每周数据汇总_2026-03-18.sqlite`
- 也可以放到仓库内的 `data/店铺每周数据汇总.sqlite` 供本机脚本使用
- `data/`、`*.sqlite`、备份文件和导出的周 JSON 已加入 `.gitignore`
- `import_week.py` 每次导入前都会自动生成一个 `*.bak_YYYYMMDD_HHMMSS` 数据库备份
- `build_v3.py`、`build_form.py`、`import_week.py`、`xlsx_to_week_json.py` 都支持环境变量 `WMIX_DB_PATH`
