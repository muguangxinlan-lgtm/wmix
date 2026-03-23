#!/usr/bin/env python3
"""生成数据填表工具 HTML — 只跟 SQLite 数据库打交道，不绑定任何看板视图"""
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
OUT = ROOT / "data_entry.html"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
q = lambda sql: [dict(r) for r in conn.execute(sql).fetchall()]

structured = q("SELECT * FROM structured_data ORDER BY 开始日期, 平台")
pws = q("SELECT * FROM platform_weekly_summary ORDER BY 开始日期, 平台")
conn.close()

structured_json = json.dumps(structured, ensure_ascii=False)
pws_json = json.dumps(pws, ensure_ascii=False)

html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>电商数据填表工具</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#f8f9fc;--card:#fff;--border:#e5e7eb;--accent:#6366f1;--green:#10b981;--red:#ef4444;--t1:#1a1a2e;--t2:#4a4a6a;--t3:#8888a4;--radius:12px}
body{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif;background:var(--bg);color:var(--t1);font-size:14px;line-height:1.6}

.header{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;padding:32px 24px;text-align:center}
.header h1{font-size:28px;font-weight:900;margin-bottom:6px}
.header p{opacity:.8;font-size:14px}

.container{max-width:960px;margin:0 auto;padding:24px}

.date-section{background:var(--card);border-radius:var(--radius);padding:20px 24px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,.06);display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.date-section label{font-weight:700;font-size:13px;color:var(--t2)}
.date-section input[type=date]{padding:8px 12px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;font-family:inherit}
.date-section .ref{font-size:12px;color:var(--t3)}

