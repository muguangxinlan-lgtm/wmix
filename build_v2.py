#!/usr/bin/env python3
"""v2 电商分析看板 - 多视角、多Tab、时间滑块、平台深钻、投放专页"""
import sqlite3, json, os

DB = "/Users/wmix/Downloads/店铺每周数据汇总_2026-03-18.sqlite"
OUT = "/Users/wmix/wmixclaude/index.html"

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

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>电商数据看板</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#09090b;--bg2:#111114;--card:#18181b;--card2:#1f1f23;
  --border:#27272a;--border2:#3f3f46;
  --t1:#fafafa;--t2:#a1a1aa;--t3:#71717a;
  --accent:#818cf8;--accent2:#6366f1;
  --green:#4ade80;--red:#f87171;--orange:#fbbf24;--blue:#60a5fa;--pink:#f472b6;--cyan:#22d3ee;--purple:#a78bfa;
  --radius:10px;
}
body{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','PingFang SC','Hiragino Sans GB',sans-serif;background:var(--bg);color:var(--t1);font-size:14px;overflow-x:hidden}
a{color:var(--accent);text-decoration:none}

/* NAV */
.topbar{position:sticky;top:0;z-index:100;background:var(--bg2);border-bottom:1px solid var(--border);backdrop-filter:blur(12px);display:flex;align-items:center;padding:0 24px;height:56px;gap:8px}
.topbar .logo{font-size:16px;font-weight:700;margin-right:24px;white-space:nowrap}
.topbar .logo span{color:var(--accent)}
.nav-tabs{display:flex;gap:2px}
.nav-tab{padding:8px 18px;border-radius:8px;cursor:pointer;font-size:13px;font-weight:500;color:var(--t2);background:transparent;border:none;transition:all .15s}
.nav-tab:hover{color:var(--t1);background:var(--card)}
.nav-tab.active{color:var(--t1);background:var(--accent2)}

/* LAYOUT */
.page{display:none;padding:24px;max-width:1440px;margin:0 auto}
.page.active{display:block}
.row{display:flex;gap:16px;margin-bottom:16px;flex-wrap:wrap}
.col{flex:1;min-width:0}
.col-2{flex:0 0 calc(50% - 8px);min-width:300px}
.col-3{flex:0 0 calc(33.33% - 11px);min-width:280px}

/* CARDS */
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px;position:relative}
.card-sm{padding:16px}
.card h4{font-size:13px;font-weight:600;color:var(--t2);margin-bottom:12px;text-transform:uppercase;letter-spacing:.5px}
.card canvas{max-height:320px}

/* KPI */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:20px}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:16px 20px}
.kpi .label{font-size:12px;color:var(--t3);margin-bottom:4px}
.kpi .val{font-size:24px;font-weight:700;font-variant-numeric:tabular-nums}
.kpi .sub{font-size:11px;margin-top:2px}
.kpi .up{color:var(--green)}.kpi .down{color:var(--red)}.kpi .neutral{color:var(--t3)}

/* RANGE SLIDER */
.range-wrap{margin-bottom:20px;background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:16px 20px}
.range-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.range-header .title{font-size:13px;font-weight:600;color:var(--t2)}
.range-header .info{font-size:12px;color:var(--t3)}
.range-presets{display:flex;gap:6px;margin-bottom:12px}
.range-btn{padding:4px 12px;border-radius:6px;font-size:12px;cursor:pointer;background:var(--bg2);color:var(--t2);border:1px solid var(--border);transition:all .15s}
.range-btn:hover,.range-btn.active{background:var(--accent2);color:#fff;border-color:var(--accent2)}
.dual-range{position:relative;height:36px;margin:0 8px}
.dual-range input[type=range]{-webkit-appearance:none;position:absolute;width:100%;height:4px;top:16px;background:transparent;pointer-events:none}
.dual-range input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:18px;height:18px;border-radius:50%;background:var(--accent);border:2px solid var(--bg);cursor:pointer;pointer-events:all;position:relative;z-index:2}
.range-track{position:absolute;top:16px;height:4px;width:100%;background:var(--border);border-radius:2px}
.range-fill{position:absolute;top:16px;height:4px;background:var(--accent2);border-radius:2px}
.range-labels{display:flex;justify-content:space-between;font-size:11px;color:var(--t3);margin-top:4px}

/* COMPARE */
.compare-bar{display:flex;gap:8px;align-items:center;margin-bottom:16px;flex-wrap:wrap}
.compare-bar label{font-size:12px;color:var(--t3)}
.compare-bar select,.compare-bar input{background:var(--card2);color:var(--t1);border:1px solid var(--border);border-radius:6px;padding:6px 10px;font-size:12px}

/* PLATFORM SECTIONS */
.platform-section{margin-bottom:32px}
.platform-header{display:flex;align-items:center;gap:12px;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--border)}
.platform-dot{width:12px;height:12px;border-radius:50%}
.platform-header h3{font-size:18px;font-weight:700}
.platform-header .summary{font-size:13px;color:var(--t2);margin-left:auto}

/* TABLE */
.tbl-wrap{overflow-x:auto;max-height:500px;overflow-y:auto}
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;padding:8px 10px;border-bottom:2px solid var(--border);color:var(--t3);font-weight:600;position:sticky;top:0;background:var(--card);white-space:nowrap}
td{padding:6px 10px;border-bottom:1px solid var(--border);white-space:nowrap}
tr:hover td{background:rgba(99,102,241,.06)}
.num{text-align:right;font-variant-numeric:tabular-nums}
.pos{color:var(--green)}.neg{color:var(--red)}

/* TABS inner */
.inner-tabs{display:flex;gap:4px;margin-bottom:16px;border-bottom:1px solid var(--border);padding-bottom:0}
.inner-tab{padding:8px 16px;font-size:13px;cursor:pointer;color:var(--t3);border-bottom:2px solid transparent;transition:all .15s;background:none;border-top:none;border-left:none;border-right:none}
.inner-tab:hover{color:var(--t1)}
.inner-tab.active{color:var(--accent);border-bottom-color:var(--accent)}

/* WEEK SNAPSHOT */
.week-card{background:var(--card2);border:1px solid var(--border);border-radius:var(--radius);padding:16px;text-align:center}
.week-card .plat{font-size:12px;font-weight:600;margin-bottom:8px}
.week-card .big{font-size:22px;font-weight:700;margin-bottom:4px}
.week-card .detail{font-size:11px;color:var(--t3);line-height:1.8}
.week-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:20px}

/* Tooltip badge */
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}
.badge-green{background:rgba(74,222,128,.15);color:var(--green)}
.badge-red{background:rgba(248,113,113,.15);color:var(--red)}
.badge-blue{background:rgba(96,165,250,.15);color:var(--blue)}

@media(max-width:768px){
  .col-2,.col-3{flex:0 0 100%}
  .topbar{padding:0 12px}.page{padding:16px}
  .kpi-grid{grid-template-columns:repeat(2,1fr)}
}
</style>
</head>
<body>

