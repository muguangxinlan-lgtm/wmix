#!/usr/bin/env python3
"""从 SQLite 生成电商数据分析看板 HTML"""

import sqlite3
import json
import os

DB_PATH = "/Users/wmix/Downloads/店铺每周数据汇总_2026-03-18.sqlite"
OUT_PATH = "/Users/wmix/wmixclaude/dashboard.html"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row


def query_json(sql):
    rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


# 1. 各平台每周成交趋势 (总成交)
weekly_revenue = query_json("""
    SELECT 开始日期, 平台, 一级对象, 数值
    FROM structured_data
    WHERE 指标大类='成交' AND 一级对象='总成交' AND 指标名称='成交金额'
    ORDER BY 开始日期, 平台
""")

# 2. 各平台每周净成交
weekly_net = query_json("""
    SELECT 开始日期, 平台, 数值
    FROM structured_data
    WHERE 指标大类='成交' AND 一级对象='净成交' AND 指标名称='成交金额'
    ORDER BY 开始日期, 平台
""")

# 3. 各平台每周退款
weekly_refund = query_json("""
    SELECT 开始日期, 平台, 数值
    FROM structured_data
    WHERE 指标大类='成交' AND 一级对象='退款' AND 指标名称='退款金额'
    ORDER BY 开始日期, 平台
""")

# 4. 平台汇总
platform_totals = query_json("""
    SELECT 平台,
           SUM(CASE WHEN 一级对象='总成交' THEN 数值 END) as 总成交,
           SUM(CASE WHEN 一级对象='净成交' THEN 数值 END) as 净成交,
           SUM(CASE WHEN 一级对象='退款' THEN 数值 END) as 退款金额
    FROM structured_data
    WHERE 指标大类='成交'
    GROUP BY 平台
    ORDER BY 总成交 DESC
""")

# 5. 渠道细分
channel_data = query_json("""
    SELECT 平台, 一级对象, SUM(数值) as 总计
    FROM structured_data
    WHERE 指标大类='渠道细分' AND 指标名称='成交金额'
    GROUP BY 平台, 一级对象
    ORDER BY 平台, 总计 DESC
""")

# 6. 小红书投放 ROI 趋势
xhs_roi = query_json("""
    SELECT 开始日期, 指标名称, 数值
    FROM structured_data
    WHERE 平台='小红书' AND 指标大类='投放' AND 一级对象='付费'
      AND 指标名称 IN ('成交金额','消耗金额','投产')
    ORDER BY 开始日期
""")

# 7. 抖店付费明细汇总
douyin_paid = query_json("""
    SELECT 一级对象, 指标名称, SUM(数值) as 总计
    FROM structured_data
    WHERE 平台='抖店' AND 指标大类='付费'
      AND 一级对象 NOT IN ('付费成交合计','支出合计','自营付费','自营自然流')
      AND 指标名称 IN ('成交金额','消耗金额','投产')
    GROUP BY 一级对象, 指标名称
    ORDER BY 一级对象
""")

# 8. 淘宝费用趋势
taobao_cost = query_json("""
    SELECT 开始日期, 一级对象, 数值
    FROM structured_data
    WHERE 平台='淘宝' AND 指标大类='费用'
    ORDER BY 开始日期
""")

# 9. 最近4周对比
recent_weeks = query_json("""
    SELECT DISTINCT 开始日期 FROM structured_data
    WHERE 指标大类='成交' AND 一级对象='总成交'
    ORDER BY 开始日期 DESC LIMIT 4
""")
recent_dates = [r['开始日期'] for r in recent_weeks]

recent_compare = query_json(f"""
    SELECT 开始日期, 平台, 一级对象, 数值
    FROM structured_data
    WHERE 指标大类='成交' AND 一级对象 IN ('总成交','净成交','退款')
      AND 开始日期 IN ({','.join(f"'{d}'" for d in recent_dates)})
    ORDER BY 开始日期, 平台
""")

# 10. platform_weekly_summary 全量
pws = query_json("SELECT * FROM platform_weekly_summary ORDER BY 开始日期, 平台")

conn.close()