.plat-section{background:var(--card);border-radius:var(--radius);margin-bottom:12px;box-shadow:0 2px 8px rgba(0,0,0,.06);overflow:hidden}
.plat-header{display:flex;align-items:center;padding:16px 20px;cursor:pointer;gap:12px;user-select:none;transition:background .15s}
.plat-header:hover{background:#f5f3ff}
.plat-header .icon{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;font-size:15px;flex-shrink:0}
.plat-header .name{font-size:16px;font-weight:700;flex:1}
.plat-header .badge{font-size:11px;padding:3px 10px;border-radius:10px;background:#f1f3f9;color:var(--t3);font-weight:600}
.plat-header .arrow{font-size:14px;color:var(--t3);transition:transform .3s}
.plat-section.open .arrow{transform:rotate(180deg)}
.plat-body{max-height:0;overflow:hidden;transition:max-height .4s ease}
.plat-section.open .plat-body{max-height:5000px}
.plat-inner{padding:0 20px 20px}

.field-group{margin-bottom:16px}
.field-group-title{font-size:12px;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #e8e8f0}
.field-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:6px}
.field-row.r3{grid-template-columns:1fr 1fr 1fr}
.field-row.r4{grid-template-columns:1fr 1fr 1fr 1fr}
.field{position:relative}
.field label{display:block;font-size:11px;color:var(--t3);margin-bottom:2px;font-weight:600}
.field input{width:100%;padding:8px 10px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;font-family:inherit;font-variant-numeric:tabular-nums;transition:border-color .2s}
.field input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(99,102,241,.1)}
.field input.computed{background:#f8f7ff;border-color:#ddd8ff;color:var(--accent);font-weight:600;cursor:not-allowed}
.field input.has-value{border-color:var(--green)}
.prev-ref{font-size:10px;color:var(--t3);margin-top:1px}
.prev-ref span{color:var(--t2);font-weight:600}

.btn-bar{display:flex;gap:12px;margin-top:24px;justify-content:center;flex-wrap:wrap}
.btn{padding:12px 32px;border-radius:10px;font-size:15px;font-weight:700;cursor:pointer;border:none;transition:all .2s;font-family:inherit}
.btn-primary{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;box-shadow:0 4px 14px rgba(99,102,241,.3)}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 6px 20px rgba(99,102,241,.4)}
.btn-secondary{background:#fff;color:var(--accent);border:2px solid var(--accent)}
.btn-secondary:hover{background:#f5f3ff}

.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(100px);background:var(--t1);color:#fff;padding:12px 28px;border-radius:10px;font-weight:600;z-index:999;transition:transform .4s;font-size:14px}
.toast.show{transform:translateX(-50%) translateY(0)}

.status-bar{background:var(--card);border-radius:var(--radius);padding:14px 20px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,.06);display:flex;align-items:center;gap:12px}
.status-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.status-text{font-size:13px;color:var(--t2)}
.status-text strong{color:var(--t1)}
.save-indicator{font-size:11px;color:var(--green);font-weight:600;margin-left:auto}

/* 导出说明 */
.export-info{background:#f0fdf4;border:1.5px solid #bbf7d0;border-radius:var(--radius);padding:16px 20px;margin-bottom:20px;font-size:13px;color:#166534;line-height:1.7}
.export-info code{background:#dcfce7;padding:2px 6px;border-radius:4px;font-size:12px;font-family:'SF Mono',Menlo,monospace}

@media(max-width:640px){
  .field-row,.field-row.r3,.field-row.r4{grid-template-columns:1fr}
  .container{padding:12px}
  .date-section{flex-direction:column;align-items:flex-start}
}
</style>
</head>
<body>

<div class="header">
  <h1>电商数据填表工具</h1>
  <p>填写手工数据 · 公式自动计算 · 导出 JSON 写入数据库</p>
</div>

<div class="container">
  <div class="export-info">
    <strong>使用流程：</strong>填写数据 → 点「导出 JSON」下载文件 → 运行
    <code>python3 import_week.py 下载的文件.json</code> 写入数据库 →
    运行 <code>python3 build_v3.py</code> 更新新版看板 →
    如需更新线上旧版，再运行 <code>python3 build_v2.py</code> 和 <code>./publish_github_pages.sh</code>
  </div>

  <div class="date-section">
    <label>新一周</label>
    <div>
      <label style="font-size:11px;color:var(--t3)">开始日期</label>
      <input type="date" id="startDate">
    </div>
    <div>
      <label style="font-size:11px;color:var(--t3)">结束日期</label>
      <input type="date" id="endDate">
    </div>
    <div class="ref" id="dateRef"></div>
  </div>

  <div class="status-bar">
    <div class="status-dot" id="statusDot" style="background:#ccc"></div>
    <div class="status-text" id="statusText">等待填写数据…</div>
    <div class="save-indicator" id="saveIndicator"></div>
  </div>

  <div id="platformForms"></div>

  <div class="btn-bar">
    <button class="btn btn-secondary" onclick="clearForm()">清空</button>
    <button class="btn btn-secondary" onclick="loadPrevWeek()">复制上周数据</button>
    <button class="btn btn-primary" onclick="exportJSON()">导出 JSON ↓</button>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
// ===== 只用于参考上周数值，不用于生成看板 =====
const RAW = """ + structured_json + r""";
const PWS = """ + pws_json + r""";

const ALL_DATES = [...new Set(RAW.map(r=>r['开始日期']))].sort();
const END_MAP = {}; RAW.forEach(r => END_MAP[r['开始日期']] = r['结束日期']);
const LATEST = ALL_DATES[ALL_DATES.length-1];

// ===== PLATFORM CONFIG =====
const PLATS_CFG = [
  {
    name:'小红书', color:['#ff2d55','#ff6b8a'], char:'红',
    manual:[
      {group:'成交', fields:[
        {key:'xhs_gross',label:'总成交',cat:'成交',obj:'总成交',metric:'成交金额',unit:'元'},
        {key:'xhs_refund',label:'退款',cat:'成交',obj:'退款',metric:'退款金额',unit:'元'},
      ]},
      {group:'投放 · 付费', fields:[
        {key:'xhs_paid_rev',label:'付费成交',cat:'投放',obj:'付费',metric:'成交金额',unit:'元'},
        {key:'xhs_paid_cost',label:'付费消耗',cat:'投放',obj:'付费',metric:'消耗金额',unit:'元'},
      ]},
      {group:'店播', fields:[
        {key:'xhs_live_rev',label:'店播成交',cat:'店播',obj:'店播',metric:'成交金额',unit:'元'},
        {key:'xhs_live_flow_rev',label:'投流成交',cat:'店播',obj:'店播',metric:'投流成交',unit:'元'},
        {key:'xhs_live_flow_cost',label:'投流消耗',cat:'店播',obj:'店播',metric:'投流消耗',unit:'元'},
      ]},
      {group:'渠道细分', fields:[
        {key:'xhs_ch_self_total',label:'自营汇总',cat:'渠道细分',obj:'自营汇总',metric:'成交金额',unit:'元'},
        {key:'xhs_ch_self_live',label:'自营直播',cat:'渠道细分',obj:'自营直播',metric:'成交金额',unit:'元'},
        {key:'xhs_ch_self_note',label:'自营笔记',cat:'渠道细分',obj:'自营笔记',metric:'成交金额',unit:'元'},
        {key:'xhs_ch_self_card',label:'自营商卡',cat:'渠道细分',obj:'自营商卡',metric:'成交金额',unit:'元'},
        {key:'xhs_ch_kol_live',label:'带货直播',cat:'渠道细分',obj:'带货直播',metric:'成交金额',unit:'元'},
        {key:'xhs_ch_kol_card',label:'带货商卡',cat:'渠道细分',obj:'带货商卡',metric:'成交金额',unit:'元'},
      ]},
    ],
    computed:[
      {key:'xhs_net',label:'净成交',formula:'xhs_gross - xhs_refund',cat:'成交',obj:'净成交',metric:'成交金额'},
      {key:'xhs_paid_roi',label:'付费投产',formula:'xhs_paid_rev / xhs_paid_cost',cat:'投放',obj:'付费',metric:'投产',decimals:4,unit:'倍'},
      {key:'xhs_live_roi',label:'店播投产',formula:'xhs_live_flow_rev / xhs_live_flow_cost',cat:'店播',obj:'店播',metric:'投产',decimals:4,unit:'倍'},
      {key:'xhs_ch_organic',label:'渠道·自然流',formula:'xhs_ch_self_total - xhs_paid_rev',cat:'渠道细分',obj:'自然流',metric:'成交金额'},
    ]
  },
  {
    name:'抖店', color:['#1e90ff','#00d4ff'], char:'抖',
    manual:[
      {group:'成交', fields:[
        {key:'dy_gross',label:'总成交',cat:'成交',obj:'总成交',metric:'成交金额',unit:'元'},
        {key:'dy_refund',label:'退款',cat:'成交',obj:'退款',metric:'退款金额',unit:'元'},
      ]},
      {group:'付费 · 各账号成交', fields:[
        {key:'dy_f_guanhao',label:'官号',cat:'付费',obj:'官号',metric:'成交金额',unit:'元'},
        {key:'dy_f_dianbo',label:'店播',cat:'付费',obj:'店播',metric:'成交金额',unit:'元'},
        {key:'dy_f_xiaolan',label:'达人(小蓝)',cat:'付费',obj:'达人（小蓝）',metric:'成交金额',unit:'元'},
        {key:'dy_f_malaoshi',label:'马老师',cat:'付费',obj:'马老师',metric:'成交金额',unit:'元'},
        {key:'dy_f_awa',label:'阿瓦达人0905',cat:'付费',obj:'阿瓦达人0905',metric:'成交金额',unit:'元'},
        {key:'dy_f_joann',label:'joann达人',cat:'付费',obj:'joann达人（0302）',metric:'成交金额',unit:'元'},
        {key:'dy_f_zhuhao',label:'主号',cat:'付费',obj:'主号（以前是官号+马老师）',metric:'成交金额',unit:'元'},
      ]},
      {group:'付费 · 各账号投产', fields:[
        {key:'dy_r_guanhao',label:'官号·投产',cat:'付费',obj:'官号',metric:'投产',unit:'倍',decimals:2},
        {key:'dy_r_dianbo',label:'店播·投产',cat:'付费',obj:'店播',metric:'投产',unit:'倍',decimals:2},
        {key:'dy_r_xiaolan',label:'达人(小蓝)·投产',cat:'付费',obj:'达人（小蓝）',metric:'投产',unit:'倍',decimals:2},
        {key:'dy_r_malaoshi',label:'马老师·投产',cat:'付费',obj:'马老师',metric:'投产',unit:'倍',decimals:2},
        {key:'dy_r_awa',label:'阿瓦·投产',cat:'付费',obj:'阿瓦达人0905',metric:'投产',unit:'倍',decimals:2},
        {key:'dy_r_joann',label:'joann·投产',cat:'付费',obj:'joann达人（0302）',metric:'投产',unit:'倍',decimals:2},
        {key:'dy_r_zhuhao',label:'主号·投产',cat:'付费',obj:'主号（以前是官号+马老师）',metric:'投产',unit:'倍',decimals:2},
      ]},
      {group:'付费 · 支出', fields:[
        {key:'dy_spend',label:'支出合计',cat:'付费',obj:'支出合计',metric:'支出金额',unit:'元'},
      ]},
      {group:'渠道细分', fields:[
        {key:'dy_ch_self',label:'自营',cat:'渠道细分',obj:'自营',metric:'成交金额',unit:'元'},
        {key:'dy_ch_coop',label:'合作',cat:'渠道细分',obj:'合作',metric:'成交金额',unit:'元'},
        {key:'dy_ch_card',label:'商品卡',cat:'渠道细分',obj:'商品卡',metric:'成交金额',unit:'元'},
        {key:'dy_ch_self_live',label:'自营直播',cat:'渠道细分',obj:'自营直播',metric:'成交金额',unit:'元'},
        {key:'dy_ch_kol_card',label:'达人商品卡',cat:'渠道细分',obj:'达人商品卡',metric:'成交金额',unit:'元'},
        {key:'dy_ch_kol_video',label:'达人短视频',cat:'渠道细分',obj:'达人短视频',metric:'成交金额',unit:'元'},
      ]},
    ],
    computed:[
      {key:'dy_net',label:'净成交',formula:'dy_gross - dy_refund',cat:'成交',obj:'净成交',metric:'成交金额'},
      {key:'dy_f_total',label:'付费成交合计',formula:'dy_f_guanhao + dy_f_dianbo + dy_f_xiaolan + dy_f_malaoshi + dy_f_awa + dy_f_joann + dy_f_zhuhao',cat:'付费',obj:'付费成交合计',metric:'成交金额'},
      {key:'dy_c_guanhao',label:'官号·消耗',formula:'dy_f_guanhao / dy_r_guanhao',cat:'付费',obj:'官号',metric:'消耗金额',decimals:4},
      {key:'dy_c_dianbo',label:'店播·消耗',formula:'dy_f_dianbo / dy_r_dianbo',cat:'付费',obj:'店播',metric:'消耗金额',decimals:4},
      {key:'dy_c_xiaolan',label:'达人(小蓝)·消耗',formula:'dy_f_xiaolan / dy_r_xiaolan',cat:'付费',obj:'达人（小蓝）',metric:'消耗金额',decimals:4},
      {key:'dy_c_malaoshi',label:'马老师·消耗',formula:'dy_f_malaoshi / dy_r_malaoshi',cat:'付费',obj:'马老师',metric:'消耗金额',decimals:4},
      {key:'dy_c_awa',label:'阿瓦·消耗',formula:'dy_f_awa / dy_r_awa',cat:'付费',obj:'阿瓦达人0905',metric:'消耗金额',decimals:4},
      {key:'dy_c_joann',label:'joann·消耗',formula:'dy_f_joann / dy_r_joann',cat:'付费',obj:'joann达人（0302）',metric:'消耗金额',decimals:4},
      {key:'dy_c_zhuhao',label:'主号·消耗',formula:'dy_f_zhuhao / dy_r_zhuhao',cat:'付费',obj:'主号（以前是官号+马老师）',metric:'消耗金额',decimals:4},
      {key:'dy_self_paid',label:'自营付费',formula:'dy_f_guanhao + dy_f_dianbo',cat:'付费',obj:'自营付费',metric:'成交金额'},
      {key:'dy_self_organic',label:'自营自然流',formula:'dy_ch_self - (dy_f_guanhao + dy_f_dianbo)',cat:'付费',obj:'自营自然流',metric:'成交金额'},
      {key:'dy_ch_organic',label:'渠道·自然流',formula:'dy_ch_self - (dy_f_guanhao + dy_f_dianbo)',cat:'渠道细分',obj:'自然流',metric:'成交金额'},
    ]
  },
  {
    name:'淘宝', color:['#ff6a00','#ffab40'], char:'淘',
    manual:[
      {group:'成交', fields:[
        {key:'tb_gross',label:'总成交',cat:'成交',obj:'总成交',metric:'成交金额',unit:'元'},
        {key:'tb_refund',label:'退款',cat:'成交',obj:'退款',metric:'退款金额',unit:'元'},
      ]},
      {group:'付费计划 · 全站推广', fields:[
        {key:'tb_p1_rev',label:'成交',cat:'投放',obj:'付费计划',obj2:'全站推广',metric:'成交金额',unit:'元'},
        {key:'tb_p1_cost',label:'消耗',cat:'投放',obj:'付费计划',obj2:'全站推广',metric:'消耗金额',unit:'元'},
      ]},
      {group:'付费计划 · 关键词推广', fields:[
        {key:'tb_p2_rev',label:'成交',cat:'投放',obj:'付费计划',obj2:'关键词推广',metric:'成交金额',unit:'元'},
        {key:'tb_p2_cost',label:'消耗',cat:'投放',obj:'付费计划',obj2:'关键词推广',metric:'消耗金额',unit:'元'},
      ]},
      {group:'付费计划 · 精准人群推广', fields:[
        {key:'tb_p3_rev',label:'成交',cat:'投放',obj:'付费计划',obj2:'精准人群推广',metric:'成交金额',unit:'元'},
        {key:'tb_p3_cost',label:'消耗',cat:'投放',obj:'付费计划',obj2:'精准人群推广',metric:'消耗金额',unit:'元'},
      ]},
      {group:'付费计划 · 货品加速', fields:[
        {key:'tb_p4_rev',label:'成交',cat:'投放',obj:'付费计划',obj2:'货品加速',metric:'成交金额',unit:'元'},
        {key:'tb_p4_cost',label:'消耗',cat:'投放',obj:'付费计划',obj2:'货品加速',metric:'消耗金额',unit:'元'},
      ]},
      {group:'付费计划 · 超播全站推', fields:[
        {key:'tb_p5_rev',label:'成交',cat:'投放',obj:'付费计划',obj2:'超播全站推',metric:'成交金额',unit:'元'},
        {key:'tb_p5_cost',label:'消耗',cat:'投放',obj:'付费计划',obj2:'超播全站推',metric:'消耗金额',unit:'元'},
      ]},
      {group:'付费计划 · 超级短视频', fields:[
        {key:'tb_p6_rev',label:'成交',cat:'投放',obj:'付费计划',obj2:'超级短视频',metric:'成交金额',unit:'元'},
        {key:'tb_p6_cost',label:'消耗',cat:'投放',obj:'付费计划',obj2:'超级短视频',metric:'消耗金额',unit:'元'},
      ]},
      {group:'渠道 (手工)', fields:[
        {key:'tb_ch_daibo',label:'淘宝达播',cat:'渠道细分',obj:'淘宝达播',metric:'成交金额',unit:'元'},
      ]},
      {group:'费用 (手工)', fields:[
        {key:'tb_taoke_fee',label:'淘客支出',cat:'费用',obj:'淘客支出',metric:'支出金额',unit:'元'},
      ]},
    ],
    computed:[
      {key:'tb_net',label:'净成交',formula:'tb_gross - tb_refund',cat:'成交',obj:'净成交',metric:'成交金额'},
      {key:'tb_p1_roi',label:'全站推广·投产',formula:'tb_p1_rev / tb_p1_cost',cat:'投放',obj:'付费计划',obj2:'全站推广',metric:'投产',decimals:2,unit:'倍'},
      {key:'tb_p2_roi',label:'关键词·投产',formula:'tb_p2_rev / tb_p2_cost',cat:'投放',obj:'付费计划',obj2:'关键词推广',metric:'投产',decimals:2,unit:'倍'},
      {key:'tb_p3_roi',label:'精准人群·投产',formula:'tb_p3_rev / tb_p3_cost',cat:'投放',obj:'付费计划',obj2:'精准人群推广',metric:'投产',decimals:2,unit:'倍'},
      {key:'tb_p4_roi',label:'货品加速·投产',formula:'tb_p4_rev / tb_p4_cost',cat:'投放',obj:'付费计划',obj2:'货品加速',metric:'投产',decimals:2,unit:'倍'},
      {key:'tb_p5_roi',label:'超播·投产',formula:'tb_p5_rev / tb_p5_cost',cat:'投放',obj:'付费计划',obj2:'超播全站推',metric:'投产',decimals:2,unit:'倍'},
      {key:'tb_p6_roi',label:'短视频·投产',formula:'tb_p6_rev / tb_p6_cost',cat:'投放',obj:'付费计划',obj2:'超级短视频',metric:'投产',decimals:2,unit:'倍'},
      {key:'tb_paid_rev',label:'渠道·付费',formula:'(tb_p1_rev||0)+(tb_p2_rev||0)+(tb_p3_rev||0)+(tb_p4_rev||0)+(tb_p5_rev||0)+(tb_p6_rev||0)',cat:'渠道细分',obj:'付费',metric:'成交金额'},
      {key:'tb_paid_cost',label:'费用·付费支出',formula:'(tb_p1_cost||0)+(tb_p2_cost||0)+(tb_p3_cost||0)+(tb_p4_cost||0)+(tb_p5_cost||0)+(tb_p6_cost||0)',cat:'费用',obj:'付费支出',metric:'支出金额'},
      {key:'tb_total_cost',label:'费用·总支出',formula:'((tb_p1_cost||0)+(tb_p2_cost||0)+(tb_p3_cost||0)+(tb_p4_cost||0)+(tb_p5_cost||0)+(tb_p6_cost||0)) + (tb_taoke_fee||0)',cat:'费用',obj:'总支出',metric:'支出金额'},
      {key:'tb_ch_self_all',label:'渠道·自营',special:'tb_self_all',cat:'渠道细分',obj:'自营',metric:'成交金额'},
      {key:'tb_ch_organic',label:'渠道·自然流',special:'tb_organic',cat:'渠道细分',obj:'自然流',metric:'成交金额'},
    ]
  },
  {
    name:'微信', color:['#07c160','#4edd8a'], char:'微',
    manual:[
      {group:'成交', fields:[
        {key:'wx_gross',label:'总成交',cat:'成交',obj:'总成交',metric:'成交金额',unit:'元'},
        {key:'wx_refund',label:'退款',cat:'成交',obj:'退款',metric:'退款金额',unit:'元'},
      ]},
      {group:'渠道细分', fields:[
        {key:'wx_ch_self',label:'自营',cat:'渠道细分',obj:'自营',metric:'成交金额',unit:'元'},
        {key:'wx_ch_coop',label:'合作',cat:'渠道细分',obj:'合作',metric:'成交金额',unit:'元'},
      ]},
    ],
    computed:[
      {key:'wx_net',label:'净成交',formula:'wx_gross - wx_refund',cat:'成交',obj:'净成交',metric:'成交金额'},
    ]
  },
  {
    name:'B站', color:['#00a1d6','#23d5e0'], char:'B',
    manual:[
      {group:'成交', fields:[
        {key:'bz_gross',label:'总成交',cat:'成交',obj:'总成交',metric:'成交金额',unit:'元'},
        {key:'bz_refund',label:'退款',cat:'成交',obj:'退款',metric:'退款金额',unit:'元'},
      ]},
      {group:'渠道细分', fields:[
        {key:'bz_ch_self',label:'自营',cat:'渠道细分',obj:'自营',metric:'成交金额',unit:'元'},
        {key:'bz_ch_coop',label:'合作',cat:'渠道细分',obj:'合作',metric:'成交金额',unit:'元'},
      ]},
    ],
    computed:[
      {key:'bz_net',label:'净成交',formula:'bz_gross - bz_refund',cat:'成交',obj:'净成交',metric:'成交金额'},
    ]
  },
  {
    name:'天猫', color:['#8b5cf6','#a78bfa'], char:'猫',
    manual:[
      {group:'成交', fields:[
        {key:'tm_gross',label:'总成交',cat:'成交',obj:'总成交',metric:'成交金额',unit:'元'},
        {key:'tm_refund',label:'退款',cat:'成交',obj:'退款',metric:'退款金额',unit:'元'},
      ]},
      {group:'渠道细分', fields:[
        {key:'tm_ch_self',label:'自营',cat:'渠道细分',obj:'自营',metric:'成交金额',unit:'元'},
        {key:'tm_ch_coop',label:'合作',cat:'渠道细分',obj:'合作',metric:'成交金额',unit:'元'},
      ]},
    ],
    computed:[
      {key:'tm_net',label:'净成交',formula:'tm_gross - tm_refund',cat:'成交',obj:'净成交',metric:'成交金额'},
    ]
  },
];

// ===== FORM VALUES =====
const V = {};

const PREV = {};
function loadPrevValues() {
  PLATS_CFG.forEach(p => {
    p.manual.forEach(g => g.fields.forEach(f => {
      const rows = RAW.filter(r =>
        r['平台']===p.name && r['开始日期']===LATEST &&
        r['指标大类']===f.cat && r['一级对象']===f.obj && r['指标名称']===f.metric &&
        ((!f.obj2 && !r['二级对象']) || r['二级对象']===f.obj2)
      );
      if(rows.length>0) PREV[f.key] = rows[0]['数值'];
    }));
  });
}

function renderForm() {
  const container = document.getElementById('platformForms');
  let html = '';
  PLATS_CFG.forEach((p, pi) => {
    const fieldCount = p.manual.reduce((s,g)=>s+g.fields.length, 0);
    const computedCount = p.computed.length;
    html += `<div class="plat-section${pi===0?' open':''}" id="plat_${pi}">
      <div class="plat-header" onclick="togglePlat(${pi})">
        <div class="icon" style="background:linear-gradient(135deg,${p.color[0]},${p.color[1]})">${p.char}</div>
        <span class="name">${p.name}</span>
        <span class="badge">${fieldCount}项手填 · ${computedCount}项自动</span>
        <span class="arrow">▼</span>
      </div>
      <div class="plat-body"><div class="plat-inner">`;
    p.manual.forEach(g => {
      html += `<div class="field-group"><div class="field-group-title">${g.group}</div>
        <div class="field-row${g.fields.length > 2 ? ' r'+Math.min(g.fields.length,4) : ''}">`;
      g.fields.forEach(f => {
        const prev = PREV[f.key];
        const prevStr = prev != null ? Number(prev).toLocaleString('zh-CN',{maximumFractionDigits:2}) : '';
        html += `<div class="field"><label>${f.label}</label>
          <input type="text" inputmode="decimal" id="${f.key}" placeholder="0" oninput="onInput('${f.key}',this.value)">
          ${prevStr ? `<div class="prev-ref">上周 <span>${prevStr}</span></div>` : ''}</div>`;
      });
      html += `</div></div>`;
    });
    if(p.computed.length > 0) {
      html += `<div class="field-group"><div class="field-group-title">自动计算</div>
        <div class="field-row${p.computed.length > 2 ? ' r'+Math.min(p.computed.length,4) : ''}">`;
      p.computed.forEach(c => {
        html += `<div class="field"><label>${c.label}</label>
          <input type="text" class="computed" id="${c.key}" readonly tabindex="-1"></div>`;
      });
      html += `</div></div>`;
    }
    html += `</div></div></div>`;
  });
  container.innerHTML = html;
}

function onInput(key, rawVal) {
  const val = parseFloat(rawVal.replace(/,/g,''));
  V[key] = isNaN(val) ? null : val;
  const el = document.getElementById(key);
  if(el) el.classList.toggle('has-value', V[key] != null);
  recalc(); autoSave(); updateStatus();
}

function recalc() {
  PLATS_CFG.forEach(p => {
    p.computed.forEach(c => {
      let result = null;
      try {
        if(c.special === 'tb_self_all') {
          result = (V['tb_gross']||0) - (V['tb_ch_daibo']||0);
        } else if(c.special === 'tb_organic') {
          const selfAll = (V['tb_gross']||0) - (V['tb_ch_daibo']||0);
          const paid = (V['_computed_tb_paid_rev'] != null) ? V['_computed_tb_paid_rev'] : 0;
          result = selfAll - paid;
        } else {
          let expr = c.formula;
          const keys = expr.match(/[a-z_][a-z0-9_]*/g) || [];
          let valid = true;
          keys.forEach(k => {
            if(k==='NaN'||k==='null'||k==='undefined') return;
            const v = V[k];
            if(v == null && !expr.includes(k+'||0')) valid = false;
            expr = expr.replace(new RegExp('\\b'+k+'\\b','g'), v != null ? v : '0');
          });
          if(valid || expr.includes('||0')) {
            result = eval(expr);
            if(!isFinite(result)) result = null;
          }
        }
      } catch(e) { result = null; }

      const el = document.getElementById(c.key);
      if(el) {
        const d = c.decimals || 2;
        el.value = result != null ? result.toLocaleString('zh-CN',{maximumFractionDigits:d,minimumFractionDigits:0}) : '';
      }
      V['_computed_'+c.key] = result;
    });
  });
}

function togglePlat(idx) { document.getElementById('plat_'+idx).classList.toggle('open'); }

function initDates() {
  const last = new Date(LATEST);
  const nextStart = new Date(last); nextStart.setDate(last.getDate()+7);
  const nextEnd = new Date(nextStart); nextEnd.setDate(nextStart.getDate()+6);
  document.getElementById('startDate').value = fmtD(nextStart);
  document.getElementById('endDate').value = fmtD(nextEnd);
  document.getElementById('dateRef').textContent = '上一周: '+LATEST+' ~ '+(END_MAP[LATEST]||'');
}
function fmtD(d) { return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }

function updateStatus() {
  const filled = Object.keys(V).filter(k=>!k.startsWith('_')&&V[k]!=null).length;
  const total = PLATS_CFG.reduce((s,p)=>s+p.manual.reduce((s2,g)=>s2+g.fields.length,0),0);
  const dot = document.getElementById('statusDot');
  const text = document.getElementById('statusText');
  if(filled===0){ dot.style.background='#ccc'; text.innerHTML='等待填写数据…'; }
  else if(filled<total){ dot.style.background='#f59e0b'; text.innerHTML=`已填 <strong>${filled}</strong> / ${total} 项`; }
  else { dot.style.background='#10b981'; text.innerHTML=`全部 <strong>${total}</strong> 项已填写 ✓`; }
}

const STORAGE_KEY = 'ecom_entry_v3';
function autoSave() {
  const data = { startDate:document.getElementById('startDate').value, endDate:document.getElementById('endDate').value, values:{} };
  Object.keys(V).forEach(k => { if(!k.startsWith('_')&&V[k]!=null) data.values[k]=V[k]; });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  const ind = document.getElementById('saveIndicator');
  ind.textContent = '已自动保存'; setTimeout(()=>ind.textContent='', 1500);
}
function autoLoad() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if(!saved) return;
  try {
    const data = JSON.parse(saved);
    if(data.startDate) document.getElementById('startDate').value = data.startDate;
    if(data.endDate) document.getElementById('endDate').value = data.endDate;
    if(data.values) {
      Object.entries(data.values).forEach(([k,v]) => {
        V[k]=v;
        const el=document.getElementById(k);
        if(el&&!el.classList.contains('computed')){ el.value=v; el.classList.add('has-value'); }
      });
      recalc(); updateStatus();
    }
  } catch(e) {}
}

function clearForm() {
  if(!confirm('确定清空所有已填数据？')) return;
  Object.keys(V).forEach(k=>delete V[k]);
  document.querySelectorAll('input[type=text]').forEach(el=>{ el.value=''; el.classList.remove('has-value'); });
  localStorage.removeItem(STORAGE_KEY);
  recalc(); updateStatus(); showToast('已清空');
}

function loadPrevWeek() {
  PLATS_CFG.forEach(p => p.manual.forEach(g => g.fields.forEach(f => {
    if(PREV[f.key]!=null){ V[f.key]=PREV[f.key]; const el=document.getElementById(f.key); if(el){el.value=PREV[f.key];el.classList.add('has-value');} }
  })));
  recalc(); autoSave(); updateStatus(); showToast('已复制上周数据');
}

function showToast(msg) {
  const t=document.getElementById('toast'); t.textContent=msg;
  t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),4500);
}

// ===== EXPORT JSON (写入数据库用) =====
function exportJSON() {
  const startDate = document.getElementById('startDate').value;
  const endDate = document.getElementById('endDate').value;
  if(!startDate||!endDate){ showToast('请先选择日期'); return; }

  const weekLabel = startDate+'~'+endDate;
  const structured_rows = [];
  const pws_rows = [];

  function addRow(plat,cat,obj,obj2,metric,val,unit,isFormula,formulaDesc) {
    if(val==null||isNaN(val)) return;
    structured_rows.push({
      '开始日期':startDate,'结束日期':endDate,
      '原始周标签':startDate.slice(5).replace(/-/g,'/')+'-'+endDate.slice(5).replace(/-/g,'/'),
      '周标签':weekLabel,'平台':plat,
      '指标大类':cat,'一级对象':obj,'二级对象':obj2||null,
      '指标名称':metric,'数值':val,
      '单位':unit||'元','来源sheet':'手工录入',
      '来源单元格':null,'来源标签':null,
      '是否公式':isFormula?'是':'否','公式说明':formulaDesc||null
    });
  }

  PLATS_CFG.forEach(p => {
    p.manual.forEach(g => g.fields.forEach(f => {
      addRow(p.name,f.cat,f.obj,f.obj2,f.metric,V[f.key],f.unit,false,null);
    }));
    p.computed.forEach(c => {
      const val = V['_computed_'+c.key];
      addRow(p.name,c.cat,c.obj,c.obj2,c.metric,val,c.unit||'元',true,c.formula||c.special||'');
    });
  });

  if(structured_rows.length===0){ showToast('没有数据可以导出'); return; }

  // Build PWS
  const keyMap = {小红书:'xhs',抖店:'dy',淘宝:'tb',微信:'wx',B站:'bz',天猫:'tm'};
  PLATS_CFG.forEach(p => {
    const k = keyMap[p.name];
    const gross = V[k+'_gross']||null;
    const refund = V[k+'_refund']||null;
    const net = V['_computed_'+k+'_net'] ?? null;
    if(gross==null && refund==null) return;
    const row = { '开始日期':startDate,'结束日期':endDate,'周标签':weekLabel,
      '平台':p.name,'总成交':gross,'退款金额':refund,'净成交':net,
      '自营成交':null,'合作成交':null,'付费成交':null,'支出合计':null };
    if(p.name==='抖店'){ row['自营成交']=V['dy_ch_self']||null; row['合作成交']=V['dy_ch_coop']||null; row['付费成交']=V['_computed_dy_f_total']||null; row['支出合计']=V['dy_spend']||null; }
    else if(p.name==='小红书'){ row['付费成交']=V['xhs_paid_rev']||null; }
    else if(p.name==='微信'){ row['自营成交']=V['wx_ch_self']||null; row['合作成交']=V['wx_ch_coop']||null; }
    else if(p.name==='B站'){ row['自营成交']=V['bz_ch_self']||null; row['合作成交']=V['bz_ch_coop']||null; }
    else if(p.name==='天猫'){ row['自营成交']=V['tm_ch_self']||null; row['合作成交']=V['tm_ch_coop']||null; }
    pws_rows.push(row);
  });

  const output = { _meta:{ export_time:new Date().toISOString(), week:weekLabel, start:startDate, end:endDate },
    structured_data: structured_rows, platform_weekly_summary: pws_rows };

  const blob = new Blob([JSON.stringify(output, null, 2)], {type:'application/json;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'week_'+startDate+'.json';
  a.click();
  URL.revokeObjectURL(url);
  showToast('已导出 week_'+startDate+'.json；下一步：先运行 python3 import_week.py 导入数据库，再运行 build_v3.py；如需更新线上旧版，再运行 build_v2.py 和 publish_github_pages.sh');
}

// ===== INIT =====
loadPrevValues();
renderForm();
initDates();
autoLoad();
updateStatus();
</script>
</body>
</html>"""

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✓ {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")