<div class="topbar">
  <div class="logo"><span>◈</span> 电商数据看板</div>
  <div class="nav-tabs">
    <button class="nav-tab active" onclick="showPage('overview',this)">总览</button>
    <button class="nav-tab" onclick="showPage('trend',this)">趋势分析</button>
    <button class="nav-tab" onclick="showPage('platforms',this)">平台深钻</button>
    <button class="nav-tab" onclick="showPage('ads',this)">投放分析</button>
    <button class="nav-tab" onclick="showPage('compare',this)">对比</button>
  </div>
</div>

<!-- ====== PAGE: OVERVIEW ====== -->
<div class="page active" id="page-overview">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
    <div>
      <h2 style="font-size:20px;font-weight:700">最新一周快照</h2>
      <p style="font-size:13px;color:var(--t3)" id="latestWeekLabel"></p>
    </div>
    <div style="display:flex;gap:8px" id="overviewWeekBtns"></div>
  </div>
  <div class="kpi-grid" id="overviewKpi"></div>
  <div class="week-grid" id="weekPlatCards"></div>
  <div class="row">
    <div class="col-2 card"><h4>本周 vs 上周 各平台成交</h4><canvas id="ovWowBar"></canvas></div>
    <div class="col-2 card"><h4>本周成交构成</h4><canvas id="ovPie"></canvas></div>
  </div>
  <div class="card" style="margin-bottom:16px"><h4>累计成交排行</h4><canvas id="ovCumBar" style="max-height:200px"></canvas></div>
</div>

<!-- ====== PAGE: TREND ====== -->
<div class="page" id="page-trend">
  <h2 style="font-size:20px;font-weight:700;margin-bottom:20px">趋势分析</h2>
  <div class="range-wrap" id="trendRange">
    <div class="range-header">
      <span class="title">时间范围</span>
      <span class="info" id="trendRangeInfo"></span>
    </div>
    <div class="range-presets" id="trendPresets"></div>
    <div class="dual-range">
      <div class="range-track"></div>
      <div class="range-fill" id="trendFill"></div>
      <input type="range" id="trendMin" min="0" max="100" value="0">
      <input type="range" id="trendMax" min="0" max="100" value="100">
    </div>
    <div class="range-labels"><span id="trendLabelL"></span><span id="trendLabelR"></span></div>
  </div>
  <div class="inner-tabs" id="trendMetricTabs"></div>
  <div class="row">
    <div class="col card"><h4>各平台趋势</h4><canvas id="trendLine"></canvas></div>
  </div>
  <div class="row">
    <div class="col-2 card"><h4>堆叠面积</h4><canvas id="trendStack"></canvas></div>
    <div class="col-2 card"><h4>退款率趋势</h4><canvas id="trendRefund"></canvas></div>
  </div>
</div>

<!-- ====== PAGE: PLATFORMS ====== -->
<div class="page" id="page-platforms">
  <h2 style="font-size:20px;font-weight:700;margin-bottom:20px">平台深钻</h2>
  <div class="range-wrap" id="platRange">
    <div class="range-header">
      <span class="title">时间范围</span>
      <span class="info" id="platRangeInfo"></span>
    </div>
    <div class="range-presets" id="platPresets"></div>
    <div class="dual-range">
      <div class="range-track"></div>
      <div class="range-fill" id="platFill"></div>
      <input type="range" id="platMin" min="0" max="100" value="0">
      <input type="range" id="platMax" min="0" max="100" value="100">
    </div>
    <div class="range-labels"><span id="platLabelL"></span><span id="platLabelR"></span></div>
  </div>
  <div id="platformSections"></div>
</div>

<!-- ====== PAGE: ADS ====== -->
<div class="page" id="page-ads">
  <h2 style="font-size:20px;font-weight:700;margin-bottom:20px">投放分析</h2>
  <div class="range-wrap" id="adsRange">
    <div class="range-header">
      <span class="title">时间范围</span>
      <span class="info" id="adsRangeInfo"></span>
    </div>
    <div class="range-presets" id="adsPresets"></div>
    <div class="dual-range">
      <div class="range-track"></div>
      <div class="range-fill" id="adsFill"></div>
      <input type="range" id="adsMin" min="0" max="100" value="0">
      <input type="range" id="adsMax" min="0" max="100" value="100">
    </div>
    <div class="range-labels"><span id="adsLabelL"></span><span id="adsLabelR"></span></div>
  </div>

  <div class="kpi-grid" id="adsKpi"></div>

  <!-- XHS -->
  <div class="platform-section">
    <div class="platform-header"><div class="platform-dot" style="background:#ff4757"></div><h3>小红书 · 付费投放</h3></div>
    <div class="row">
      <div class="col-2 card"><h4>成交 vs 消耗 vs 投产</h4><canvas id="adsXhsMain"></canvas></div>
      <div class="col-2 card"><h4>店播投放</h4><canvas id="adsXhsShop"></canvas></div>
    </div>
  </div>

  <!-- DOUYIN -->
  <div class="platform-section">
    <div class="platform-header"><div class="platform-dot" style="background:#1e90ff"></div><h3>抖店 · 付费投放</h3></div>
    <div class="row">
      <div class="col card"><h4>各账号 · 付费成交趋势</h4><canvas id="adsDouyinLine"></canvas></div>
    </div>
    <div class="row">
      <div class="col-2 card"><h4>各账号累计效率 (成交 / 消耗 / ROI)</h4><canvas id="adsDouyinBar"></canvas></div>
      <div class="col-2 card"><h4>自营付费 vs 自营自然流</h4><canvas id="adsDouyinSelf"></canvas></div>
    </div>
    <div class="row">
      <div class="col card"><h4>支出合计趋势</h4><canvas id="adsDouyinCost"></canvas></div>
    </div>
  </div>

  <!-- TAOBAO -->
  <div class="platform-section">
    <div class="platform-header"><div class="platform-dot" style="background:#ff8c00"></div><h3>淘宝 · 费用 & 投放</h3></div>
    <div class="row">
      <div class="col-2 card"><h4>费用构成趋势</h4><canvas id="adsTbCost"></canvas></div>
      <div class="col-2 card"><h4>付费计划投产趋势</h4><canvas id="adsTbRoi"></canvas></div>
    </div>
    <div class="row">
      <div class="col card"><h4>付费计划明细</h4><div class="tbl-wrap" id="adsTbTable"></div></div>
    </div>
  </div>
</div>

<!-- ====== PAGE: COMPARE ====== -->
<div class="page" id="page-compare">
  <h2 style="font-size:20px;font-weight:700;margin-bottom:20px">周对比</h2>
  <div class="compare-bar">
    <label>周 A:</label><select id="cmpWeekA"></select>
    <label style="margin-left:12px">周 B:</label><select id="cmpWeekB"></select>
    <label style="margin-left:12px">平台:</label><select id="cmpPlatform"><option value="all">全部</option></select>
    <button class="range-btn" onclick="runCompare()" style="margin-left:8px">对比</button>
  </div>
  <div class="kpi-grid" id="cmpKpi"></div>
  <div class="row">
    <div class="col-2 card"><h4>成交对比</h4><canvas id="cmpBar"></canvas></div>
    <div class="col-2 card"><h4>渠道对比</h4><canvas id="cmpChannel"></canvas></div>
  </div>
  <div class="card"><h4>明细对比</h4><div class="tbl-wrap" id="cmpTable"></div></div>