# Build HTML
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>店铺每周数据汇总 - 电商分析看板</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
:root {{
  --bg: #0f1117;
  --card: #1a1d27;
  --border: #2a2d3a;
  --text: #e4e4e7;
  --text2: #a1a1aa;
  --accent: #6366f1;
  --green: #22c55e;
  --red: #ef4444;
  --orange: #f59e0b;
  --blue: #3b82f6;
  --pink: #ec4899;
  --cyan: #06b6d4;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.6;
}}
.header {{
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
  padding: 28px 32px; border-bottom: 1px solid var(--border);
}}
.header h1 {{ font-size: 24px; font-weight: 700; }}
.header .sub {{ color: var(--text2); font-size: 14px; margin-top: 4px; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
.kpi-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }}
.kpi {{
  background: var(--card); border: 1px solid var(--border); border-radius: 12px;
  padding: 20px; text-align: center;
}}
.kpi .label {{ color: var(--text2); font-size: 13px; margin-bottom: 6px; }}
.kpi .value {{ font-size: 28px; font-weight: 700; }}
.kpi .value.green {{ color: var(--green); }}
.kpi .value.blue {{ color: var(--blue); }}
.kpi .value.red {{ color: var(--red); }}
.kpi .value.orange {{ color: var(--orange); }}
.grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
.grid3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
.card {{
  background: var(--card); border: 1px solid var(--border); border-radius: 12px;
  padding: 20px; min-height: 300px;
}}
.card h3 {{ font-size: 15px; font-weight: 600; margin-bottom: 16px; color: var(--text); }}
.card canvas {{ width: 100% !important; }}
.full {{ grid-column: 1 / -1; }}
table {{
  width: 100%; border-collapse: collapse; font-size: 13px;
}}
th {{ text-align: left; padding: 10px 12px; border-bottom: 2px solid var(--border); color: var(--text2); font-weight: 600; white-space: nowrap; }}
td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); white-space: nowrap; }}
tr:hover td {{ background: rgba(99,102,241,0.08); }}
.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.positive {{ color: var(--green); }}
.negative {{ color: var(--red); }}
.tabs {{ display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }}
.tab {{
  padding: 6px 16px; border-radius: 8px; cursor: pointer; font-size: 13px;
  background: var(--border); color: var(--text2); border: none; transition: all 0.2s;
}}
.tab.active {{ background: var(--accent); color: white; }}
.section-title {{ font-size: 18px; font-weight: 700; margin: 32px 0 16px; padding-left: 12px; border-left: 3px solid var(--accent); }}
.filter-bar {{
  display: flex; gap: 12px; align-items: center; margin-bottom: 20px; flex-wrap: wrap;
}}
.filter-bar select {{
  background: var(--card); color: var(--text); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 12px; font-size: 13px;
}}
@media (max-width: 900px) {{
  .grid2, .grid3 {{ grid-template-columns: 1fr; }}
  .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
}}
@media (max-width: 600px) {{
  .kpi-row {{ grid-template-columns: 1fr; }}
  .container {{ padding: 12px; }}
}}
</style>
</head>
<body>

<div class="header">
  <h1>店铺每周数据汇总 · 电商分析看板</h1>
  <div class="sub">数据范围：2025-02-15 ~ 2026-03-15 · 覆盖平台：小红书 / 抖店 / 淘宝 / 微信 / B站 / 天猫</div>
</div>

<div class="container">

<!-- KPI -->
<div class="kpi-row" id="kpiRow"></div>

<!-- 总成交趋势 -->
<div class="section-title">成交趋势</div>
<div class="filter-bar">
  <select id="metricSelect" onchange="updateTrend()">
    <option value="总成交">总成交</option>
    <option value="净成交">净成交</option>
  </select>
  <select id="stackSelect" onchange="updateTrend()">
    <option value="0">折线图</option>
    <option value="1">堆叠面积图</option>
  </select>
</div>
<div class="grid2">
  <div class="card full"><canvas id="trendChart" height="100"></canvas></div>
</div>

<!-- 平台对比 -->
<div class="section-title">平台对比</div>
<div class="grid2">
  <div class="card"><h3>各平台累计成交</h3><canvas id="platformBar"></canvas></div>
  <div class="card"><h3>成交占比</h3><canvas id="platformPie"></canvas></div>
</div>

<!-- 渠道细分 -->
<div class="section-title">渠道细分</div>
<div class="tabs" id="channelTabs"></div>
<div class="grid2">
  <div class="card"><h3 id="channelTitle">渠道分布</h3><canvas id="channelChart"></canvas></div>
  <div class="card"><h3>渠道明细</h3><div id="channelTable" style="overflow-x:auto;"></div></div>
