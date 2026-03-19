#!/usr/bin/env python3
"""v3 电商数据看板 — 单页滚动杂志式 · ECharts · 彩色活泼风格"""
import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "data" / "店铺每周数据汇总.sqlite"
LEGACY_DB = Path("/Users/wmix/Downloads/店铺每周数据汇总_2026-03-18.sqlite")
DB = Path(os.environ.get("WMIX_DB_PATH", DEFAULT_DB))
if not DB.exists() and LEGACY_DB.exists():
    DB = LEGACY_DB
OUT = ROOT / "dashboard_v3.html"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
q = lambda sql: [dict(r) for r in conn.execute(sql).fetchall()]

structured = q("SELECT * FROM structured_data ORDER BY 开始日期, 平台")
pws = q("SELECT * FROM platform_weekly_summary ORDER BY 开始日期, 平台")
notes = q("SELECT * FROM notes")
conn.close()

structured_json = json.dumps(structured, ensure_ascii=False)
pws_json = json.dumps(pws, ensure_ascii=False)
notes_json = json.dumps(notes, ensure_ascii=False)

html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>电商数据看板 v3</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#f8f9fc;--bg2:#f1f3f9;--card:#ffffff;--border:#e5e7eb;
  --t1:#1a1a2e;--t2:#4a4a6a;--t3:#8888a4;
  --accent:#6366f1;--green:#10b981;--red:#ef4444;--orange:#f59e0b;
  --radius:14px;--shadow:0 2px 12px rgba(99,102,241,.08);
}
html{scroll-behavior:smooth}
body{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','PingFang SC','Hiragino Sans GB',sans-serif;background:var(--bg);color:var(--t1);font-size:14px;overflow-x:hidden;line-height:1.6}

/* ===== STICKY FILTER BAR ===== */
.filter-bar{position:sticky;top:0;z-index:100;background:rgba(255,255,255,.92);backdrop-filter:blur(16px);border-bottom:1px solid var(--border);padding:12px 24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.filter-bar .logo{font-size:17px;font-weight:800;background:linear-gradient(135deg,#6366f1,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-right:8px;white-space:nowrap}
.filter-group{display:flex;align-items:center;gap:6px}
.filter-group label{font-size:12px;color:var(--t3);font-weight:600;white-space:nowrap}
.pill{display:inline-flex;align-items:center;padding:5px 14px;border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;border:1.5px solid var(--border);background:#fff;color:var(--t2);transition:all .2s;user-select:none}
.pill:hover{border-color:var(--accent);color:var(--accent)}
.pill.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.plat-pill{position:relative;padding-left:24px}
.plat-pill::before{content:'';position:absolute;left:10px;top:50%;transform:translateY(-50%);width:8px;height:8px;border-radius:50%}
.plat-pill[data-p="抖店"]::before{background:#1e90ff}
.plat-pill[data-p="小红书"]::before{background:#ff2d55}
.plat-pill[data-p="淘宝"]::before{background:#ff6a00}
.plat-pill[data-p="微信"]::before{background:#07c160}
.plat-pill[data-p="B站"]::before{background:#00a1d6}
.plat-pill[data-p="天猫"]::before{background:#8b5cf6}

/* ===== FLOATING NAV ===== */
.side-nav{position:fixed;right:20px;top:50%;transform:translateY(-50%);z-index:90;display:flex;flex-direction:column;gap:12px;padding:12px 8px;background:rgba(255,255,255,.85);backdrop-filter:blur(8px);border-radius:20px;box-shadow:var(--shadow)}
.side-nav a{width:10px;height:10px;border-radius:50%;background:var(--border);display:block;transition:all .25s;position:relative}
.side-nav a:hover,.side-nav a.active{background:var(--accent);transform:scale(1.4)}
.side-nav a .tip{position:absolute;right:22px;top:50%;transform:translateY(-50%);background:var(--t1);color:#fff;font-size:11px;padding:3px 10px;border-radius:6px;white-space:nowrap;opacity:0;pointer-events:none;transition:opacity .2s}
.side-nav a:hover .tip{opacity:1}

/* ===== SECTIONS ===== */
.section{padding:40px 24px;max-width:1400px;margin:0 auto}
.section:nth-child(even){background:var(--bg2)}
.section-title{font-size:22px;font-weight:800;margin-bottom:6px}
.section-sub{font-size:13px;color:var(--t3);margin-bottom:24px}

/* ===== HERO ===== */
.hero{background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 40%,#a78bfa 100%);color:#fff;padding:56px 24px 48px;text-align:center}
.hero h1{font-size:36px;font-weight:900;margin-bottom:8px;text-shadow:0 2px 12px rgba(0,0,0,.15)}
.hero .sub{font-size:15px;opacity:.85;margin-bottom:24px}
.hero .big-num{font-size:48px;font-weight:900;font-variant-numeric:tabular-nums}
.hero .big-label{font-size:13px;opacity:.7;margin-top:4px}

/* ===== KPI CARDS ===== */
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}
.kpi-card{background:var(--card);border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow);position:relative;overflow:hidden}
.kpi-card .label{font-size:12px;color:var(--t3);font-weight:600;margin-bottom:4px}
.kpi-card .val{font-size:24px;font-weight:800;font-variant-numeric:tabular-nums}
.kpi-card .delta{font-size:12px;font-weight:600;margin-top:2px}
.kpi-card .delta.up{color:var(--green)}.kpi-card .delta.down{color:var(--red)}.kpi-card .delta.neutral{color:var(--t3)}
.kpi-card .spark{position:absolute;bottom:0;right:0;width:100px;height:40px}

/* ===== CHART CONTAINERS ===== */
.chart-row{display:grid;gap:16px;margin-bottom:16px}
.chart-row.r2{grid-template-columns:1fr 1fr}
.chart-row.r3{grid-template-columns:1fr 1fr 1fr}
.chart-box{background:var(--card);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow)}
.chart-box h4{font-size:13px;font-weight:700;color:var(--t2);margin-bottom:12px}
.chart-box .chart{width:100%;min-height:360px}
.chart-box .chart-sm{width:100%;min-height:280px}
.chart-box .chart-lg{width:100%;min-height:420px}

/* ===== TREND PILLS ===== */
.metric-pills{display:flex;gap:6px;margin-bottom:16px;flex-wrap:wrap}

/* ===== ACCORDION ===== */
.accordion{margin-bottom:12px;border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow)}
.accordion-header{display:flex;align-items:center;padding:16px 20px;cursor:pointer;background:var(--card);transition:background .2s;gap:12px}
.accordion-header:hover{background:#fafbff}
.accordion-header .plat-icon{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:800;color:#fff;flex-shrink:0}
.accordion-header .info{flex:1}
.accordion-header .info .name{font-size:15px;font-weight:700}
.accordion-header .info .stats{font-size:12px;color:var(--t3)}
.accordion-header .arrow{font-size:18px;color:var(--t3);transition:transform .3s}
.accordion.open .arrow{transform:rotate(180deg)}
.accordion-body{max-height:0;overflow:hidden;transition:max-height .4s ease;background:var(--card)}
.accordion.open .accordion-body{max-height:3000px}
.accordion-inner{padding:0 20px 20px}

/* ===== TABLE ===== */
.data-table-wrap{overflow-x:auto;max-height:600px;overflow-y:auto;border-radius:var(--radius);box-shadow:var(--shadow)}
table{width:100%;border-collapse:collapse;font-size:12px;background:var(--card)}
th{text-align:left;padding:10px 12px;border-bottom:2px solid var(--border);color:var(--t3);font-weight:700;position:sticky;top:0;background:var(--card);white-space:nowrap;cursor:pointer}
th:hover{color:var(--accent)}
td{padding:8px 12px;border-bottom:1px solid #f0f0f5;white-space:nowrap}
tr:hover td{background:#f5f3ff}
.num{text-align:right;font-variant-numeric:tabular-nums}
.pos{color:var(--green)}.neg{color:var(--red)}

/* ===== RESPONSIVE ===== */
@media(max-width:1024px){
  .kpi-grid{grid-template-columns:repeat(2,1fr)}
  .chart-row.r2,.chart-row.r3{grid-template-columns:1fr}
}
@media(max-width:768px){
  .kpi-grid{grid-template-columns:1fr 1fr}
  .hero h1{font-size:24px}.hero .big-num{font-size:32px}
  .filter-bar{padding:8px 12px;gap:8px}
  .side-nav{right:8px;gap:8px;padding:8px 5px}
  .side-nav a{width:8px;height:8px}
  .section{padding:24px 12px}
}
</style>
</head>
<body>

<!-- STICKY FILTER BAR -->
<div class="filter-bar" id="filterBar">
  <span class="logo">◈ 电商看板 v3</span>
  <div class="filter-group">
    <label>日期</label>
    <span class="pill active" data-range="4" onclick="setDateRange(4,this)">近4周</span>
    <span class="pill" data-range="8" onclick="setDateRange(8,this)">近8周</span>
    <span class="pill" data-range="13" onclick="setDateRange(13,this)">近13周</span>
    <span class="pill" data-range="26" onclick="setDateRange(26,this)">近26周</span>
    <span class="pill" data-range="0" onclick="setDateRange(0,this)">全部</span>
  </div>
  <div class="filter-group" id="platFilter">
    <label>平台</label>
  </div>
</div>

<!-- FLOATING SIDE NAV -->
<nav class="side-nav" id="sideNav">
  <a href="#sec-hero"><span class="tip">概览</span></a>
  <a href="#sec-kpi"><span class="tip">KPI</span></a>
  <a href="#sec-river"><span class="tip">收入之河</span></a>
  <a href="#sec-panorama"><span class="tip">全景对比</span></a>
  <a href="#sec-trend"><span class="tip">趋势</span></a>
  <a href="#sec-platform"><span class="tip">平台</span></a>
  <a href="#sec-ads"><span class="tip">投放</span></a>
  <a href="#sec-table"><span class="tip">数据表</span></a>
</nav>

<!-- ====== 1. HERO ====== -->
<div class="hero" id="sec-hero">
  <h1>电商数据全景看板</h1>
  <div class="sub" id="heroSub"></div>
  <div class="big-num" id="heroGMV"></div>
  <div class="big-label">累计总 GMV</div>
</div>

<!-- ====== 2. KPI ====== -->
<div class="section" id="sec-kpi">
  <div class="section-title">核心指标</div>
  <div class="section-sub">选定时间范围内的关键数据概览</div>
  <div class="kpi-grid" id="kpiGrid"></div>
</div>

<!-- ====== 3. RIVER ====== -->
<div class="section" id="sec-river" style="background:var(--bg2)">
  <div class="section-title">收入之河</div>
  <div class="section-sub">各平台成交金额随时间的流动</div>
  <div class="chart-box"><div class="chart-lg" id="chartRiver"></div></div>
</div>

<!-- ====== 4. PANORAMA ====== -->
<div class="section" id="sec-panorama">
  <div class="section-title">平台全景对比</div>
  <div class="section-sub">多维能力雷达 & 收入构成层级</div>
  <div class="chart-row r2">
    <div class="chart-box"><h4>五维雷达</h4><div class="chart" id="chartRadar"></div></div>
    <div class="chart-box"><h4>收入矩形树图</h4><div class="chart" id="chartTreemap"></div></div>
  </div>
</div>

<!-- ====== 5. TREND ====== -->
<div class="section" id="sec-trend" style="background:var(--bg2)">
  <div class="section-title">趋势分析</div>
  <div class="section-sub">追踪关键指标的周度变化</div>
  <div class="metric-pills" id="trendPills"></div>
  <div class="chart-box" style="margin-bottom:16px"><div class="chart-lg" id="chartTrend"></div></div>
  <div class="chart-row r2">
    <div class="chart-box"><h4>堆叠面积</h4><div class="chart" id="chartStack"></div></div>
    <div class="chart-box"><h4>周环比变化</h4><div class="chart" id="chartWow"></div></div>
  </div>
</div>

<!-- ====== 6. PLATFORM DRILL ====== -->
<div class="section" id="sec-platform">
  <div class="section-title">平台深钻</div>
  <div class="section-sub">展开查看每个平台的详细数据</div>
  <div id="accordionContainer"></div>
</div>

<!-- ====== 7. ADS ====== -->
<div class="section" id="sec-ads" style="background:var(--bg2)">
  <div class="section-title">投放分析</div>
  <div class="section-sub">广告投放效率与费用流向</div>
  <div class="kpi-grid" id="adsKpi" style="grid-template-columns:repeat(3,1fr)"></div>
  <div class="chart-box" style="margin-bottom:16px"><h4>费用流向桑基图</h4><div class="chart-lg" id="chartSankey"></div></div>
  <div class="chart-row r3">
    <div class="chart-box"><h4>小红书 · 投放效率</h4><div class="chart-sm" id="chartAdsXhs"></div></div>
    <div class="chart-box"><h4>抖店 · 投放效率</h4><div class="chart-sm" id="chartAdsDy"></div></div>
    <div class="chart-box"><h4>淘宝 · 费用构成</h4><div class="chart-sm" id="chartAdsTb"></div></div>
  </div>
  <div class="chart-box" style="margin-top:16px"><h4>ROI 周热力日历</h4><div class="chart-lg" id="chartCalendar"></div></div>
</div>

<!-- ====== 8. TABLE ====== -->
<div class="section" id="sec-table">
  <div class="section-title">全量数据表</div>
  <div class="section-sub">可排序的完整周度汇总</div>
  <div class="data-table-wrap" id="fullTable"></div>
</div>

<script>
// ===== DATA =====
const RAW = """ + structured_json + r""";
const PWS = """ + pws_json + r""";
const NOTES = """ + notes_json + r""";

// ===== CONSTANTS =====
const PLATS = ['抖店','小红书','淘宝','微信','B站','天猫'];
const COLORS = {
  '抖店':['#1e90ff','#00d4ff'],'小红书':['#ff2d55','#ff6b8a'],'淘宝':['#ff6a00','#ffab40'],
  '微信':['#07c160','#4edd8a'],'B站':['#00a1d6','#23d5e0'],'天猫':['#8b5cf6','#a78bfa']
};
const C = p => COLORS[p]?.[0] || '#6366f1';
const ALL_DATES = [...new Set(RAW.map(r=>r['开始日期']))].sort();
const END_MAP = {}; RAW.forEach(r => END_MAP[r['开始日期']] = r['结束日期']);

// ===== GLOBAL STATE =====
const STATE = {
  dateRange: 4,  // 0=all
  platforms: new Set(PLATS),
  trendMetric: 0,  // index
  expandedPlatform: null,
  dates: []  // computed
};

function computeDates() {
  const n = STATE.dateRange;
  STATE.dates = n === 0 ? [...ALL_DATES] : ALL_DATES.slice(-n);
}

// ===== HELPERS =====
function fmt(n){ if(n==null||isNaN(n)) return '-'; if(Math.abs(n)>=1e8) return (n/1e8).toFixed(2)+'亿'; if(Math.abs(n)>=1e4) return (n/1e4).toFixed(2)+'万'; return n.toLocaleString('zh-CN',{maximumFractionDigits:0}); }
function fmtK(n){ if(n==null||isNaN(n)) return '-'; return n.toLocaleString('zh-CN',{maximumFractionDigits:0}); }
function pct(a,b){ if(!b) return '-'; return (a/b*100).toFixed(1)+'%'; }
function deltaObj(a,b){ if(!b) return {text:'-',cls:'neutral',val:0}; const d=(a-b)/b*100; return {text:(d>=0?'+':'')+d.toFixed(1)+'%',cls:d>=0?'up':'down',val:d}; }

function sumFiltered(plat, cat, obj, metric, dates) {
  return RAW.filter(r => r['平台']===plat && r['指标大类']===cat && r['一级对象']===obj && r['指标名称']===metric && dates.includes(r['开始日期']))
    .reduce((s,r) => s + (r['数值']||0), 0);
}
function weeklyMap(cat, obj, metric, dates) {
  const m = {};
  RAW.filter(r => r['指标大类']===cat && r['一级对象']===obj && r['指标名称']===metric && dates.includes(r['开始日期']))
    .forEach(r => { if(!m[r['开始日期']]) m[r['开始日期']]={}; m[r['开始日期']][r['平台']]=r['数值']; });
  return m;
}
function activePlats() { return PLATS.filter(p => STATE.platforms.has(p)); }

// ===== ECHART POOL =====
const CHARTS = {};
function getChart(id) {
  if(CHARTS[id]) { CHARTS[id].dispose(); }
  const el = document.getElementById(id);
  if(!el) return null;
  const c = echarts.init(el);
  CHARTS[id] = c;
  return c;
}

// ===== FILTER BAR =====
function setDateRange(n, el) {
  STATE.dateRange = n;
  document.querySelectorAll('.filter-bar .pill[data-range]').forEach(p => p.classList.remove('active'));
  if(el) el.classList.add('active');
  renderAll();
}

function initPlatFilter() {
  const container = document.getElementById('platFilter');
  PLATS.forEach(p => {
    const pill = document.createElement('span');
    pill.className = 'pill plat-pill active';
    pill.dataset.p = p;
    pill.textContent = p;
    pill.onclick = () => {
      if(STATE.platforms.has(p)) { STATE.platforms.delete(p); pill.classList.remove('active'); }
      else { STATE.platforms.add(p); pill.classList.add('active'); }
      renderAll();
    };
    container.appendChild(pill);
  });
}

// ===== SIDE NAV =====
function initSideNav() {
  const sections = document.querySelectorAll('[id^="sec-"]');
  const navLinks = document.querySelectorAll('.side-nav a');
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if(e.isIntersecting) {
        const id = e.target.id;
        navLinks.forEach((a,i) => {
          a.classList.toggle('active', a.getAttribute('href') === '#'+id);
        });
      }
    });
  }, {threshold:0.3});
  sections.forEach(s => obs.observe(s));
}

// ===== RENDER ALL =====
function renderAll() {
  computeDates();
  renderHero();
  renderKPI();
  renderRiver();
  renderPanorama();
  renderTrend();
  renderAccordions();
  renderAds();
  renderTable();
}

// ===== 1. HERO =====
function renderHero() {
  const d = STATE.dates;
  document.getElementById('heroSub').textContent = d.length > 0
    ? d[0] + ' ~ ' + (END_MAP[d[d.length-1]]||d[d.length-1]) + ' · ' + d.length + '周'
    : '无数据';
  let total = 0;
  activePlats().forEach(p => { total += sumFiltered(p,'成交','总成交','成交金额',d); });
  document.getElementById('heroGMV').textContent = '¥' + fmt(total);
}

// ===== 2. KPI =====
function renderKPI() {
  const d = STATE.dates;
  const ap = activePlats();
  let totalGross=0,totalNet=0,totalRefund=0,totalSpend=0;
  ap.forEach(p => {
    totalGross += sumFiltered(p,'成交','总成交','成交金额',d);
    totalNet += sumFiltered(p,'成交','净成交','成交金额',d);
    totalRefund += sumFiltered(p,'成交','退款','退款金额',d);
    totalSpend += sumFiltered(p,'费用','总支出','支出金额',d) + sumFiltered(p,'付费','支出合计','支出金额',d);
  });
  // latest week & prev
  const latest = d[d.length-1], prev = d.length>1 ? d[d.length-2] : null;
  let latestGross=0, prevGross=0;
  ap.forEach(p => {
    latestGross += sumFiltered(p,'成交','总成交','成交金额',[latest]);
    if(prev) prevGross += sumFiltered(p,'成交','总成交','成交金额',[prev]);
  });
  const wow = deltaObj(latestGross, prevGross);
  const refRate = totalGross>0 ? (totalRefund/totalGross*100).toFixed(1)+'%' : '-';
  const roi = totalSpend>0 ? (totalGross/totalSpend).toFixed(2) : '-';

  // Sparkline data: weekly gross totals
  const sparkData = d.map(dt => {
    let s=0; ap.forEach(p => { s += sumFiltered(p,'成交','总成交','成交金额',[dt]); }); return s;
  });

  const kpis = [
    {label:'总成交',val:fmt(totalGross),color:'#6366f1'},
    {label:'净成交',val:fmt(totalNet),color:'#10b981'},
    {label:'退款金额',val:fmt(totalRefund),color:'#ef4444'},
    {label:'退款率',val:refRate,color:'#f59e0b'},
    {label:'最新周成交',val:fmt(latestGross),color:'#8b5cf6'},
    {label:'周环比',val:wow.text,color:wow.cls==='up'?'#10b981':'#ef4444',cls:wow.cls},
    {label:'累计支出',val:fmt(totalSpend),color:'#f97316'},
    {label:'综合ROI',val:roi,color:'#06b6d4'},
  ];

  const grid = document.getElementById('kpiGrid');
  grid.innerHTML = kpis.map((k,i) => `
    <div class="kpi-card">
      <div class="label">${k.label}</div>
      <div class="val" style="color:${k.color}">${k.val}</div>
      ${k.cls ? `<div class="delta ${k.cls}">${k.val}</div>` : ''}
      <div class="spark" id="spark${i}"></div>
    </div>`).join('');

  // Render sparklines
  kpis.forEach((k,i) => {
    const el = document.getElementById('spark'+i);
    if(!el || sparkData.length < 2) return;
    const c = echarts.init(el);
    c.setOption({
      grid:{left:0,right:0,top:0,bottom:0},
      xAxis:{show:false,data:d},
      yAxis:{show:false,min:'dataMin',max:'dataMax'},
      series:[{type:'line',data:sparkData,smooth:true,symbol:'none',lineStyle:{width:1.5,color:k.color},areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:k.color+'40'},{offset:1,color:k.color+'05'}])}}]
    });
    CHARTS['spark'+i] = c;
  });
}

// ===== 3. RIVER =====
function renderRiver() {
  const c = getChart('chartRiver'); if(!c) return;
  const d = STATE.dates, ap = activePlats();
  const data = [];
  d.forEach(dt => {
    ap.forEach(p => {
      const v = sumFiltered(p,'成交','总成交','成交金额',[dt]);
      data.push([dt, v, p]);
    });
  });
  c.setOption({
    tooltip:{trigger:'axis'},
    legend:{data:ap,top:10,textStyle:{color:'#4a4a6a'}},
    singleAxis:{type:'category',data:d,bottom:30,top:50,axisLabel:{formatter:v=>v.slice(5)}},
    series:[{
      type:'themeRiver',
      data:data,
      label:{show:false},
      emphasis:{itemStyle:{shadowBlur:20,shadowColor:'rgba(0,0,0,.2)'}},
      color:ap.map(p=>C(p))
    }]
  });
}

// ===== 4. PANORAMA =====
function renderPanorama() {
  renderRadar();
  renderTreemap();
}

function renderRadar() {
  const c = getChart('chartRadar'); if(!c) return;
  const d = STATE.dates, ap = activePlats();
  // 5 dimensions: totalGross, netGross, channelCount, lowRefundRate, growthMomentum
  const maxVals = [0,0,0,0,0];
  const platData = ap.map(p => {
    const gross = sumFiltered(p,'成交','总成交','成交金额',d);
    const net = sumFiltered(p,'成交','净成交','成交金额',d);
    const ref = sumFiltered(p,'成交','退款','退款金额',d);
    const chSet = new Set();
    RAW.filter(r=>r['平台']===p&&r['指标大类']==='渠道细分'&&d.includes(r['开始日期'])).forEach(r=>chSet.add(r['一级对象']));
    const chCount = chSet.size;
    const refRate = gross>0 ? 100-ref/gross*100 : 100; // higher=better
    // growth: last week vs first week
    const first = sumFiltered(p,'成交','总成交','成交金额',[d[0]]);
    const last = sumFiltered(p,'成交','总成交','成交金额',[d[d.length-1]]);
    const growth = first>0 ? (last-first)/first*100+50 : 50;
    const vals = [gross, net, chCount, refRate, Math.max(0,growth)];
    vals.forEach((v,i) => { if(v>maxVals[i]) maxVals[i]=v; });
    return {name:p, vals};
  });

  c.setOption({
    legend:{data:ap.map(p=>p),top:0,textStyle:{color:'#4a4a6a'}},
    radar:{
      indicator:[
        {name:'总成交',max:maxVals[0]*1.1||1},
        {name:'净成交',max:maxVals[1]*1.1||1},
        {name:'渠道数',max:maxVals[2]*1.2||1},
        {name:'低退款率',max:110},
        {name:'增长动力',max:maxVals[4]*1.2||100}
      ],
      shape:'polygon',
      splitArea:{areaStyle:{color:['#f8f9fc','#f1f3f9','#e8eaf6','#f1f3f9','#f8f9fc']}}
    },
    series:[{
      type:'radar',
      data:platData.map(pd => ({
        name:pd.name,
        value:pd.vals,
        lineStyle:{color:C(pd.name),width:2},
        areaStyle:{color:C(pd.name)+'25'},
        itemStyle:{color:C(pd.name)}
      }))
    }],
    tooltip:{}
  });
}

function renderTreemap() {
  const c = getChart('chartTreemap'); if(!c) return;
  const d = STATE.dates, ap = activePlats();
  const treeData = ap.map(p => {
    const channels = {};
    RAW.filter(r=>r['平台']===p&&r['指标大类']==='渠道细分'&&r['指标名称']==='成交金额'&&d.includes(r['开始日期']))
      .forEach(r=>{ channels[r['一级对象']] = (channels[r['一级对象']]||0) + (r['数值']||0); });
    const children = Object.entries(channels).map(([name,val])=>({name,value:val})).filter(x=>x.value>0).sort((a,b)=>b.value-a.value);
    const total = children.reduce((s,x)=>s+x.value,0);
    return {name:p, value:total, children, itemStyle:{color:C(p)}};
  }).filter(x=>x.value>0);

  c.setOption({
    tooltip:{formatter:info => {
      const v = info.value;
      return info.name + ': ¥' + fmt(v);
    }},
    series:[{
      type:'treemap',
      data:treeData,
      roam:false,
      leafDepth:2,
      levels:[
        {itemStyle:{borderColor:'#fff',borderWidth:3,gapWidth:3},upperLabel:{show:true,height:28,color:'#fff',fontWeight:'bold',fontSize:13}},
        {itemStyle:{borderColor:'#fff',borderWidth:1,gapWidth:1},colorMappingBy:'value'}
      ],
      label:{show:true,formatter:'{b}\n¥{c}',fontSize:11},
      breadcrumb:{show:true,top:5}
    }]
  });
}

// ===== 5. TREND =====
const TREND_METRICS = [
  {label:'总成交',cat:'成交',obj:'总成交',metric:'成交金额'},
  {label:'净成交',cat:'成交',obj:'净成交',metric:'成交金额'},
  {label:'退款',cat:'成交',obj:'退款',metric:'退款金额'},
  {label:'退款率',special:'refundRate'},
];

function initTrendPills() {
  const el = document.getElementById('trendPills');
  el.innerHTML = TREND_METRICS.map((m,i) =>
    `<span class="pill ${i===0?'active':''}" onclick="STATE.trendMetric=${i};document.querySelectorAll('#trendPills .pill').forEach(p=>p.classList.remove('active'));this.classList.add('active');renderTrend()">${m.label}</span>`
  ).join('');
}

function renderTrend() {
  const d = STATE.dates, ap = activePlats();
  const m = TREND_METRICS[STATE.trendMetric];
  const labels = d.map(x=>x.slice(5));

  // Main trend line
  const c1 = getChart('chartTrend');
  if(c1) {
    let series;
    if(m.special === 'refundRate') {
      const revMap = weeklyMap('成交','总成交','成交金额',d);
      const refMap = weeklyMap('成交','退款','退款金额',d);
      series = ap.map(p => ({
        name:p, type:'line', smooth:true, symbol:'circle', symbolSize:4,
        data:d.map(dt => {
          const rev = revMap[dt]?.[p], ref = refMap[dt]?.[p];
          return (rev && ref) ? +(ref/rev*100).toFixed(1) : null;
        }),
        lineStyle:{color:C(p),width:2.5},itemStyle:{color:C(p)},connectNulls:true
      }));
    } else {
      const wm = weeklyMap(m.cat,m.obj,m.metric,d);
      series = ap.map(p => ({
        name:p, type:'line', smooth:true, symbol:'circle', symbolSize:4,
        data:d.map(dt => wm[dt]?.[p] || null),
        lineStyle:{color:C(p),width:2.5},itemStyle:{color:C(p)},connectNulls:true
      }));
    }
    c1.setOption({
      tooltip:{trigger:'axis'},
      legend:{data:ap,top:0,textStyle:{color:'#4a4a6a'}},
      grid:{left:60,right:30,top:40,bottom:60},
      xAxis:{type:'category',data:labels,axisLabel:{rotate:45}},
      yAxis:{type:'value',axisLabel:{formatter:v=>m.special==='refundRate'?v+'%':fmt(v)}},
      dataZoom:[{type:'slider',bottom:10,height:20}],
      series
    },{notMerge:true});
  }

  // Stacked area
  const c2 = getChart('chartStack');
  if(c2) {
    const wm = weeklyMap('成交','总成交','成交金额',d);
    c2.setOption({
      tooltip:{trigger:'axis'},
      legend:{data:ap,top:0,textStyle:{color:'#4a4a6a'}},
      grid:{left:60,right:20,top:40,bottom:30},
      xAxis:{type:'category',data:labels,axisLabel:{rotate:45}},
      yAxis:{type:'value',axisLabel:{formatter:v=>fmt(v)}},
      series:ap.map(p => ({
        name:p,type:'line',stack:'total',areaStyle:{opacity:.4},smooth:true,symbol:'none',
        data:d.map(dt=>wm[dt]?.[p]||0),
        lineStyle:{color:C(p)},itemStyle:{color:C(p)},areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:C(p)+'66'},{offset:1,color:C(p)+'10'}])}
      }))
    },{notMerge:true});
  }

  // WoW bar
  const c3 = getChart('chartWow');
  if(c3 && d.length > 1) {
    const wm = weeklyMap('成交','总成交','成交金额',d);
    const wowData = d.slice(1).map((dt,i) => {
      let cur=0, prev=0;
      ap.forEach(p => { cur += wm[dt]?.[p]||0; prev += wm[d[i]]?.[p]||0; });
      return prev>0 ? +((cur-prev)/prev*100).toFixed(1) : 0;
    });
    c3.setOption({
      tooltip:{trigger:'axis',formatter:p=>p[0].name+'<br/>环比: '+p[0].value+'%'},
      grid:{left:50,right:20,top:20,bottom:30},
      xAxis:{type:'category',data:d.slice(1).map(x=>x.slice(5)),axisLabel:{rotate:45}},
      yAxis:{type:'value',axisLabel:{formatter:v=>v+'%'}},
      series:[{
        type:'bar',
        data:wowData.map(v=>({value:v,itemStyle:{color:v>=0?'#10b981':'#ef4444'}})),
        barMaxWidth:30,itemStyle:{borderRadius:[4,4,0,0]}
      }]
    },{notMerge:true});
  }
}

// ===== 6. PLATFORM ACCORDIONS =====
function renderAccordions() {
  const container = document.getElementById('accordionContainer');
  container.innerHTML = '';
  const d = STATE.dates, ap = activePlats();

  ap.forEach(p => {
    const gross = sumFiltered(p,'成交','总成交','成交金额',d);
    const net = sumFiltered(p,'成交','净成交','成交金额',d);
    const ref = sumFiltered(p,'成交','退款','退款金额',d);
    if(gross===0 && net===0) return;

    const acc = document.createElement('div');
    acc.className = 'accordion' + (STATE.expandedPlatform===p?' open':'');
    const isOpen = STATE.expandedPlatform===p;

    const trendId = 'accTrend_'+p.replace(/[^a-zA-Z0-9\u4e00-\u9fff]/g,'');
    const chId = 'accCh_'+p.replace(/[^a-zA-Z0-9\u4e00-\u9fff]/g,'');

    acc.innerHTML = `
      <div class="accordion-header" onclick="toggleAccordion('${p}',this.parentElement)">
        <div class="plat-icon" style="background:linear-gradient(135deg,${COLORS[p][0]},${COLORS[p][1]})">${p[0]}</div>
        <div class="info">
          <div class="name">${p}</div>
          <div class="stats">总成交 ¥${fmt(gross)} · 净成交 ¥${fmt(net)} · 退款 ¥${fmt(ref)} (${pct(ref,gross)})</div>
        </div>
        <span class="arrow">▼</span>
      </div>
      <div class="accordion-body">
        <div class="accordion-inner">
          <div class="chart-row r2" style="margin-top:16px">
            <div class="chart-box"><h4>成交趋势</h4><div class="chart-sm" id="${trendId}"></div></div>
            <div class="chart-box"><h4>渠道构成</h4><div class="chart-sm" id="${chId}"></div></div>
          </div>
          <div class="chart-box" style="margin-top:12px"><h4>周数据</h4><div class="data-table-wrap" id="accTbl_${trendId}"></div></div>
        </div>
      </div>`;
    container.appendChild(acc);

    if(isOpen) {
      setTimeout(() => drawAccordionCharts(p, trendId, chId, d), 50);
    }
  });
}

function toggleAccordion(plat, el) {
  const wasOpen = el.classList.contains('open');
  // close all
  document.querySelectorAll('.accordion').forEach(a=>a.classList.remove('open'));
  STATE.expandedPlatform = null;

  if(!wasOpen) {
    el.classList.add('open');
    STATE.expandedPlatform = plat;
    const trendId = 'accTrend_'+plat.replace(/[^a-zA-Z0-9\u4e00-\u9fff]/g,'');
    const chId = 'accCh_'+plat.replace(/[^a-zA-Z0-9\u4e00-\u9fff]/g,'');
    setTimeout(() => drawAccordionCharts(plat, trendId, chId, STATE.dates), 100);
  }
}

function drawAccordionCharts(plat, trendId, chId, d) {
  // Trend
  const c1 = getChart(trendId);
  if(c1) {
    const grossW={},netW={},refW={};
    RAW.filter(r=>r['平台']===plat&&r['指标大类']==='成交'&&d.includes(r['开始日期'])).forEach(r=>{
      if(r['一级对象']==='总成交') grossW[r['开始日期']]=r['数值'];
      if(r['一级对象']==='净成交') netW[r['开始日期']]=r['数值'];
      if(r['一级对象']==='退款') refW[r['开始日期']]=r['数值'];
    });
    c1.setOption({
      tooltip:{trigger:'axis'},
      legend:{data:['总成交','净成交','退款'],top:0,textStyle:{color:'#4a4a6a'}},
      grid:{left:60,right:20,top:36,bottom:30},
      xAxis:{type:'category',data:d.map(x=>x.slice(5)),axisLabel:{rotate:45}},
      yAxis:{type:'value',axisLabel:{formatter:v=>fmt(v)}},
      series:[
        {name:'总成交',type:'line',smooth:true,data:d.map(dt=>grossW[dt]||null),lineStyle:{color:C(plat),width:2.5},itemStyle:{color:C(plat)},connectNulls:true},
        {name:'净成交',type:'line',smooth:true,data:d.map(dt=>netW[dt]||null),lineStyle:{color:C(plat),width:1.5,type:'dashed'},itemStyle:{color:C(plat)+'88'},connectNulls:true},
        {name:'退款',type:'bar',data:d.map(dt=>refW[dt]||null),itemStyle:{color:'#ef444455'},barMaxWidth:16}
      ]
    });
  }

  // Channel donut
  const c2 = getChart(chId);
  if(c2) {
    const chMap = {};
    RAW.filter(r=>r['平台']===plat&&r['指标大类']==='渠道细分'&&r['指标名称']==='成交金额'&&d.includes(r['开始日期']))
      .forEach(r=>{ chMap[r['一级对象']] = (chMap[r['一级对象']]||0) + (r['数值']||0); });
    const channels = Object.entries(chMap).filter(x=>x[1]>0).sort((a,b)=>b[1]-a[1]);
    const palette = ['#6366f1','#f472b6','#10b981','#f59e0b','#3b82f6','#06b6d4','#8b5cf6','#fb923c'];
    c2.setOption({
      tooltip:{trigger:'item',formatter:'{b}: ¥{c} ({d}%)'},
      legend:{orient:'vertical',right:10,top:'center',textStyle:{color:'#4a4a6a',fontSize:11}},
      series:[{
        type:'pie',radius:['40%','70%'],center:['35%','50%'],
        data:channels.map(([name,val],i)=>({name,value:val,itemStyle:{color:palette[i%palette.length]}})),
        label:{show:false},emphasis:{label:{show:true,fontSize:13,fontWeight:'bold'}}
      }]
    });
  }

  // Table
  const tblEl = document.getElementById('accTbl_'+trendId);
  if(tblEl) {
    const rows = PWS.filter(r=>r['平台']===plat&&d.includes(r['开始日期']));
    let html = '<table><tr><th>周</th><th class="num">总成交</th><th class="num">退款</th><th class="num">净成交</th><th class="num">自营</th><th class="num">合作</th><th class="num">付费</th><th class="num">支出</th></tr>';
    rows.forEach(r=>{
      html += `<tr><td>${r['周标签']||''}</td><td class="num">${fmtK(r['总成交'])}</td><td class="num neg">${fmtK(r['退款金额'])}</td><td class="num">${fmtK(r['净成交'])}</td><td class="num">${fmtK(r['自营成交'])}</td><td class="num">${fmtK(r['合作成交'])}</td><td class="num">${fmtK(r['付费成交'])}</td><td class="num neg">${fmtK(r['支出合计'])}</td></tr>`;
    });
    html += '</table>';
    tblEl.innerHTML = html;
  }
}

// ===== 7. ADS =====
function renderAds() {
  const d = STATE.dates, ap = activePlats();

  // KPI
  const xhsCost = sumFiltered('小红书','投放','付费','消耗金额',d);
  const xhsRev = sumFiltered('小红书','投放','付费','成交金额',d);
  const dyCost = sumFiltered('抖店','付费','支出合计','支出金额',d);
  const dyRev = sumFiltered('抖店','付费','付费成交合计','成交金额',d);
  const tbCost = sumFiltered('淘宝','费用','总支出','支出金额',d);
  const totalSpend = xhsCost + dyCost + tbCost;
  const totalRev = xhsRev + dyRev;

  document.getElementById('adsKpi').innerHTML = `
    <div class="kpi-card"><div class="label">总投放消耗</div><div class="val" style="color:#f97316">¥${fmt(totalSpend)}</div></div>
    <div class="kpi-card"><div class="label">总付费成交</div><div class="val" style="color:#10b981">¥${fmt(totalRev)}</div></div>
    <div class="kpi-card"><div class="label">综合ROI</div><div class="val" style="color:#6366f1">${totalSpend>0?(totalRev/totalSpend).toFixed(2):'–'}</div></div>
  `;

  renderSankey(d, ap);
  renderAdsXhs(d);
  renderAdsDy(d);
  renderAdsTb(d);
  renderCalendar(d, ap);
}

function renderSankey(d, ap) {
  const c = getChart('chartSankey'); if(!c) return;

  const nodes = new Set(['总预算']);
  const links = [];

  ap.forEach(p => {
    // Platform level costs
    let platCost = 0;
    if(p === '小红书') platCost = sumFiltered(p,'投放','付费','消耗金额',d);
    else if(p === '抖店') platCost = sumFiltered(p,'付费','支出合计','支出金额',d);
    else if(p === '淘宝') platCost = sumFiltered(p,'费用','总支出','支出金额',d);
    if(platCost <= 0) return;

    nodes.add(p);
    links.push({source:'总预算',target:p,value:platCost});

    // Channel breakdown for revenue
    const chMap = {};
    RAW.filter(r=>r['平台']===p&&r['指标大类']==='渠道细分'&&r['指标名称']==='成交金额'&&d.includes(r['开始日期']))
      .forEach(r=>{ chMap[r['一级对象']] = (chMap[r['一级对象']]||0) + (r['数值']||0); });
    Object.entries(chMap).filter(x=>x[1]>0).sort((a,b)=>b[1]-a[1]).slice(0,5).forEach(([ch,val])=>{
      const chNode = p+'·'+ch;
      nodes.add(chNode);
      links.push({source:p,target:chNode,value:val});
    });
  });

  if(links.length === 0) { c.clear(); return; }

  c.setOption({
    tooltip:{trigger:'item'},
    series:[{
      type:'sankey',
      data:[...nodes].map(n=>({name:n,itemStyle:{color:COLORS[n]?.[0] || (n==='总预算'?'#6366f1':'#94a3b8')}})),
      links,
      emphasis:{focus:'adjacency'},
      lineStyle:{color:'gradient',curveness:0.5},
      label:{color:'#1a1a2e',fontSize:11},
      nodeWidth:20,nodeGap:12,layoutIterations:32
    }]
  });
}

function renderAdsXhs(d) {
  const c = getChart('chartAdsXhs'); if(!c) return;
  const data = RAW.filter(r=>r['平台']==='小红书'&&r['指标大类']==='投放'&&r['一级对象']==='付费'&&d.includes(r['开始日期']));
  const byDate = {};
  data.forEach(r=>{ if(!byDate[r['开始日期']]) byDate[r['开始日期']]={}; byDate[r['开始日期']][r['指标名称']]=r['数值']; });
  const dates = Object.keys(byDate).sort();
  c.setOption({
    tooltip:{trigger:'axis'},
    legend:{top:0,textStyle:{color:'#4a4a6a',fontSize:11}},
    grid:{left:50,right:50,top:36,bottom:30},
    xAxis:{type:'category',data:dates.map(x=>x.slice(5)),axisLabel:{rotate:45}},
    yAxis:[{type:'value',axisLabel:{formatter:v=>fmt(v)}},{type:'value',position:'right',axisLabel:{formatter:v=>v.toFixed(1),color:'#10b981'}}],
    series:[
      {name:'成交',type:'bar',data:dates.map(dt=>byDate[dt]?.['成交金额']||0),itemStyle:{color:'#ff2d55'},barMaxWidth:14},
      {name:'消耗',type:'bar',data:dates.map(dt=>byDate[dt]?.['消耗金额']||0),itemStyle:{color:'#ff6b8a88'},barMaxWidth:14},
      {name:'投产',type:'line',yAxisIndex:1,data:dates.map(dt=>byDate[dt]?.['投产']||null),lineStyle:{color:'#10b981',width:2},itemStyle:{color:'#10b981'},smooth:true,connectNulls:true}
    ]
  },{notMerge:true});
}

function renderAdsDy(d) {
  const c = getChart('chartAdsDy'); if(!c) return;
  const accounts = ['官号','店播','达人（小蓝）','马老师'];
  const palette = ['#1e90ff','#00d4ff','#818cf8','#a78bfa'];
  const byDate = {};
  RAW.filter(r=>r['平台']==='抖店'&&r['指标大类']==='付费'&&accounts.includes(r['一级对象'])&&r['指标名称']==='成交金额'&&d.includes(r['开始日期']))
    .forEach(r=>{ if(!byDate[r['开始日期']]) byDate[r['开始日期']]={}; byDate[r['开始日期']][r['一级对象']]=r['数值']; });
  const dates = Object.keys(byDate).sort();
  c.setOption({
    tooltip:{trigger:'axis'},
    legend:{top:0,textStyle:{color:'#4a4a6a',fontSize:11}},
    grid:{left:50,right:20,top:36,bottom:30},
    xAxis:{type:'category',data:dates.map(x=>x.slice(5)),axisLabel:{rotate:45}},
    yAxis:{type:'value',axisLabel:{formatter:v=>fmt(v)}},
    series:accounts.map((a,i)=>({
      name:a,type:'line',smooth:true,
      data:dates.map(dt=>byDate[dt]?.[a]||null),
      lineStyle:{color:palette[i],width:2},itemStyle:{color:palette[i]},connectNulls:true
    }))
  },{notMerge:true});
}

function renderAdsTb(d) {
  const c = getChart('chartAdsTb'); if(!c) return;
  const byDate = {};
  RAW.filter(r=>r['平台']==='淘宝'&&r['指标大类']==='费用'&&d.includes(r['开始日期']))
    .forEach(r=>{ if(!byDate[r['开始日期']]) byDate[r['开始日期']]={}; byDate[r['开始日期']][r['一级对象']]=r['数值']; });
  const dates = Object.keys(byDate).sort();
  c.setOption({
    tooltip:{trigger:'axis'},
    legend:{top:0,textStyle:{color:'#4a4a6a',fontSize:11}},
    grid:{left:50,right:20,top:36,bottom:30},
    xAxis:{type:'category',data:dates.map(x=>x.slice(5)),axisLabel:{rotate:45}},
    yAxis:{type:'value',axisLabel:{formatter:v=>fmt(v)}},
    series:[
      {name:'付费支出',type:'bar',stack:'cost',data:dates.map(dt=>byDate[dt]?.['付费支出']||0),itemStyle:{color:'#ff6a00'},barMaxWidth:20},
      {name:'淘客支出',type:'bar',stack:'cost',data:dates.map(dt=>byDate[dt]?.['淘客支出']||0),itemStyle:{color:'#ffab40'},barMaxWidth:20},
    ]
  },{notMerge:true});
}

function renderCalendar(d, ap) {
  const c = getChart('chartCalendar'); if(!c) return;
  // Weekly ROI: totalRev / totalSpend per week
  const calData = [];
  d.forEach(dt => {
    let rev=0, spend=0;
    ap.forEach(p => {
      rev += sumFiltered(p,'成交','总成交','成交金额',[dt]);
      spend += sumFiltered(p,'费用','总支出','支出金额',[dt]) + sumFiltered(p,'付费','支出合计','支出金额',[dt]) + sumFiltered(p,'投放','付费','消耗金额',[dt]);
    });
    const roi = spend>0 ? +(rev/spend).toFixed(2) : 0;
    calData.push([dt, roi]);
  });

  // Determine year range
  const years = [...new Set(d.map(x=>x.slice(0,4)))].sort();
  const calendarList = years.map((y,i)=>({
    top: 60+i*160, left:60, right:60, cellSize:['auto',18],
    range:y, yearLabel:{color:'#4a4a6a'}, dayLabel:{color:'#8888a4',fontSize:10}, monthLabel:{color:'#4a4a6a'}
  }));

  c.setOption({
    tooltip:{formatter:p=>p.value?p.value[0]+' ROI: '+p.value[1]:'' },
    visualMap:{min:0,max:Math.max(...calData.map(x=>x[1]),5),inRange:{color:['#ebedf0','#c6e48b','#7bc96f','#239a3b','#196127']},orient:'horizontal',left:'center',top:10,textStyle:{color:'#4a4a6a'}},
    calendar:calendarList,
    series:years.map((y,i)=>({
      type:'heatmap',coordinateSystem:'calendar',calendarIndex:i,
      data:calData.filter(x=>x[0].startsWith(y))
    }))
  },{notMerge:true});
}

// ===== 8. TABLE =====
let tableSortCol = null, tableSortAsc = true;
function renderTable() {
  const d = STATE.dates, ap = activePlats();
  const rows = PWS.filter(r=>ap.includes(r['平台'])&&d.includes(r['开始日期']));

  const cols = ['周标签','平台','总成交','退款金额','净成交','自营成交','合作成交','付费成交','支出合计'];
  const numCols = new Set(['总成交','退款金额','净成交','自营成交','合作成交','付费成交','支出合计']);

  let sorted = [...rows];
  if(tableSortCol !== null) {
    const col = cols[tableSortCol];
    sorted.sort((a,b) => {
      let va=a[col], vb=b[col];
      if(va==null) va = numCols.has(col)?-Infinity:'';
      if(vb==null) vb = numCols.has(col)?-Infinity:'';
      if(numCols.has(col)) return tableSortAsc ? va-vb : vb-va;
      return tableSortAsc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
    });
  }

  let html = '<table><tr>';
  cols.forEach((c,i) => {
    const arrow = tableSortCol===i ? (tableSortAsc?' ↑':' ↓') : '';
    html += `<th class="${numCols.has(c)?'num':''}" onclick="sortTable(${i})">${c}${arrow}</th>`;
  });
  html += '</tr>';
  sorted.forEach(r => {
    html += '<tr>';
    cols.forEach(c => {
      const v = r[c];
      if(numCols.has(c)) {
        const cls = c==='退款金额'||c==='支出合计'?'num neg':'num';
        html += `<td class="${cls}">${fmtK(v)}</td>`;
      } else if(c==='平台') {
        html += `<td style="color:${C(v)};font-weight:600">${v||'-'}</td>`;
      } else {
        html += `<td>${v||'-'}</td>`;
      }
    });
    html += '</tr>';
  });
  html += '</table>';
  document.getElementById('fullTable').innerHTML = html;
}

function sortTable(colIdx) {
  if(tableSortCol === colIdx) tableSortAsc = !tableSortAsc;
  else { tableSortCol = colIdx; tableSortAsc = true; }
  renderTable();
}

// ===== RESIZE =====
window.addEventListener('resize', () => {
  Object.values(CHARTS).forEach(c => { try{c.resize()}catch(e){} });
});

// ===== INIT =====
initPlatFilter();
initTrendPills();
initSideNav();
setDateRange(0, document.querySelector('.pill[data-range="0"]'));
// Default to all data on load, then activate "全部"
document.querySelectorAll('.filter-bar .pill[data-range]').forEach(p=>p.classList.remove('active'));
document.querySelector('.pill[data-range="0"]').classList.add('active');
</script>
</body>
</html>"""

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"✓ {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")