</div>

<script>
// ===== DATA =====
const RAW = """ + structured_json + """;
const PWS = """ + pws_json + """;

const COLORS = {
  '小红书':'#ff4757','抖店':'#1e90ff','淘宝':'#ff8c00',
  '微信':'#2ed573','B站':'#00b8d4','天猫':'#a855f7'
};
const PLATS = ['抖店','小红书','淘宝','微信','B站','天猫'];
const ALL_DATES = [...new Set(RAW.map(r=>r['开始日期']))].sort();
const ALL_END_DATES = {};
RAW.forEach(r => { ALL_END_DATES[r['开始日期']] = r['结束日期']; });

// ===== HELPERS =====
function fmt(n){if(n==null||isNaN(n))return'-';if(Math.abs(n)>=10000)return(n/10000).toFixed(2)+'万';return n.toLocaleString('zh-CN',{maximumFractionDigits:0})}
function fmtK(n){if(n==null||isNaN(n))return'-';return n.toLocaleString('zh-CN',{maximumFractionDigits:0})}
function pct(a,b){if(!b)return'-';return(a/b*100).toFixed(1)+'%'}
function delta(a,b){if(!b)return{text:'-',cls:'neutral'};const d=(a-b)/b*100;return{text:(d>=0?'+':'')+d.toFixed(1)+'%',cls:d>=0?'up':'down'}}

function getVal(data, plat, cat, obj, metric, dates) {
  return data.filter(r => r['平台']===plat && r['指标大类']===cat && r['一级对象']===obj && r['指标名称']===metric && (!dates || dates.includes(r['开始日期'])));
}
function sumVal(data, plat, cat, obj, metric, dates) {
  return getVal(data, plat, cat, obj, metric, dates).reduce((s,r)=>s+(r['数值']||0),0);
}
function weeklyByPlatform(cat, obj, metric, dates) {
  const m = {};
  RAW.filter(r=>r['指标大类']===cat&&r['一级对象']===obj&&r['指标名称']===metric&&dates.includes(r['开始日期']))
    .forEach(r=>{ if(!m[r['开始日期']])m[r['开始日期']]={};m[r['开始日期']][r['平台']]=r['数值']; });
  return m;
}

// chart defaults
Chart.defaults.color = '#71717a';
Chart.defaults.borderColor = '#27272a';
Chart.defaults.font.family = '-apple-system,BlinkMacSystemFont,PingFang SC,sans-serif';
Chart.defaults.font.size = 11;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyleWidth = 8;
Chart.defaults.plugins.legend.labels.boxHeight = 6;

const charts = {};
function makeChart(id, cfg) {
  if(charts[id]) charts[id].destroy();
  charts[id] = new Chart(document.getElementById(id), cfg);
  return charts[id];
}
function lineDataset(label, data, color, opts={}) {
  return {label, data, borderColor:color, backgroundColor:'transparent', tension:.35, borderWidth:2, pointRadius:0, pointHoverRadius:4, ...opts};
}
function areaDataset(label, data, color) {
  return {label, data, borderColor:color, backgroundColor:color+'33', fill:true, tension:.35, borderWidth:1.5, pointRadius:0};
}
function barDataset(label, data, color) {
  return {label, data, backgroundColor:color+'bb', borderRadius:4, borderSkipped:false};
}

// ===== NAVIGATION =====
function showPage(id, btn) {
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(b=>b.classList.remove('active'));
  document.getElementById('page-'+id).classList.add('active');
  if(btn) btn.classList.add('active');
  if(id==='overview') renderOverview();
  if(id==='trend') renderTrend();
  if(id==='platforms') renderPlatforms();
  if(id==='ads') renderAds();
  if(id==='compare') initCompare();
}

// ===== RANGE SLIDER =====
function setupRange(prefix, onchange) {
  const minR = document.getElementById(prefix+'Min');
  const maxR = document.getElementById(prefix+'Max');
  const fill = document.getElementById(prefix+'Fill');
  const labelL = document.getElementById(prefix+'LabelL');
  const labelR = document.getElementById(prefix+'LabelR');
  const info = document.getElementById(prefix+'RangeInfo');
  const presets = document.getElementById(prefix+'Presets');

  minR.max = maxR.max = ALL_DATES.length - 1;
  minR.value = 0; maxR.value = ALL_DATES.length - 1;

  function update() {
    let lo = +minR.value, hi = +maxR.value;
    if(lo > hi) { [minR.value, maxR.value] = [hi, lo]; lo=hi; hi=+maxR.value; }
    const pctL = lo/(ALL_DATES.length-1)*100, pctR = hi/(ALL_DATES.length-1)*100;
    fill.style.left = pctL+'%'; fill.style.width = (pctR-pctL)+'%';
    labelL.textContent = ALL_DATES[lo]; labelR.textContent = ALL_DATES[hi];
    info.textContent = ALL_DATES[lo] + ' ~ ' + (ALL_END_DATES[ALL_DATES[hi]]||ALL_DATES[hi]) + '  (' + (hi-lo+1) + '周)';
    onchange(ALL_DATES.slice(lo, hi+1));
  }
  minR.oninput = maxR.oninput = update;

  // presets
  const presetCfg = [
    {label:'最近4周', n:4},{label:'最近8周', n:8},{label:'最近13周', n:13},
    {label:'最近26周', n:26},{label:'全部', n:ALL_DATES.length}
  ];
  presets.innerHTML = '';
  presetCfg.forEach(p => {
    const btn = document.createElement('button');
    btn.className = 'range-btn' + (p.n===ALL_DATES.length?' active':'');
    btn.textContent = p.label;
    btn.onclick = () => {
      presets.querySelectorAll('.range-btn').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      minR.value = Math.max(0, ALL_DATES.length - p.n);
      maxR.value = ALL_DATES.length - 1;
      update();
    };
    presets.appendChild(btn);
  });

  update();
  return {setRange: (lo,hi) => { minR.value=lo; maxR.value=hi; update(); }};
}