</div>

<!-- 投放 ROI -->
<div class="section-title">投放分析</div>
<div class="grid2">
  <div class="card"><h3>小红书 · 付费投放趋势</h3><canvas id="xhsRoiChart" height="120"></canvas></div>
  <div class="card"><h3>抖店 · 各账号付费效率</h3><canvas id="douyinPaidChart"></canvas></div>
</div>

<!-- 淘宝费用 -->
<div class="grid2">
  <div class="card"><h3>淘宝 · 费用趋势</h3><canvas id="taobaoCostChart" height="120"></canvas></div>
  <div class="card"><h3>退款率趋势</h3><canvas id="refundRateChart" height="120"></canvas></div>
</div>

<!-- 最近4周明细 -->
<div class="section-title">最近4周周报</div>
<div class="card full" style="overflow-x:auto; margin-bottom: 24px;">
  <table id="weeklyTable"></table>
</div>

<!-- 全量数据表 -->
<div class="section-title">全量周数据</div>
<div class="filter-bar">
  <select id="tablePlatform" onchange="renderFullTable()">
    <option value="all">全部平台</option>
  </select>
</div>
<div class="card full" style="overflow-x:auto; margin-bottom: 24px; max-height: 600px; overflow-y: auto;">
  <table id="fullTable"></table>
</div>

</div>

<script>
// ============ DATA ============
const weeklyRevenue = {json.dumps(weekly_revenue, ensure_ascii=False)};
const weeklyNet = {json.dumps(weekly_net, ensure_ascii=False)};
const weeklyRefund = {json.dumps(weekly_refund, ensure_ascii=False)};
const platformTotals = {json.dumps(platform_totals, ensure_ascii=False)};
const channelData = {json.dumps(channel_data, ensure_ascii=False)};
const xhsRoi = {json.dumps(xhs_roi, ensure_ascii=False)};
const douyinPaid = {json.dumps(douyin_paid, ensure_ascii=False)};
const taobaoCost = {json.dumps(taobao_cost, ensure_ascii=False)};
const recentCompare = {json.dumps(recent_compare, ensure_ascii=False)};
const recentDates = {json.dumps(recent_dates, ensure_ascii=False)};
const pws = {json.dumps(pws, ensure_ascii=False)};

const COLORS = {{
  '小红书': '#ff4757', '抖店': '#1e90ff', '淘宝': '#ff8c00',
  '微信': '#2ed573', 'B站': '#00b8d4', '天猫': '#a855f7'
}};
const PLATFORMS = ['抖店','小红书','淘宝','微信','B站','天猫'];

function fmt(n) {{
  if (n == null || isNaN(n)) return '-';
  if (Math.abs(n) >= 10000) return (n/10000).toFixed(2) + '万';
  return n.toFixed(0);
}}
function fmtFull(n) {{
  if (n == null || isNaN(n)) return '-';
  return n.toLocaleString('zh-CN', {{maximumFractionDigits: 0}});
}}
function pct(a, b) {{
  if (!b || b === 0) return '-';
  return (a / b * 100).toFixed(1) + '%';
}}

// ============ KPI ============
(function() {{
  const total = platformTotals.reduce((s,r) => s + (r['总成交']||0), 0);
  const net = platformTotals.reduce((s,r) => s + (r['净成交']||0), 0);
  const refund = platformTotals.reduce((s,r) => s + (r['退款金额']||0), 0);
  const refundRate = total > 0 ? (refund / total * 100).toFixed(1) + '%' : '-';
  // latest week total
  const latestDate = recentDates[0];
  const latestTotal = recentCompare.filter(r => r['开始日期']===latestDate && r['一级对象']==='总成交').reduce((s,r)=>s+(r['数值']||0),0);
  const prevDate = recentDates[1];
  const prevTotal = recentCompare.filter(r => r['开始日期']===prevDate && r['一级对象']==='总成交').reduce((s,r)=>s+(r['数值']||0),0);
  const wow = prevTotal > 0 ? ((latestTotal - prevTotal)/prevTotal*100).toFixed(1) : '-';

  document.getElementById('kpiRow').innerHTML = `
    <div class="kpi"><div class="label">累计总成交</div><div class="value green">${{fmt(total)}}</div></div>
    <div class="kpi"><div class="label">累计净成交</div><div class="value blue">${{fmt(net)}}</div></div>
    <div class="kpi"><div class="label">累计退款</div><div class="value red">${{fmt(refund)}}</div></div>
    <div class="kpi"><div class="label">退款率</div><div class="value orange">${{refundRate}}</div></div>
    <div class="kpi"><div class="label">最新周 (${{latestDate}})</div><div class="value green">${{fmt(latestTotal)}}</div></div>
    <div class="kpi"><div class="label">周环比</div><div class="value ${{parseFloat(wow)>=0?'green':'red'}}">${{wow}}%</div></div>
  `;
}})();

