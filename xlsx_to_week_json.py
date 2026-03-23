#!/usr/bin/env python3
"""从周度 Excel 中提取最新未导入的一周数据，输出为 import_week.py 可导入的 JSON。"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_DB = ROOT / "data" / "店铺每周数据汇总.sqlite"
LEGACY_DB = Path("/Users/wmix/Downloads/店铺每周数据汇总_2026-03-18.sqlite")
DEFAULT_DB = os.environ.get(
    "WMIX_DB_PATH",
    str(REPO_DB if REPO_DB.exists() else LEGACY_DB),
)
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def col_to_num(col: str) -> int:
    n = 0
    for ch in col:
        if ch.isalpha():
            n = n * 26 + ord(ch.upper()) - 64
    return n


def num_to_col(num: int) -> str:
    out = []
    while num:
        num, rem = divmod(num - 1, 26)
        out.append(chr(65 + rem))
    return "".join(reversed(out))


def shift_col(col: str, offset: int) -> str:
    return num_to_col(col_to_num(col) + offset)


def is_number(val) -> bool:
    return isinstance(val, (int, float))


def safe_div(a: float | None, b: float | None) -> float | None:
    if a is None or b in (None, 0):
        return None
    return a / b


def maybe_float(val):
    if val in (None, "", "-"):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    text = str(val).replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_mmdd(text: str, year_hint: int) -> tuple[date, date]:
    parts = text.replace("（包含这周数据未详细纠正）", "").split("-")
    if len(parts) != 2:
        raise ValueError(f"无法解析周标签: {text}")
    start_m, start_d = [int(x) for x in parts[0].split("/")]
    end_m, end_d = [int(x) for x in parts[1].split("/")]
    start = date(year_hint, start_m, start_d)
    end_year = year_hint + (1 if (end_m, end_d) < (start_m, start_d) else 0)
    end = date(end_year, end_m, end_d)
    return start, end


@dataclass
class Cell:
    value: object
    formula: str | None = None


class Workbook:
    def __init__(self, path: Path):
        self.path = path
        self._zip = zipfile.ZipFile(path)
        self._shared = self._load_shared_strings()
        self._sheet_targets = self._load_sheet_targets()
        self._cache: dict[str, dict[str, Cell]] = {}

    def close(self):
        self._zip.close()

    def _load_shared_strings(self) -> list[str]:
        try:
            root = ET.fromstring(self._zip.read("xl/sharedStrings.xml"))
        except KeyError:
            return []
        out = []
        for si in root:
            out.append("".join(t.text or "" for t in si.iter(NS + "t")))
        return out

    def _load_sheet_targets(self) -> dict[str, str]:
        wb = ET.fromstring(self._zip.read("xl/workbook.xml"))
        rels = ET.fromstring(self._zip.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels
            if rel.attrib["Target"].startswith("worksheets/")
        }
        out = {}
        for sheet in wb.find(NS + "sheets"):
            rid = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            out[sheet.attrib["name"]] = "xl/" + rel_map[rid]
        return out

    def _parse_sheet(self, name: str) -> dict[str, Cell]:
        if name in self._cache:
            return self._cache[name]
        ws = ET.fromstring(self._zip.read(self._sheet_targets[name]))
        data: dict[str, Cell] = {}
        for c in ws.iter(NS + "c"):
            ref = c.attrib["r"]
            cell_type = c.attrib.get("t")
            formula = c.find(NS + "f")
            value = c.find(NS + "v")
            parsed = None
            if cell_type == "s" and value is not None:
                parsed = self._shared[int(value.text)]
            elif cell_type == "inlineStr":
                inline = c.find(NS + "is")
                parsed = "".join(t.text or "" for t in inline.iter(NS + "t")) if inline is not None else ""
            elif value is not None:
                parsed = maybe_float(value.text)
                if parsed is None:
                    parsed = value.text
            data[ref] = Cell(parsed, formula.text if formula is not None else None)
        self._cache[name] = data
        return data

    def cell(self, sheet: str, ref: str) -> Cell:
        return self._parse_sheet(sheet).get(ref, Cell(None, None))

    def value(self, sheet: str, ref: str):
        return self.cell(sheet, ref).value


def latest_db_week(db_path: Path) -> tuple[date, date]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    row = cur.execute(
        "SELECT MAX(开始日期), MAX(结束日期) FROM structured_data"
    ).fetchone()
    conn.close()
    if not row or not row[0] or not row[1]:
        raise RuntimeError(f"数据库中没有可参考的历史周次: {db_path}")
    return date.fromisoformat(row[0]), date.fromisoformat(row[1])


def find_summary_week_col(wb: Workbook, latest_start: date) -> tuple[str, date, date, str]:
    expected_start = latest_start + timedelta(days=7)
    expected_label = f"{expected_start:%m/%d}-{(expected_start + timedelta(days=6)):%m/%d}"

    header_cols = []
    for ref, cell in wb._parse_sheet("周汇总✅").items():
        if ref.endswith("1") and isinstance(cell.value, str) and "/" in cell.value and "-" in cell.value:
            col = "".join(ch for ch in ref if ch.isalpha())
            header_cols.append((col_to_num(col), col, cell.value))
    header_cols.sort()

    for _, col, raw in header_cols:
        if raw == expected_label and is_number(wb.value("周汇总✅", f"{col}3")):
            start, end = parse_mmdd(raw, expected_start.year)
            return col, start, end, raw

    for _, col, raw in header_cols:
        try:
            start, end = parse_mmdd(raw, expected_start.year)
        except ValueError:
            continue
        if start > latest_start and is_number(wb.value("周汇总✅", f"{col}3")):
            return col, start, end, raw

    raise RuntimeError("未找到 Excel 中最新且未导入的一周")


def find_sheet_col_by_label(wb: Workbook, sheet: str, label: str) -> str:
    matches = []
    for ref, cell in wb._parse_sheet(sheet).items():
        if ref.endswith("1") and cell.value == label:
            col = "".join(ch for ch in ref if ch.isalpha())
            matches.append(col)
    if not matches:
        raise RuntimeError(f"{sheet} 中找不到周标签 {label}")
    return sorted(matches, key=col_to_num)[-1]


def find_taobao_start_col(wb: Workbook, target_total: float) -> str:
    candidates = []
    for ref, cell in wb._parse_sheet("淘宝✅").items():
        if ref.endswith("3") and is_number(cell.value) and abs(float(cell.value) - target_total) < 0.01:
            val_col = "".join(ch for ch in ref if ch.isalpha())
            candidates.append(shift_col(val_col, -1))
    if not candidates:
        raise RuntimeError("淘宝✅ 中找不到与周汇总匹配的总成交列")
    return sorted(candidates, key=col_to_num)[-1]


def build_rows(wb: Workbook, start: date, end: date, raw_week: str):
    start_s = start.isoformat()
    end_s = end.isoformat()
    week_label = f"{start_s}~{end_s}"
    summary_col = find_sheet_col_by_label(wb, "周汇总✅", raw_week)
    dy_col = find_sheet_col_by_label(wb, "抖店✅", raw_week)
    xhs_col = find_sheet_col_by_label(wb, "小红书✅", raw_week)
    tb_total = float(wb.value("周汇总✅", f"{summary_col}5"))
    tb_col = find_taobao_start_col(wb, tb_total)

    def add_row(rows, plat, cat, obj, metric, value, *, obj2=None, unit="元", sheet="", cell="", label="", formula=None):
        if value is None:
            return
        rows.append({
            "开始日期": start_s,
            "结束日期": end_s,
            "原始周标签": raw_week,
            "周标签": week_label,
            "平台": plat,
            "指标大类": cat,
            "一级对象": obj,
            "二级对象": obj2,
            "指标名称": metric,
            "数值": round(float(value), 6),
            "单位": unit,
            "来源sheet": sheet,
            "来源单元格": cell or None,
            "来源标签": label or None,
            "是否公式": "是" if formula else "否",
            "公式说明": formula,
        })

    rows = []

    summary = {
        "抖店": {"row": 3, "detail_sheet": "抖店✅"},
        "小红书": {"row": 4, "detail_sheet": "小红书✅"},
        "淘宝": {"row": 5, "detail_sheet": "淘宝✅"},
        "天猫": {"row": 6, "detail_sheet": None},
        "微信": {"row": 7, "detail_sheet": None},
        "B站": {"row": 8, "detail_sheet": None},
    }

    pws = []

    def summary_vals(row_num: int):
        gross = maybe_float(wb.value("周汇总✅", f"{summary_col}{row_num}"))
        refund = maybe_float(wb.value("周汇总✅", f"{shift_col(summary_col, 1)}{row_num}"))
        self_amt = maybe_float(wb.value("周汇总✅", f"{shift_col(summary_col, 2)}{row_num}"))
        coop_amt = maybe_float(wb.value("周汇总✅", f"{shift_col(summary_col, 3)}{row_num}"))
        net = gross - refund if gross is not None and refund is not None else None
        if coop_amt is None and gross is not None and self_amt is not None:
            coop_amt = gross - self_amt
        return gross, refund, net, self_amt, coop_amt

    for plat, meta in summary.items():
        gross, refund, net, self_amt, coop_amt = summary_vals(meta["row"])
        if plat == "抖店":
            add_row(rows, plat, "成交", "总成交", "成交金额", wb.value("抖店✅", f"{dy_col}2"), sheet="抖店✅", cell=f"{dy_col}2", label="抖店成交")
        elif plat == "小红书":
            add_row(rows, plat, "成交", "总成交", "成交金额", wb.value("小红书✅", f"{xhs_col}3"), sheet="小红书✅", cell=f"{xhs_col}3", label="总成交")
        elif plat == "淘宝":
            add_row(rows, plat, "成交", "总成交", "成交金额", wb.value("淘宝✅", f"{shift_col(tb_col, 1)}3"), sheet="淘宝✅", cell=f"{shift_col(tb_col, 1)}3", label="总成交")
        else:
            add_row(rows, plat, "成交", "总成交", "成交金额", gross, sheet="周汇总✅", cell=f"{summary_col}{meta['row']}", label="总成交")

        add_row(rows, plat, "成交", "退款", "退款金额", refund, sheet="周汇总✅", cell=f"{shift_col(summary_col, 1)}{meta['row']}", label="退款金额")
        add_row(
            rows,
            plat,
            "成交",
            "净成交",
            "成交金额",
            net,
            sheet="周汇总✅",
            cell=f"{summary_col}{meta['row']}/{shift_col(summary_col, 1)}{meta['row']}",
            label="成交金额 - 退款金额",
            formula="周汇总成交金额 - 周汇总退款金额",
        )

        if plat in {"天猫", "微信", "B站"}:
            add_row(rows, plat, "渠道细分", "自营", "成交金额", self_amt, sheet="周汇总✅", cell=f"{shift_col(summary_col, 2)}{meta['row']}", label="自营")
            add_row(
                rows,
                plat,
                "渠道细分",
                "合作",
                "成交金额",
                coop_amt,
                sheet="周汇总✅",
                cell=f"{summary_col}{meta['row']}/{shift_col(summary_col, 2)}{meta['row']}",
                label="合作（总成交-自营）",
                formula="周汇总总成交 - 周汇总自营",
            )

        row = {
            "开始日期": start_s,
            "结束日期": end_s,
            "周标签": week_label,
            "平台": plat,
            "总成交": round(gross, 6) if gross is not None else None,
            "退款金额": round(refund, 6) if refund is not None else None,
            "净成交": round(net, 6) if net is not None else None,
            "自营成交": None,
            "合作成交": None,
            "付费成交": None,
            "支出合计": None,
        }
        if plat in {"抖店", "天猫", "微信", "B站"}:
            row["自营成交"] = round(self_amt, 6) if self_amt is not None else None
            row["合作成交"] = round(coop_amt, 6) if coop_amt is not None else None
        pws.append(row)

    dy_total = maybe_float(wb.value("抖店✅", f"{dy_col}2"))
    dy_self = maybe_float(wb.value("抖店✅", f"{dy_col}4"))
    dy_goods = maybe_float(wb.value("抖店✅", f"{dy_col}6"))
    dy_live = maybe_float(wb.value("抖店✅", f"{dy_col}8"))
    dy_coop = maybe_float(wb.value("抖店✅", f"{dy_col}9"))
    dy_short = maybe_float(wb.value("抖店✅", f"{dy_col}11"))
    dy_goods达人 = maybe_float(wb.value("抖店✅", f"{dy_col}13"))
    dy_paid_total = maybe_float(wb.value("抖店✅", f"{dy_col}43"))
    dy_spend_total = maybe_float(wb.value("抖店✅", f"{dy_col}44"))

    add_row(rows, "抖店", "渠道细分", "自营", "成交金额", dy_self, sheet="抖店✅", cell=f"{dy_col}4", label="自营")
    add_row(rows, "抖店", "渠道细分", "自然流", "成交金额", dy_self - (maybe_float(wb.value("抖店✅", f"{dy_col}32")) or 0) - (maybe_float(wb.value("抖店✅", f"{dy_col}34")) or 0), sheet="抖店✅", cell=f"{dy_col}48", label="店铺自然流", formula=f"{dy_col}4-({dy_col}32+{dy_col}34)")
    add_row(rows, "抖店", "渠道细分", "商品卡", "成交金额", dy_goods, sheet="抖店✅", cell=f"{dy_col}6", label="自营商品卡")
    add_row(rows, "抖店", "渠道细分", "自营直播", "成交金额", dy_live, sheet="抖店✅", cell=f"{dy_col}8", label="自营直播")
    add_row(rows, "抖店", "渠道细分", "合作", "成交金额", dy_coop, sheet="抖店✅", cell=f"{dy_col}9", label="合作")
    add_row(rows, "抖店", "渠道细分", "达人短视频", "成交金额", dy_short, sheet="抖店✅", cell=f"{dy_col}11", label="达人短视频")
    add_row(rows, "抖店", "渠道细分", "达人商品卡", "成交金额", dy_goods达人, sheet="抖店✅", cell=f"{dy_col}13", label="达人商品卡")

    dy_accounts = [
        ("马老师", 31),
        ("店播", 32),
        ("官号", 34),
        ("达人（小蓝）", 36),
        ("阿瓦达人0905", 38),
        ("joann达人（0302）", 40),
    ]
    dy_self_paid = 0.0
    for name, row_num in dy_accounts:
        revenue = maybe_float(wb.value("抖店✅", f"{dy_col}{row_num}"))
        roi = maybe_float(wb.value("抖店✅", f"{shift_col(dy_col, 1)}{row_num}"))
        if name == "马老师" and roi is not None and revenue is not None and abs(roi - revenue) < 0.01:
            roi = None
        spend = safe_div(revenue, roi)
        add_row(rows, "抖店", "付费", name, "成交金额", revenue, sheet="抖店✅", cell=f"{dy_col}{row_num}", label=name)
        add_row(rows, "抖店", "付费", name, "投产", roi, unit="倍", sheet="抖店✅", cell=f"{shift_col(dy_col, 1)}{row_num}", label=name)
        add_row(rows, "抖店", "付费", name, "消耗金额", spend, sheet="抖店✅", cell=f"{dy_col}{row_num}", label=name, formula="成交金额 / 投产" if spend is not None else None)
        if name in {"店播", "官号"} and revenue is not None:
            dy_self_paid += revenue

    dy_self_natural = dy_self - dy_self_paid if dy_self is not None else None
    add_row(rows, "抖店", "付费", "付费成交合计", "成交金额", dy_paid_total, sheet="抖店✅", cell=f"{dy_col}43", label="付费成交合计")
    add_row(rows, "抖店", "付费", "支出合计", "支出金额", dy_spend_total, sheet="抖店✅", cell=f"{dy_col}44", label="支出合计")
    add_row(rows, "抖店", "付费", "自营付费", "成交金额", dy_self_paid, sheet="抖店✅", cell=f"{dy_col}47", label="自营付费", formula=f"{dy_col}32+{dy_col}34")
    add_row(rows, "抖店", "付费", "自营自然流", "成交金额", dy_self_natural, sheet="抖店✅", cell=f"{dy_col}48", label="自营自然流", formula=f"{dy_col}4-{dy_col}47")

    for row in pws:
        if row["平台"] == "抖店":
            row["自营成交"] = round(dy_self, 6) if dy_self is not None else None
            row["合作成交"] = round(dy_coop, 6) if dy_coop is not None else None
            row["付费成交"] = round(dy_paid_total, 6) if dy_paid_total is not None else None
            row["支出合计"] = round(dy_spend_total, 6) if dy_spend_total is not None else None

    xhs_total = maybe_float(wb.value("小红书✅", f"{xhs_col}3"))
    xhs_self = maybe_float(wb.value("小红书✅", f"{xhs_col}5"))
    xhs_note = maybe_float(wb.value("小红书✅", f"{xhs_col}8"))
    xhs_live = maybe_float(wb.value("小红书✅", f"{xhs_col}10"))
    xhs_card = maybe_float(wb.value("小红书✅", f"{xhs_col}11"))
    xhs_live_goods = maybe_float(wb.value("小红书✅", f"{xhs_col}14"))
    xhs_goods_card = maybe_float(wb.value("小红书✅", f"{xhs_col}13"))
    xhs_paid_cost = maybe_float(wb.value("小红书✅", f"{shift_col(xhs_col, 1)}15"))
    xhs_paid_rev = maybe_float(wb.value("小红书✅", f"{shift_col(xhs_col, 1)}17"))
    xhs_paid_roi = safe_div(xhs_paid_rev, xhs_paid_cost)
    xhs_shop_rev = maybe_float(wb.value("小红书✅", f"{shift_col(xhs_col, 1)}29"))
    xhs_shop_cost = maybe_float(wb.value("小红书✅", f"{shift_col(xhs_col, 1)}34"))
    xhs_shop_paid_rev = maybe_float(wb.value("小红书✅", f"{shift_col(xhs_col, 1)}35"))
    xhs_shop_roi = safe_div(xhs_shop_paid_rev, xhs_shop_cost)

    add_row(rows, "小红书", "渠道细分", "自营汇总", "成交金额", xhs_self, sheet="小红书✅", cell=f"{xhs_col}5", label="自营汇总")
    add_row(rows, "小红书", "渠道细分", "自营笔记", "成交金额", xhs_note, sheet="小红书✅", cell=f"{xhs_col}8", label="自营笔记")
    add_row(rows, "小红书", "渠道细分", "自营直播", "成交金额", xhs_live, sheet="小红书✅", cell=f"{xhs_col}10", label="自营直播")
    add_row(rows, "小红书", "渠道细分", "自营商卡", "成交金额", xhs_card, sheet="小红书✅", cell=f"{xhs_col}11", label="自营商卡")
    add_row(rows, "小红书", "渠道细分", "带货商卡", "成交金额", xhs_goods_card, sheet="小红书✅", cell=f"{xhs_col}13", label="带货商卡")
    add_row(rows, "小红书", "渠道细分", "带货直播", "成交金额", xhs_live_goods, sheet="小红书✅", cell=f"{xhs_col}14", label="带货直播")
    add_row(rows, "小红书", "渠道细分", "自然流", "成交金额", xhs_self - xhs_paid_rev if xhs_self is not None and xhs_paid_rev is not None else None, sheet="小红书✅", cell=f"{xhs_col}7", label="自然流（自营减付费）", formula="自营汇总 - 付费成交金额")
    add_row(rows, "小红书", "投放", "付费", "消耗金额", xhs_paid_cost, sheet="小红书✅", cell=f"{shift_col(xhs_col, 1)}15", label="付费")
    add_row(rows, "小红书", "投放", "付费", "投产", xhs_paid_roi, unit="倍", sheet="小红书✅", cell=f"{shift_col(xhs_col, 1)}16", label="付费", formula="付费成交金额 / 付费消耗金额")
    add_row(rows, "小红书", "投放", "付费", "成交金额", xhs_paid_rev, sheet="小红书✅", cell=f"{shift_col(xhs_col, 1)}17", label="付费")
    add_row(rows, "小红书", "店播", "店播", "成交金额", xhs_shop_rev, sheet="小红书✅", cell=f"{shift_col(xhs_col, 1)}29", label="店播")
    add_row(rows, "小红书", "店播", "店播", "投流消耗", xhs_shop_cost, sheet="小红书✅", cell=f"{shift_col(xhs_col, 1)}34", label="店播")
    add_row(rows, "小红书", "店播", "店播", "投流成交", xhs_shop_paid_rev, sheet="小红书✅", cell=f"{shift_col(xhs_col, 1)}35", label="店播")
    add_row(rows, "小红书", "店播", "店播", "投产", xhs_shop_roi, unit="倍", sheet="小红书✅", cell=f"{shift_col(xhs_col, 1)}36", label="店播", formula="店播投流成交 / 店播投流消耗")

    for row in pws:
        if row["平台"] == "小红书":
            row["付费成交"] = round(xhs_paid_rev, 6) if xhs_paid_rev is not None else None

    tb_total = maybe_float(wb.value("淘宝✅", f"{shift_col(tb_col, 1)}3"))
    tb_refund = maybe_float(wb.value("周汇总✅", f"{shift_col(summary_col, 1)}5"))
    tb_paid_plans = [
        ("全站推广", 15),
        ("超级短视频", 16),
        ("超播全站推", 17),
        ("关键词推广", 18),
        ("货品加速", 19),
    ]
    tb_paid_spend = 0.0
    tb_paid_rev = 0.0
    for name, row_num in tb_paid_plans:
        spend = maybe_float(wb.value("淘宝✅", f"{tb_col}{row_num}"))
        rev = maybe_float(wb.value("淘宝✅", f"{shift_col(tb_col, 1)}{row_num}"))
        roi = maybe_float(wb.value("淘宝✅", f"{shift_col(tb_col, 2)}{row_num}"))
        if spend is None and rev is None:
            continue
        if spend is not None:
            tb_paid_spend += spend
        if rev is not None:
            tb_paid_rev += rev
        add_row(rows, "淘宝", "投放", "付费计划", "消耗金额", spend, obj2=name, sheet="淘宝✅", cell=f"{tb_col}{row_num}", label=name)
        add_row(rows, "淘宝", "投放", "付费计划", "成交金额", rev, obj2=name, sheet="淘宝✅", cell=f"{shift_col(tb_col, 1)}{row_num}", label=name)
        add_row(rows, "淘宝", "投放", "付费计划", "投产", roi, obj2=name, unit="倍", sheet="淘宝✅", cell=f"{shift_col(tb_col, 2)}{row_num}", label=name)

    tb_commission = maybe_float(wb.value("淘宝✅", f"{shift_col(tb_col, 1)}85"))
    tb_service_fee = maybe_float(wb.value("淘宝✅", f"{shift_col(tb_col, 1)}86"))
    tb_general = None
    auto_base = maybe_float(wb.value("淘宝✅", f"{shift_col(tb_col, 1)}83"))
    auto_pct = maybe_float(wb.value("淘宝✅", f"{shift_col(tb_col, 1)}84"))
    if auto_base is not None and auto_pct is not None:
        tb_general = auto_base * auto_pct
    tb_affiliate_total = maybe_float(wb.value("淘宝✅", f"{shift_col(tb_col, 1)}82"))
    tb_affiliate = tb_affiliate_total - tb_general if tb_affiliate_total is not None and tb_general is not None else tb_affiliate_total
    tb_daibo = maybe_float(wb.value("淘宝✅", f"{shift_col(tb_col, 1)}7")) or 0.0
    tb_self = maybe_float(wb.value("周汇总✅", f"{shift_col(summary_col, 2)}5"))
    tb_organic = tb_self - tb_paid_rev if tb_self is not None else None
    tb_affiliate_spend = (tb_commission or 0.0) + (tb_service_fee or 0.0)
    tb_total_spend = tb_affiliate_spend + tb_paid_spend

    add_row(rows, "淘宝", "渠道细分", "付费", "成交金额", tb_paid_rev, sheet="淘宝✅", cell=f"{shift_col(tb_col, 1)}20", label="付费", formula="付费计划合计成交")
    add_row(rows, "淘宝", "渠道细分", "淘宝客", "成交金额", tb_affiliate, sheet="淘宝✅", cell=f"{shift_col(tb_col, 1)}89", label="淘宝客", formula="淘客总 - 自主 * 百分比" if tb_general is not None else None)
    add_row(rows, "淘宝", "渠道细分", "淘宝达播", "成交金额", tb_daibo, sheet="淘宝✅", cell=f"{shift_col(tb_col, 1)}7", label="淘宝达播")
    add_row(rows, "淘宝", "渠道细分", "自营", "成交金额", tb_self, sheet="周汇总✅", cell=f"{shift_col(summary_col, 2)}5", label="自营")
    add_row(rows, "淘宝", "渠道细分", "自然流", "成交金额", tb_organic, sheet="淘宝✅", cell=f"{shift_col(tb_col, 1)}10", label="自然流", formula="自营 - 付费")
    add_row(rows, "淘宝", "费用", "付费支出", "支出金额", tb_paid_spend, sheet="淘宝✅", cell=f"{tb_col}20", label="付费支出", formula="付费计划合计消耗")
    add_row(rows, "淘宝", "费用", "淘客支出", "支出金额", tb_affiliate_spend, sheet="淘宝✅", cell=f"{shift_col(tb_col, 1)}95", label="淘客支出", formula="佣金 + 服务费")
    add_row(rows, "淘宝", "费用", "总支出", "支出金额", tb_total_spend, sheet="淘宝✅", cell=f"{shift_col(tb_col, 1)}13", label="总支出", formula="淘客支出 + 付费支出")

    for row in pws:
        if row["平台"] == "淘宝":
            row["自营成交"] = round(tb_self, 6) if tb_self is not None else None
            row["付费成交"] = round(tb_paid_rev, 6) if tb_paid_rev is not None else None
            row["支出合计"] = round(tb_total_spend, 6) if tb_total_spend is not None else None

    return {
        "_meta": {
            "export_time": datetime.now().isoformat(timespec="seconds"),
            "week": week_label,
            "start": start_s,
            "end": end_s,
            "source_excel": str(wb.path),
        },
        "structured_data": rows,
        "platform_weekly_summary": pws,
    }


def main():
    parser = argparse.ArgumentParser(description="从 Excel 生成可导入的周 JSON")
    parser.add_argument("xlsx", help="周数据 Excel 路径")
    parser.add_argument("--db", default=DEFAULT_DB, help="用于判断最新已导入周的数据库路径")
    parser.add_argument("--out", help="输出 JSON 路径；默认写到 Excel 同目录")
    args = parser.parse_args()

    xlsx_path = Path(args.xlsx).expanduser().resolve()
    db_path = Path(args.db).expanduser().resolve()
    if not xlsx_path.exists():
        print(f"✗ Excel 不存在: {xlsx_path}", file=sys.stderr)
        sys.exit(1)
    if not db_path.exists():
        print(f"✗ 数据库不存在: {db_path}", file=sys.stderr)
        sys.exit(1)

    latest_start, _ = latest_db_week(db_path)
    wb = Workbook(xlsx_path)
    try:
        _, start, end, raw_week = find_summary_week_col(wb, latest_start)
        payload = build_rows(wb, start, end, raw_week)
    finally:
        wb.close()

    out_path = Path(args.out).expanduser().resolve() if args.out else xlsx_path.with_name(f"week_{start.isoformat()}.json")
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✓ 已生成: {out_path}")
    print(f"  周次: {start} ~ {end}")
    print(f"  structured_data: {len(payload['structured_data'])} 条")
    print(f"  platform_weekly_summary: {len(payload['platform_weekly_summary'])} 条")


if __name__ == "__main__":
    main()