// ==================== OVERVIEW ====================
let ovDates;
function renderOverview() {
  const latest = ALL_DATES[ALL_DATES.length-1];
  const prev = ALL_DATES[ALL_DATES.length-2];
  ovDates = [latest];

  document.getElementById('latestWeekLabel').textContent = latest + ' ~ ' + (ALL_END_DATES[latest]||'');

  // week selector buttons
  const btnsEl = document.getElementById('overviewWeekBtns');
  btnsEl.innerHTML = '';
  ALL_DATES.slice(-5).reverse().forEach((d,i) => {
    const b = document.createElement('button');
    b.className = 'range-btn'+(i===0?' active':'');
    b.textContent = d.slice(5);
    b.onclick = () => {
      btnsEl.querySelectorAll('.range-btn').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      ovDates = [d];
      document.getElementById('latestWeekLabel').textContent = d + ' ~ ' + (ALL_END_DATES[d]||'');
      renderOverviewContent(d, ALL_DATES[ALL_DATES.indexOf(d)-1]);
    };
    btnsEl.appendChild(b);
  });
  renderOverviewContent(latest, prev);
}

function renderOverviewContent(curDate, prevDate) {
  // KPI
  let totalCur=0, totalPrev=0, netCur=0, refundCur=0;
  PLATS.forEach(p => {
    totalCur += sumVal(RAW,p,'成交','总成交','成交金额',[curDate]);
    totalPrev += sumVal(RAW,p,'成交','总成交','成交金额',[prevDate]);
    netCur += sumVal(RAW,p,'成交','净成交','成交金额',[curDate]);
    refundCur += sumVal(RAW,p,'成交','退款','退款金额',[curDate]);
  });
  const d = delta(totalCur, totalPrev);
  const refRate = totalCur>0 ? (refundCur/totalCur*100).toFixed(1)+'%' : '-';

  // cumulative
  let cumTotal=0, cumNet=0;
  PLATS.forEach(p => {
    cumTotal += sumVal(RAW,p,'成交','总成交','成交金额',ALL_DATES);
    cumNet += sumVal(RAW,p,'成交','净成交','成交金额',ALL_DATES);
  });

  document.getElementById('overviewKpi').innerHTML = `
    <div class="kpi"><div class="label">本周总成交</div><div class="val" style="color:var(--green)">${fmt(totalCur)}</div><div class="sub ${d.cls}">环比 ${d.text}</div></div>
    <div class="kpi"><div class="label">本周净成交</div><div class="val" style="color:var(--blue)">${fmt(netCur)}</div></div>
    <div class="kpi"><div class="label">本周退款</div><div class="val" style="color:var(--red)">${fmt(refundCur)}</div><div class="sub neutral">退款率 ${refRate}</div></div>
    <div class="kpi"><div class="label">累计总成交</div><div class="val" style="color:var(--t1)">${fmt(cumTotal)}</div></div>
    <div class="kpi"><div class="label">累计净成交</div><div class="val" style="color:var(--t2)">${fmt(cumNet)}</div></div>
  `;

  // platform cards
  let cardsHtml = '';
  PLATS.forEach(p => {
    const gross = sumVal(RAW,p,'成交','总成交','成交金额',[curDate]);
    const net = sumVal(RAW,p,'成交','净成交','成交金额',[curDate]);
    const ref = sumVal(RAW,p,'成交','退款','退款金额',[curDate]);
    const prevGross = sumVal(RAW,p,'成交','总成交','成交金额',[prevDate]);
    const dd = delta(gross, prevGross);
    if(gross===0 && net===0) return;
    cardsHtml += `<div class="week-card">
      <div class="plat" style="color:${COLORS[p]}">${p}</div>
      <div class="big">${fmt(gross)}</div>
      <div class="detail">
        净成交 ${fmt(net)}<br>退款 ${fmt(ref)}<br>
        <span class="${dd.cls}">环比 ${dd.text}</span>
      </div>
    </div>`;
  });
  document.getElementById('weekPlatCards').innerHTML = cardsHtml;

  // WoW bar
  const platLabels = PLATS.filter(p => sumVal(RAW,p,'成交','总成交','成交金额',[curDate])>0 || sumVal(RAW,p,'成交','总成交','成交金额',[prevDate])>0);
  makeChart('ovWowBar', {
    type:'bar',
    data:{
      labels: platLabels,
      datasets:[
        barDataset('本周', platLabels.map(p=>sumVal(RAW,p,'成交','总成交','成交金额',[curDate])), '#818cf8'),
        barDataset('上周', platLabels.map(p=>sumVal(RAW,p,'成交','总成交','成交金额',[prevDate])), '#3f3f46'),
      ]
    },
    options:{responsive:true,plugins:{legend:{labels:{color:'#a1a1aa'}}},scales:{x:{grid:{display:false}},y:{ticks:{callback:v=>fmt(v)}}}}
  });

  // Pie
  const pieData = PLATS.map(p=>sumVal(RAW,p,'成交','总成交','成交金额',[curDate])).filter(v=>v>0);
  const pieLabels = PLATS.filter(p=>sumVal(RAW,p,'成交','总成交','成交金额',[curDate])>0);
  makeChart('ovPie', {
    type:'doughnut',
    data:{labels:pieLabels, datasets:[{data:pieData, backgroundColor:pieLabels.map(p=>COLORS[p]), borderWidth:0, borderRadius:2}]},
    options:{responsive:true,cutout:'60%',plugins:{legend:{position:'right',labels:{color:'#a1a1aa',padding:10}}}}
  });

  // Cumulative bar
  const cumData = PLATS.map(p=>({p, v:sumVal(RAW,p,'成交','总成交','成交金额',ALL_DATES)})).filter(x=>x.v>0).sort((a,b)=>b.v-a.v);
  makeChart('ovCumBar', {
    type:'bar',
    data:{labels:cumData.map(x=>x.p), datasets:[{data:cumData.map(x=>x.v), backgroundColor:cumData.map(x=>COLORS[x.p]+'bb'), borderRadius:4}]},
    options:{indexAxis:'y',responsive:true,plugins:{legend:{display:false}},scales:{x:{ticks:{callback:v=>fmt(v)}},y:{grid:{display:false}}}}
  });
}

// ==================== TREND ====================
let trendDates = ALL_DATES;
const trendMetrics = [
  {label:'总成交', cat:'成交', obj:'总成交', metric:'成交金额'},
  {label:'净成交', cat:'成交', obj:'净成交', metric:'成交金额'},
  {label:'退款', cat:'成交', obj:'退款', metric:'退款金额'},
];
let trendMetricIdx = 0;

function renderTrend() {
  setupRange('trend', dates => { trendDates = dates; drawTrend(); });

  const tabsEl = document.getElementById('trendMetricTabs');
  tabsEl.innerHTML = '';
  trendMetrics.forEach((m,i) => {
    const b = document.createElement('button');
    b.className = 'inner-tab'+(i===0?' active':'');
    b.textContent = m.label;
    b.onclick = () => {
      tabsEl.querySelectorAll('.inner-tab').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      trendMetricIdx = i;
      drawTrend();
    };
    tabsEl.appendChild(b);
  });
  drawTrend();
}