// ============ TREND CHART ============
let trendChart;
function updateTrend() {{
  const metric = document.getElementById('metricSelect').value;
  const stacked = document.getElementById('stackSelect').value === '1';
  const src = metric === '总成交' ? weeklyRevenue : weeklyNet;

  // group by date
  const dateMap = {{}};
  src.forEach(r => {{
    if (!dateMap[r['开始日期']]) dateMap[r['开始日期']] = {{}};
    dateMap[r['开始日期']][r['平台']] = r['数值'];
  }});
  const dates = Object.keys(dateMap).sort();
  const datasets = PLATFORMS.map(p => ({{
    label: p, data: dates.map(d => dateMap[d]?.[p] || 0),
    borderColor: COLORS[p], backgroundColor: stacked ? COLORS[p]+'44' : 'transparent',
    fill: stacked, tension: 0.3, borderWidth: 2, pointRadius: 0,
  }}));

  if (trendChart) trendChart.destroy();
  trendChart = new Chart(document.getElementById('trendChart'), {{
    type: 'line',
    data: {{ labels: dates.map(d => d.slice(5)), datasets }},
    options: {{
      responsive: true, interaction: {{ mode: 'index', intersect: false }},
      plugins: {{ legend: {{ labels: {{ color: '#a1a1aa', usePointStyle: true }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#71717a', maxRotation: 45 }}, grid: {{ color: '#27272a' }} }},
        y: {{ stacked, ticks: {{ color: '#71717a', callback: v => fmt(v) }}, grid: {{ color: '#27272a' }} }}
      }}
    }}
  }});
}}
updateTrend();

// ============ PLATFORM BAR + PIE ============
(function() {{
  const labels = platformTotals.map(r => r['平台']);
  const colors = labels.map(l => COLORS[l] || '#666');

  new Chart(document.getElementById('platformBar'), {{
    type: 'bar',
    data: {{
      labels,
      datasets: [
        {{ label: '总成交', data: platformTotals.map(r => r['总成交']||0), backgroundColor: colors.map(c=>c+'cc') }},
        {{ label: '净成交', data: platformTotals.map(r => r['净成交']||0), backgroundColor: colors.map(c=>c+'66') }},
      ]
    }},
    options: {{
      responsive: true, plugins: {{ legend: {{ labels: {{ color: '#a1a1aa' }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#a1a1aa' }}, grid: {{ display: false }} }},
        y: {{ ticks: {{ color: '#71717a', callback: v => fmt(v) }}, grid: {{ color: '#27272a' }} }}
      }}
    }}
  }});

  new Chart(document.getElementById('platformPie'), {{
    type: 'doughnut',
    data: {{
      labels,
      datasets: [{{ data: platformTotals.map(r => r['总成交']||0), backgroundColor: colors, borderWidth: 0 }}]
    }},
    options: {{
      responsive: true,
      plugins: {{
        legend: {{ position: 'right', labels: {{ color: '#a1a1aa', padding: 12 }} }},
        tooltip: {{ callbacks: {{ label: ctx => ctx.label + ': ' + fmt(ctx.raw) }} }}
      }}
    }}
  }});
}})();

// ============ CHANNEL ============
let channelChart;
const channelPlatforms = [...new Set(channelData.map(r => r['平台']))];
const channelTabsEl = document.getElementById('channelTabs');
channelPlatforms.forEach((p, i) => {{
  const btn = document.createElement('button');
  btn.className = 'tab' + (i===0?' active':'');
  btn.textContent = p;
  btn.onclick = () => showChannel(p, btn);
  channelTabsEl.appendChild(btn);
}});

function showChannel(platform, btn) {{
  document.querySelectorAll('#channelTabs .tab').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');

  const data = channelData.filter(r => r['平台'] === platform);
  const labels = data.map(r => r['一级对象']);
  const values = data.map(r => r['总计']);
  const total = values.reduce((a,b)=>a+b,0);

  document.getElementById('channelTitle').textContent = platform + ' · 渠道分布';

  if (channelChart) channelChart.destroy();
  channelChart = new Chart(document.getElementById('channelChart'), {{
    type: 'bar',
    data: {{
      labels,
      datasets: [{{ data: values, backgroundColor: '#6366f1cc', borderRadius: 6 }}]
    }},
    options: {{
      indexAxis: 'y', responsive: true,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: '#71717a', callback: v => fmt(v) }}, grid: {{ color: '#27272a' }} }},
        y: {{ ticks: {{ color: '#a1a1aa' }}, grid: {{ display: false }} }}
      }}
    }}
  }});

  // table
  let html = '<table><tr><th>渠道</th><th class="num">成交金额</th><th class="num">占比</th></tr>';
  data.forEach(r => {{
    html += `<tr><td>${{r['一级对象']}}</td><td class="num">${{fmtFull(r['总计'])}}</td><td class="num">${{pct(r['总计'],total)}}</td></tr>`;
  }});
  html += '</table>';
  document.getElementById('channelTable').innerHTML = html;
}}
showChannel(channelPlatforms[0]);

// ============ XHS ROI ============
(function() {{
  const dates = [...new Set(xhsRoi.map(r=>r['开始日期']))].sort();
  const byDate = {{}};
  xhsRoi.forEach(r => {{
    if (!byDate[r['开始日期']]) byDate[r['开始日期']] = {{}};
    byDate[r['开始日期']][r['指标名称']] = r['数值'];
  }});

  new Chart(document.getElementById('xhsRoiChart'), {{
    type: 'bar',
    data: {{
      labels: dates.map(d=>d.slice(5)),
      datasets: [
        {{ label: '付费成交', data: dates.map(d=>byDate[d]?.['成交金额']||0), backgroundColor: '#6366f1aa', order: 2, yAxisID: 'y' }},
        {{ label: '消耗', data: dates.map(d=>byDate[d]?.['消耗金额']||0), backgroundColor: '#ef444488', order: 2, yAxisID: 'y' }},
        {{ label: '投产比', data: dates.map(d=>byDate[d]?.['投产']||0), type:'line', borderColor:'#22c55e', backgroundColor:'transparent', tension:0.3, borderWidth:2, pointRadius:2, order:1, yAxisID:'y1' }}
      ]
    }},
    options: {{
      responsive: true, interaction: {{ mode: 'index', intersect: false }},
      plugins: {{ legend: {{ labels: {{ color: '#a1a1aa', usePointStyle: true }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#71717a', maxRotation: 45 }}, grid: {{ display: false }} }},
        y: {{ position: 'left', ticks: {{ color: '#71717a', callback: v=>fmt(v) }}, grid: {{ color: '#27272a' }} }},
        y1: {{ position: 'right', ticks: {{ color: '#22c55e' }}, grid: {{ display: false }} }}
      }}
    }}
  }});
}})();

// ============ DOUYIN PAID ============
(function() {{
  const accounts = [...new Set(douyinPaid.map(r => r['一级对象']))];
  const revenue = [], cost = [], roi = [];
  accounts.forEach(a => {{
    const items = douyinPaid.filter(r => r['一级对象'] === a);
    revenue.push(items.find(r => r['指标名称']==='成交金额')?.['总计'] || 0);
    cost.push(items.find(r => r['指标名称']==='消耗金额')?.['总计'] || 0);
    const roiItem = items.find(r => r['指标名称']==='投产');
    const weeks = roiItem ? 1 : 0;
    roi.push(roiItem ? roiItem['总计'] : 0);
  }});

  // Calculate average ROI
  const avgRoi = accounts.map((a, i) => {{
    const items = douyinPaid.filter(r => r['一级对象'] === a && r['指标名称']==='投产');
    if (items.length === 0) return 0;
    // total 投产 is sum of weekly 投产, we need count of weeks
    const revItem = douyinPaid.filter(r => r['一级对象'] === a && r['指标名称']==='成交金额');
    const costItem = douyinPaid.filter(r => r['一级对象'] === a && r['指标名称']==='消耗金额');
    if (costItem.length && costItem[0]['总计'] > 0) return revItem[0]['总计'] / costItem[0]['总计'];
    return 0;
  }});

  new Chart(document.getElementById('douyinPaidChart'), {{
    type: 'bar',
    data: {{
      labels: accounts.map(a => a.length > 8 ? a.slice(0,8)+'…' : a),
      datasets: [
        {{ label: '成交', data: revenue, backgroundColor: '#3b82f6aa', yAxisID: 'y' }},
        {{ label: '消耗', data: cost, backgroundColor: '#f59e0baa', yAxisID: 'y' }},
        {{ label: '综合ROI', data: avgRoi, type: 'line', borderColor: '#22c55e', backgroundColor: 'transparent', pointRadius: 4, borderWidth: 2, yAxisID: 'y1' }}
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ labels: {{ color: '#a1a1aa', usePointStyle: true }} }}, tooltip: {{ callbacks: {{ label: ctx => ctx.dataset.label + ': ' + (ctx.datasetIndex===2 ? ctx.raw.toFixed(2) : fmt(ctx.raw)) }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#a1a1aa', maxRotation: 45 }}, grid: {{ display: false }} }},
        y: {{ position: 'left', ticks: {{ color: '#71717a', callback: v=>fmt(v) }}, grid: {{ color: '#27272a' }} }},
        y1: {{ position: 'right', ticks: {{ color: '#22c55e' }}, grid: {{ display: false }}, min: 0 }}
      }}
    }}
  }});
}})();

// ============ TAOBAO COST ============
(function() {{
  const dates = [...new Set(taobaoCost.map(r=>r['开始日期']))].sort();
  const categories = ['总支出','付费支出','淘客支出'];
  const byDate = {{}};
  taobaoCost.forEach(r => {{
    if (!byDate[r['开始日期']]) byDate[r['开始日期']] = {{}};
    byDate[r['开始日期']][r['一级对象']] = r['数值'];
  }});

  const colors = ['#f59e0b','#6366f1','#ec4899'];
  new Chart(document.getElementById('taobaoCostChart'), {{
    type: 'line',
    data: {{
      labels: dates.map(d=>d.slice(5)),
      datasets: categories.map((c,i) => ({{
        label: c, data: dates.map(d=>byDate[d]?.[c]||0),
        borderColor: colors[i], backgroundColor: 'transparent', tension: 0.3, borderWidth: 2, pointRadius: 0
      }}))
    }},
    options: {{
      responsive: true, interaction: {{ mode: 'index', intersect: false }},
      plugins: {{ legend: {{ labels: {{ color: '#a1a1aa', usePointStyle: true }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#71717a', maxRotation: 45 }}, grid: {{ display: false }} }},
        y: {{ ticks: {{ color: '#71717a', callback: v=>fmt(v) }}, grid: {{ color: '#27272a' }} }}
      }}
    }}
  }});
}})();

// ============ REFUND RATE ============
(function() {{
  // Calculate refund rate per week per platform
  const revenueMap = {{}};
  weeklyRevenue.forEach(r => {{
    const key = r['开始日期'] + '|' + r['平台'];
    revenueMap[key] = r['数值'];
  }});
  const refundMap = {{}};
  weeklyRefund.forEach(r => {{
    const key = r['开始日期'] + '|' + r['平台'];
    refundMap[key] = r['数值'];
  }});

  const dates = [...new Set(weeklyRevenue.map(r=>r['开始日期']))].sort();
  const mainPlatforms = ['抖店','小红书','淘宝'];

  new Chart(document.getElementById('refundRateChart'), {{
    type: 'line',
    data: {{
      labels: dates.map(d=>d.slice(5)),
      datasets: mainPlatforms.map(p => ({{
        label: p,
        data: dates.map(d => {{
          const rev = revenueMap[d+'|'+p];
          const ref = refundMap[d+'|'+p];
          return (rev && ref) ? (ref/rev*100) : null;
        }}),
        borderColor: COLORS[p], backgroundColor: 'transparent',
        tension: 0.3, borderWidth: 2, pointRadius: 0, spanGaps: true
      }}))
    }},
    options: {{
      responsive: true, interaction: {{ mode: 'index', intersect: false }},
      plugins: {{ legend: {{ labels: {{ color: '#a1a1aa', usePointStyle: true }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#71717a', maxRotation: 45 }}, grid: {{ display: false }} }},
        y: {{ ticks: {{ color: '#71717a', callback: v=>v+'%' }}, grid: {{ color: '#27272a' }} }}
      }}
    }}
  }});
}})();

// ============ RECENT 4 WEEKS TABLE ============
(function() {{
  const sortedDates = [...recentDates].sort();
  let html = '<tr><th>平台</th>';
  sortedDates.forEach(d => html += `<th class="num" colspan="3">${{d}}</th>`);
  html += '</tr><tr><th></th>';
  sortedDates.forEach(() => html += '<th class="num">总成交</th><th class="num">净成交</th><th class="num">退款</th>');
  html += '</tr>';

  PLATFORMS.forEach(p => {{
    html += `<tr><td style="color:${{COLORS[p]}};font-weight:600">${{p}}</td>`;
    sortedDates.forEach(d => {{
      const get = (obj) => recentCompare.find(r => r['开始日期']===d && r['平台']===p && r['一级对象']===obj);
      const gross = get('总成交');
      const net = get('净成交');
      const ref = get('退款');
      html += `<td class="num">${{gross ? fmtFull(gross['数值']) : '-'}}</td>`;
      html += `<td class="num">${{net ? fmtFull(net['数值']) : '-'}}</td>`;
      html += `<td class="num negative">${{ref ? fmtFull(ref['数值']) : '-'}}</td>`;
    }});
    html += '</tr>';
  }});

  // Total row
  html += '<tr style="font-weight:700;border-top:2px solid var(--border)"><td>合计</td>';
  sortedDates.forEach(d => {{
    const grossTotal = recentCompare.filter(r=>r['开始日期']===d&&r['一级对象']==='总成交').reduce((s,r)=>s+(r['数值']||0),0);
    const netTotal = recentCompare.filter(r=>r['开始日期']===d&&r['一级对象']==='净成交').reduce((s,r)=>s+(r['数值']||0),0);
    const refTotal = recentCompare.filter(r=>r['开始日期']===d&&r['一级对象']==='退款').reduce((s,r)=>s+(r['数值']||0),0);
    html += `<td class="num">${{fmtFull(grossTotal)}}</td><td class="num">${{fmtFull(netTotal)}}</td><td class="num negative">${{fmtFull(refTotal)}}</td>`;
  }});
  html += '</tr>';

  document.getElementById('weeklyTable').innerHTML = html;
}})();

// ============ FULL TABLE ============
const tablePlatformSel = document.getElementById('tablePlatform');
PLATFORMS.forEach(p => {{
  const opt = document.createElement('option');
  opt.value = p; opt.textContent = p;
  tablePlatformSel.appendChild(opt);
}});

function renderFullTable() {{
  const sel = tablePlatformSel.value;
  const data = sel === 'all' ? pws : pws.filter(r => r['平台'] === sel);
  let html = '<tr><th>周</th><th>平台</th><th class="num">总成交</th><th class="num">退款</th><th class="num">净成交</th><th class="num">自营</th><th class="num">合作</th><th class="num">付费</th><th class="num">支出</th></tr>';
  data.forEach(r => {{
    html += `<tr>
      <td>${{r['周标签']}}</td>
      <td style="color:${{COLORS[r['平台']]||'#999'}}">${{r['平台']}}</td>
      <td class="num">${{fmtFull(r['总成交'])}}</td>
      <td class="num negative">${{fmtFull(r['退款金额'])}}</td>
      <td class="num">${{fmtFull(r['净成交'])}}</td>
      <td class="num">${{fmtFull(r['自营成交'])}}</td>
      <td class="num">${{fmtFull(r['合作成交'])}}</td>
      <td class="num">${{fmtFull(r['付费成交'])}}</td>
      <td class="num negative">${{fmtFull(r['支出合计'])}}</td>
    </tr>`;
  }});
  document.getElementById('fullTable').innerHTML = html;
}}
renderFullTable();
</script>
</body>
</html>
"""

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Dashboard saved to {OUT_PATH}")
print(f"File size: {os.path.getsize(OUT_PATH) / 1024:.0f} KB")