function drawTrend() {
  const m = trendMetrics[trendMetricIdx];
  const wm = weeklyByPlatform(m.cat, m.obj, m.metric, trendDates);
  const labels = trendDates.map(d=>d.slice(5));

  // line
  makeChart('trendLine', {
    type:'line',
    data:{labels, datasets:PLATS.map(p=>lineDataset(p, trendDates.map(d=>wm[d]?.[p]||null), COLORS[p], {spanGaps:true}))},
    options:{responsive:true,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#a1a1aa'}}},scales:{x:{ticks:{maxRotation:45},grid:{display:false}},y:{ticks:{callback:v=>fmt(v)}}}}
  });

  // stacked area
  makeChart('trendStack', {
    type:'line',
    data:{labels, datasets:PLATS.map(p=>areaDataset(p, trendDates.map(d=>wm[d]?.[p]||0), COLORS[p]))},
    options:{responsive:true,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#a1a1aa'}}},scales:{x:{ticks:{maxRotation:45},grid:{display:false}},y:{stacked:true,ticks:{callback:v=>fmt(v)}}}}
  });

  // refund rate
  const revMap = weeklyByPlatform('成交','总成交','成交金额',trendDates);
  const refMap = weeklyByPlatform('成交','退款','退款金额',trendDates);
  makeChart('trendRefund', {
    type:'line',
    data:{labels, datasets:['抖店','小红书','淘宝'].map(p=>lineDataset(p, trendDates.map(d=>{
      const rev=revMap[d]?.[p], ref=refMap[d]?.[p];
      return(rev&&ref)?ref/rev*100:null;
    }), COLORS[p], {spanGaps:true}))},
    options:{responsive:true,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#a1a1aa'}}},scales:{x:{ticks:{maxRotation:45},grid:{display:false}},y:{ticks:{callback:v=>v.toFixed(0)+'%'}}}}
  });
}

// ==================== PLATFORMS ====================
let platDates = ALL_DATES;
function renderPlatforms() {
  setupRange('plat', dates => { platDates = dates; drawPlatforms(); });
  drawPlatforms();
}

function drawPlatforms() {
  const container = document.getElementById('platformSections');
  container.innerHTML = '';

  PLATS.forEach(plat => {
    const gross = sumVal(RAW,plat,'成交','总成交','成交金额',platDates);
    if(gross === 0) return;

    const net = sumVal(RAW,plat,'成交','净成交','成交金额',platDates);
    const ref = sumVal(RAW,plat,'成交','退款','退款金额',platDates);

    const sec = document.createElement('div');
    sec.className = 'platform-section';

    // channels for this platform
    const chMap = {};
    RAW.filter(r=>r['平台']===plat&&r['指标大类']==='渠道细分'&&r['指标名称']==='成交金额'&&platDates.includes(r['开始日期']))
      .forEach(r=>{ chMap[r['一级对象']] = (chMap[r['一级对象']]||0) + (r['数值']||0); });
    const channels = Object.entries(chMap).sort((a,b)=>b[1]-a[1]);

    const trendId = 'plt_trend_'+plat;
    const channelId = 'plt_ch_'+plat;
    const tableId = 'plt_tbl_'+plat;

    sec.innerHTML = `
      <div class="platform-header">
        <div class="platform-dot" style="background:${COLORS[plat]}"></div>
        <h3>${plat}</h3>
        <div class="summary">总成交 ${fmt(gross)} · 净成交 ${fmt(net)} · 退款 ${fmt(ref)} (${pct(ref,gross)})</div>
      </div>
      <div class="kpi-grid" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))">
        <div class="kpi card-sm"><div class="label">总成交</div><div class="val" style="font-size:18px;color:${COLORS[plat]}">${fmt(gross)}</div></div>
        <div class="kpi card-sm"><div class="label">净成交</div><div class="val" style="font-size:18px">${fmt(net)}</div></div>
        <div class="kpi card-sm"><div class="label">退款</div><div class="val" style="font-size:18px;color:var(--red)">${fmt(ref)}</div></div>
        <div class="kpi card-sm"><div class="label">退款率</div><div class="val" style="font-size:18px;color:var(--orange)">${pct(ref,gross)}</div></div>
        ${channels.length>0?`<div class="kpi card-sm"><div class="label">主渠道</div><div class="val" style="font-size:14px">${channels[0][0]} ${pct(channels[0][1],gross)}</div></div>`:''}
      </div>
      <div class="row">
        <div class="col-2 card"><h4>成交趋势</h4><canvas id="${trendId}"></canvas></div>
        <div class="col-2 card"><h4>渠道构成</h4><canvas id="${channelId}"></canvas></div>
      </div>
      <div class="card" style="margin-bottom:8px"><h4>周数据明细</h4><div class="tbl-wrap" id="${tableId}"></div></div>
    `;
    container.appendChild(sec);

    // trend chart
    const grossW = {}, netW = {}, refW = {};
    RAW.filter(r=>r['平台']===plat&&r['指标大类']==='成交'&&platDates.includes(r['开始日期'])).forEach(r=>{
      const d = r['开始日期'];
      if(r['一级对象']==='总成交') grossW[d]=r['数值'];
      if(r['一级对象']==='净成交') netW[d]=r['数值'];
      if(r['一级对象']==='退款') refW[d]=r['数值'];
    });
    makeChart(trendId, {
      type:'line',
      data:{labels:platDates.map(d=>d.slice(5)), datasets:[
        lineDataset('总成交',platDates.map(d=>grossW[d]||null),COLORS[plat],{spanGaps:true}),
        lineDataset('净成交',platDates.map(d=>netW[d]||null),COLORS[plat]+'88',{spanGaps:true,borderDash:[4,4]}),
        {label:'退款',data:platDates.map(d=>refW[d]||null),type:'bar',backgroundColor:'#f8717133',borderRadius:3,spanGaps:true}
      ]},
      options:{responsive:true,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#a1a1aa'}}},scales:{x:{ticks:{maxRotation:45},grid:{display:false}},y:{ticks:{callback:v=>fmt(v)}}}}
    });

    // channel chart
    if(channels.length > 0) {
      makeChart(channelId, {
        type:'doughnut',
        data:{labels:channels.map(c=>c[0]), datasets:[{data:channels.map(c=>c[1]), backgroundColor:['#818cf8','#f472b6','#4ade80','#fbbf24','#60a5fa','#22d3ee','#a78bfa','#fb923c'].slice(0,channels.length), borderWidth:0}]},
        options:{responsive:true,cutout:'55%',plugins:{legend:{position:'right',labels:{color:'#a1a1aa',padding:8}}}}
      });
    }

    // table
    const pwsRows = PWS.filter(r=>r['平台']===plat&&platDates.includes(r['开始日期']));
    let tbl = '<table><tr><th>周</th><th class="num">总成交</th><th class="num">退款</th><th class="num">净成交</th><th class="num">自营</th><th class="num">合作</th><th class="num">付费</th><th class="num">支出</th></tr>';
    pwsRows.forEach(r=>{
      tbl += `<tr><td>${r['周标签']}</td><td class="num">${fmtK(r['总成交'])}</td><td class="num neg">${fmtK(r['退款金额'])}</td><td class="num">${fmtK(r['净成交'])}</td><td class="num">${fmtK(r['自营成交'])}</td><td class="num">${fmtK(r['合作成交'])}</td><td class="num">${fmtK(r['付费成交'])}</td><td class="num neg">${fmtK(r['支出合计'])}</td></tr>`;
    });
    tbl += '</table>';
    document.getElementById(tableId).innerHTML = tbl;
  });
}

// ==================== ADS ====================
let adsDates = ALL_DATES;
function renderAds() {
  setupRange('ads', dates => { adsDates = dates; drawAds(); });
  drawAds();
}

function drawAds() {
  // KPI
  const xhsPaid = sumVal(RAW,'小红书','投放','付费','成交金额',adsDates);
  const xhsCost = sumVal(RAW,'小红书','投放','付费','消耗金额',adsDates);
  const dyPaid = sumVal(RAW,'抖店','付费','付费成交合计','成交金额',adsDates);
  const dyCost = sumVal(RAW,'抖店','付费','支出合计','支出金额',adsDates);
  const tbCost = sumVal(RAW,'淘宝','费用','总支出','支出金额',adsDates);
  const tbPaidCost = sumVal(RAW,'淘宝','费用','付费支出','支出金额',adsDates);
  const totalAdSpend = xhsCost + dyCost + tbCost;
  const totalAdRev = xhsPaid + dyPaid;

  document.getElementById('adsKpi').innerHTML = `
    <div class="kpi"><div class="label">总投放消耗</div><div class="val" style="color:var(--orange)">${fmt(totalAdSpend)}</div></div>
    <div class="kpi"><div class="label">总付费成交</div><div class="val" style="color:var(--green)">${fmt(totalAdRev)}</div></div>
    <div class="kpi"><div class="label">综合ROI</div><div class="val" style="color:var(--accent)">${totalAdSpend>0?(totalAdRev/totalAdSpend).toFixed(2):'–'}</div></div>
    <div class="kpi"><div class="label">小红书 消耗</div><div class="val" style="font-size:18px;color:#ff4757">${fmt(xhsCost)}</div></div>
    <div class="kpi"><div class="label">抖店 支出</div><div class="val" style="font-size:18px;color:#1e90ff">${fmt(dyCost)}</div></div>
    <div class="kpi"><div class="label">淘宝 总支出</div><div class="val" style="font-size:18px;color:#ff8c00">${fmt(tbCost)}</div></div>
  `;

  // ---- XHS ----
  const xhsData = RAW.filter(r=>r['平台']==='小红书'&&r['指标大类']==='投放'&&r['一级对象']==='付费'&&adsDates.includes(r['开始日期']));
  const xhsDates = [...new Set(xhsData.map(r=>r['开始日期']))].sort();
  const xhsByDate = {};
  xhsData.forEach(r=>{ if(!xhsByDate[r['开始日期']])xhsByDate[r['开始日期']]={};xhsByDate[r['开始日期']][r['指标名称']]=r['数值']; });

  makeChart('adsXhsMain', {
    type:'bar',
    data:{labels:xhsDates.map(d=>d.slice(5)), datasets:[
      barDataset('付费成交',xhsDates.map(d=>xhsByDate[d]?.['成交金额']||0),'#818cf8'),
      barDataset('消耗',xhsDates.map(d=>xhsByDate[d]?.['消耗金额']||0),'#f87171'),
      {label:'投产',data:xhsDates.map(d=>xhsByDate[d]?.['投产']||null),type:'line',borderColor:'#4ade80',backgroundColor:'transparent',tension:.3,borderWidth:2,pointRadius:2,yAxisID:'y1',spanGaps:true}
    ]},
    options:{responsive:true,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#a1a1aa'}}},scales:{x:{ticks:{maxRotation:45},grid:{display:false}},y:{ticks:{callback:v=>fmt(v)}},y1:{position:'right',grid:{display:false},ticks:{color:'#4ade80'}}}}
  });

  // XHS shop broadcast
  const xhsShop = RAW.filter(r=>r['平台']==='小红书'&&r['指标大类']==='店播'&&adsDates.includes(r['开始日期']));
  const xhsShopDates = [...new Set(xhsShop.map(r=>r['开始日期']))].sort();
  const xhsShopByDate = {};
  xhsShop.forEach(r=>{ if(!xhsShopByDate[r['开始日期']])xhsShopByDate[r['开始日期']]={};xhsShopByDate[r['开始日期']][r['指标名称']]=r['数值']; });

  makeChart('adsXhsShop', {
    type:'bar',
    data:{labels:xhsShopDates.map(d=>d.slice(5)), datasets:[
      barDataset('店播成交',xhsShopDates.map(d=>xhsShopByDate[d]?.['成交金额']||0),'#f472b6'),
      barDataset('投流成交',xhsShopDates.map(d=>xhsShopByDate[d]?.['投流成交']||0),'#818cf8'),
      barDataset('投流消耗',xhsShopDates.map(d=>xhsShopByDate[d]?.['投流消耗']||0),'#fbbf24'),
      {label:'投产',data:xhsShopDates.map(d=>xhsShopByDate[d]?.['投产']||null),type:'line',borderColor:'#4ade80',backgroundColor:'transparent',tension:.3,borderWidth:2,pointRadius:2,yAxisID:'y1',spanGaps:true}
    ]},
    options:{responsive:true,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#a1a1aa'}}},scales:{x:{ticks:{maxRotation:45},grid:{display:false}},y:{ticks:{callback:v=>fmt(v)}},y1:{position:'right',grid:{display:false},ticks:{color:'#4ade80'}}}}
  });

  // ---- DOUYIN ----
  const dyAccounts = ['官号','店播','达人（小蓝）','马老师','阿瓦达人0905','joann达人（0302）','主号（以前是官号+马老师）'];
  const dyAcctColors = ['#818cf8','#f472b6','#4ade80','#fbbf24','#60a5fa','#22d3ee','#a78bfa'];

  // line: weekly by account
  const dyWeekly = {};
  RAW.filter(r=>r['平台']==='抖店'&&r['指标大类']==='付费'&&dyAccounts.includes(r['一级对象'])&&r['指标名称']==='成交金额'&&adsDates.includes(r['开始日期']))
    .forEach(r=>{if(!dyWeekly[r['开始日期']])dyWeekly[r['开始日期']]={};dyWeekly[r['开始日期']][r['一级对象']]=r['数值'];});
  const dyDates = [...new Set(Object.keys(dyWeekly))].sort();

  makeChart('adsDouyinLine', {
    type:'line',
    data:{labels:dyDates.map(d=>d.slice(5)), datasets:dyAccounts.map((a,i)=>lineDataset(a.length>8?a.slice(0,8)+'…':a, dyDates.map(d=>dyWeekly[d]?.[a]||null), dyAcctColors[i%dyAcctColors.length], {spanGaps:true}))},
    options:{responsive:true,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#a1a1aa'}}},scales:{x:{ticks:{maxRotation:45},grid:{display:false}},y:{ticks:{callback:v=>fmt(v)}}}}
  });

  // bar: accumulated
  const dyAccData = dyAccounts.map(a => {
    const rev = sumVal(RAW,'抖店','付费',a,'成交金额',adsDates);
    const cost = sumVal(RAW,'抖店','付费',a,'消耗金额',adsDates);
    return {name:a, rev, cost, roi: cost>0?rev/cost:0};
  }).filter(x=>x.rev>0);

  makeChart('adsDouyinBar', {
    type:'bar',
    data:{labels:dyAccData.map(x=>x.name.length>6?x.name.slice(0,6)+'…':x.name), datasets:[
      barDataset('成交',dyAccData.map(x=>x.rev),'#818cf8'),
      barDataset('消耗',dyAccData.map(x=>x.cost),'#f87171'),
      {label:'ROI',data:dyAccData.map(x=>x.roi),type:'line',borderColor:'#4ade80',backgroundColor:'transparent',tension:.3,borderWidth:2,pointRadius:4,yAxisID:'y1'}
    ]},
    options:{responsive:true,plugins:{legend:{labels:{color:'#a1a1aa'}},tooltip:{callbacks:{label:ctx=>ctx.dataset.label+': '+(ctx.datasetIndex===2?ctx.raw.toFixed(2):fmt(ctx.raw))}}},scales:{x:{ticks:{maxRotation:45},grid:{display:false}},y:{ticks:{callback:v=>fmt(v)}},y1:{position:'right',grid:{display:false},ticks:{color:'#4ade80'},min:0}}}
  });

  // self-operated paid vs organic
  const dySelfPaid = {}, dySelfOrg = {};
  RAW.filter(r=>r['平台']==='抖店'&&r['指标大类']==='付费'&&r['一级对象']==='自营付费'&&r['指标名称']==='成交金额'&&adsDates.includes(r['开始日期']))
    .forEach(r=>dySelfPaid[r['开始日期']]=r['数值']);
  RAW.filter(r=>r['平台']==='抖店'&&r['指标大类']==='付费'&&r['一级对象']==='自营自然流'&&r['指标名称']==='成交金额'&&adsDates.includes(r['开始日期']))
    .forEach(r=>dySelfOrg[r['开始日期']]=r['数值']);
  const dySelfDates = [...new Set([...Object.keys(dySelfPaid),...Object.keys(dySelfOrg)])].sort().filter(d=>adsDates.includes(d));

  makeChart('adsDouyinSelf', {
    type:'bar',
    data:{labels:dySelfDates.map(d=>d.slice(5)), datasets:[
      {...barDataset('自营付费',dySelfDates.map(d=>dySelfPaid[d]||0),'#818cf8'), stack:'a'},
      {...barDataset('自营自然流',dySelfDates.map(d=>dySelfOrg[d]||0),'#4ade80'), stack:'a'},
    ]},
    options:{responsive:true,plugins:{legend:{labels:{color:'#a1a1aa'}}},scales:{x:{ticks:{maxRotation:45},grid:{display:false}},y:{stacked:true,ticks:{callback:v=>fmt(v)}}}}
  });

  // douyin cost
  const dyCostW = {};
  RAW.filter(r=>r['平台']==='抖店'&&r['指标大类']==='付费'&&r['一级对象']==='支出合计'&&r['指标名称']==='支出金额'&&adsDates.includes(r['开始日期']))
    .forEach(r=>dyCostW[r['开始日期']]=r['数值']);
  const dyCostDates = Object.keys(dyCostW).sort();
  makeChart('adsDouyinCost', {
    type:'line',
    data:{labels:dyCostDates.map(d=>d.slice(5)), datasets:[lineDataset('支出合计',dyCostDates.map(d=>dyCostW[d]),'#f87171')]},
    options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{ticks:{maxRotation:45},grid:{display:false}},y:{ticks:{callback:v=>fmt(v)}}}}
  });

  // ---- TAOBAO ----
  const tbFee = RAW.filter(r=>r['平台']==='淘宝'&&r['指标大类']==='费用'&&adsDates.includes(r['开始日期']));
  const tbFeeDates = [...new Set(tbFee.map(r=>r['开始日期']))].sort();
  const tbFeeByDate = {};
  tbFee.forEach(r=>{if(!tbFeeByDate[r['开始日期']])tbFeeByDate[r['开始日期']]={};tbFeeByDate[r['开始日期']][r['一级对象']]=r['数值'];});

  makeChart('adsTbCost', {
    type:'bar',
    data:{labels:tbFeeDates.map(d=>d.slice(5)), datasets:[
      {...barDataset('付费支出',tbFeeDates.map(d=>tbFeeByDate[d]?.['付费支出']||0),'#818cf8'),stack:'a'},
      {...barDataset('淘客支出',tbFeeDates.map(d=>tbFeeByDate[d]?.['淘客支出']||0),'#f472b6'),stack:'a'},
    ]},
    options:{responsive:true,plugins:{legend:{labels:{color:'#a1a1aa'}}},scales:{x:{ticks:{maxRotation:45},grid:{display:false}},y:{stacked:true,ticks:{callback:v=>fmt(v)}}}}
  });

  // taobao ROI
  const tbRoi = RAW.filter(r=>r['平台']==='淘宝'&&r['指标大类']==='投放'&&r['一级对象']==='付费计划'&&adsDates.includes(r['开始日期']));
  // aggregate by date (sum revenue, sum cost, weighted ROI)
  const tbRoiByDate = {};
  tbRoi.forEach(r=>{
    if(!tbRoiByDate[r['开始日期']]) tbRoiByDate[r['开始日期']]={rev:0,cost:0};
    if(r['指标名称']==='成交金额') tbRoiByDate[r['开始日期']].rev += r['数值']||0;
    if(r['指标名称']==='消耗金额') tbRoiByDate[r['开始日期']].cost += r['数值']||0;
  });
  const tbRoiDates = Object.keys(tbRoiByDate).sort();
  makeChart('adsTbRoi', {
    type:'bar',
    data:{labels:tbRoiDates.map(d=>d.slice(5)), datasets:[
      barDataset('付费成交',tbRoiDates.map(d=>tbRoiByDate[d].rev),'#818cf8'),
      barDataset('消耗',tbRoiDates.map(d=>tbRoiByDate[d].cost),'#f87171'),
      {label:'投产',data:tbRoiDates.map(d=>tbRoiByDate[d].cost>0?tbRoiByDate[d].rev/tbRoiByDate[d].cost:null),type:'line',borderColor:'#4ade80',backgroundColor:'transparent',tension:.3,borderWidth:2,pointRadius:2,yAxisID:'y1',spanGaps:true}
    ]},
    options:{responsive:true,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:'#a1a1aa'}}},scales:{x:{ticks:{maxRotation:45},grid:{display:false}},y:{ticks:{callback:v=>fmt(v)}},y1:{position:'right',grid:{display:false},ticks:{color:'#4ade80'}}}}
  });

  // taobao plans detail table
  const tbPlans = RAW.filter(r=>r['平台']==='淘宝'&&r['指标大类']==='投放'&&r['一级对象']==='付费计划'&&adsDates.includes(r['开始日期']));
  // group by date+二级对象
  const tbPlanMap = {};
  tbPlans.forEach(r => {
    const key = r['开始日期']+'|'+(r['二级对象']||'');
    if(!tbPlanMap[key]) tbPlanMap[key] = {date:r['开始日期'], plan:r['二级对象']||'-'};
    tbPlanMap[key][r['指标名称']] = r['数值'];
  });
  const tbPlanRows = Object.values(tbPlanMap).sort((a,b)=>a.date.localeCompare(b.date));
  let tbTbl = '<table><tr><th>周</th><th>计划</th><th class="num">成交</th><th class="num">消耗</th><th class="num">投产</th></tr>';
  tbPlanRows.forEach(r => {
    tbTbl += `<tr><td>${r.date.slice(5)}</td><td>${r.plan}</td><td class="num">${fmtK(r['成交金额'])}</td><td class="num neg">${fmtK(r['消耗金额'])}</td><td class="num">${r['投产']!=null?r['投产'].toFixed(2):'-'}</td></tr>`;
  });
  tbTbl += '</table>';
  document.getElementById('adsTbTable').innerHTML = tbTbl;
}

// ==================== COMPARE ====================
function initCompare() {
  const selA = document.getElementById('cmpWeekA');
  const selB = document.getElementById('cmpWeekB');
  const selP = document.getElementById('cmpPlatform');

  if(selA.options.length <= 1) {
    selA.innerHTML = ''; selB.innerHTML = '';
    ALL_DATES.slice().reverse().forEach((d,i) => {
      selA.add(new Option(d, d, i===0, i===0));
      selB.add(new Option(d, d, i===1, i===1));
    });
    selP.innerHTML = '<option value="all">全部</option>';
    PLATS.forEach(p => selP.add(new Option(p, p)));
  }
  runCompare();
}

function runCompare() {
  const weekA = document.getElementById('cmpWeekA').value;
  const weekB = document.getElementById('cmpWeekB').value;
  const plat = document.getElementById('cmpPlatform').value;
  const platforms = plat === 'all' ? PLATS : [plat];

  let grossA=0,grossB=0,netA=0,netB=0,refA=0,refB=0;
  platforms.forEach(p => {
    grossA += sumVal(RAW,p,'成交','总成交','成交金额',[weekA]);
    grossB += sumVal(RAW,p,'成交','总成交','成交金额',[weekB]);
    netA += sumVal(RAW,p,'成交','净成交','成交金额',[weekA]);
    netB += sumVal(RAW,p,'成交','净成交','成交金额',[weekB]);
    refA += sumVal(RAW,p,'成交','退款','退款金额',[weekA]);
    refB += sumVal(RAW,p,'成交','退款','退款金额',[weekB]);
  });

  const dG = delta(grossA, grossB), dN = delta(netA, netB), dR = delta(refA, refB);
  document.getElementById('cmpKpi').innerHTML = `
    <div class="kpi"><div class="label">周A 总成交</div><div class="val" style="font-size:20px">${fmt(grossA)}</div></div>
    <div class="kpi"><div class="label">周B 总成交</div><div class="val" style="font-size:20px">${fmt(grossB)}</div></div>
    <div class="kpi"><div class="label">变化</div><div class="val ${dG.cls}" style="font-size:20px">${dG.text}</div></div>
    <div class="kpi"><div class="label">周A 净成交</div><div class="val" style="font-size:20px">${fmt(netA)}</div></div>
    <div class="kpi"><div class="label">周B 净成交</div><div class="val" style="font-size:20px">${fmt(netB)}</div></div>
    <div class="kpi"><div class="label">变化</div><div class="val ${dN.cls}" style="font-size:20px">${dN.text}</div></div>
  `;

  // bar comparison
  const labels = platforms.filter(p=>sumVal(RAW,p,'成交','总成交','成交金额',[weekA])>0||sumVal(RAW,p,'成交','总成交','成交金额',[weekB])>0);
  makeChart('cmpBar', {
    type:'bar',
    data:{labels, datasets:[
      barDataset('周A: '+weekA, labels.map(p=>sumVal(RAW,p,'成交','总成交','成交金额',[weekA])), '#818cf8'),
      barDataset('周B: '+weekB, labels.map(p=>sumVal(RAW,p,'成交','总成交','成交金额',[weekB])), '#3f3f46'),
    ]},
    options:{responsive:true,plugins:{legend:{labels:{color:'#a1a1aa'}}},scales:{x:{grid:{display:false}},y:{ticks:{callback:v=>fmt(v)}}}}
  });

  // channel comparison (pick first non-all platform, or first platform)
  const chPlat = plat!=='all' ? plat : (labels[0]||PLATS[0]);
  const chA = {}, chB = {};
  RAW.filter(r=>r['平台']===chPlat&&r['指标大类']==='渠道细分'&&r['指标名称']==='成交金额'&&r['开始日期']===weekA).forEach(r=>chA[r['一级对象']]=r['数值']);
  RAW.filter(r=>r['平台']===chPlat&&r['指标大类']==='渠道细分'&&r['指标名称']==='成交金额'&&r['开始日期']===weekB).forEach(r=>chB[r['一级对象']]=r['数值']);
  const allCh = [...new Set([...Object.keys(chA),...Object.keys(chB)])];

  makeChart('cmpChannel', {
    type:'bar',
    data:{labels:allCh, datasets:[
      barDataset('周A',allCh.map(c=>chA[c]||0),'#818cf8'),
      barDataset('周B',allCh.map(c=>chB[c]||0),'#3f3f46'),
    ]},
    options:{responsive:true,plugins:{legend:{labels:{color:'#a1a1aa'}}},scales:{x:{grid:{display:false}},y:{ticks:{callback:v=>fmt(v)}}}}
  });

  // detail table
  let tbl = '<table><tr><th>平台</th><th>指标</th><th class="num">周A</th><th class="num">周B</th><th class="num">变化</th></tr>';
  platforms.forEach(p => {
    [['总成交','成交','总成交','成交金额'],['净成交','成交','净成交','成交金额'],['退款','成交','退款','退款金额']].forEach(([label,cat,obj,met]) => {
      const a = sumVal(RAW,p,cat,obj,met,[weekA]);
      const b = sumVal(RAW,p,cat,obj,met,[weekB]);
      const d = delta(a,b);
      if(a===0&&b===0) return;
      tbl += `<tr><td style="color:${COLORS[p]}">${p}</td><td>${label}</td><td class="num">${fmtK(a)}</td><td class="num">${fmtK(b)}</td><td class="num ${d.cls}">${d.text}</td></tr>`;
    });
  });
  tbl += '</table>';
  document.getElementById('cmpTable').innerHTML = tbl;
}

// ===== INIT =====
renderOverview();
</script>
</body>
</html>"""

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"✓ {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")
