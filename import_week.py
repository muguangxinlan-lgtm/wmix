#!/usr/bin/env python3
"""
将填表工具导出的 JSON 文件写入 SQLite 数据库。

用法:
    python3 import_week.py week_2026-03-16.json
    python3 import_week.py week_2026-03-16.json --db /path/to/other.sqlite
"""
import sqlite3, json, sys, os, shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_DB = ROOT / "data" / "店铺每周数据汇总.sqlite"
LEGACY_DB = Path("/Users/wmix/Downloads/店铺每周数据汇总_2026-03-18.sqlite")
DEFAULT_DB = os.environ.get(
    "WMIX_DB_PATH",
    str(REPO_DB if REPO_DB.exists() else LEGACY_DB),
)

def main():
    if len(sys.argv) < 2:
        print("用法: python3 import_week.py <json文件> [--db <数据库路径>]")
        sys.exit(1)

    json_path = sys.argv[1]
    db_path = DEFAULT_DB

    if "--db" in sys.argv:
        idx = sys.argv.index("--db")
        if idx + 1 < len(sys.argv):
            db_path = sys.argv[idx + 1]

    if not os.path.exists(json_path):
        print(f"✗ 文件不存在: {json_path}")
        sys.exit(1)

    if not os.path.exists(db_path):
        print(f"✗ 数据库不存在: {db_path}")
        sys.exit(1)

    # 读取 JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    meta = data.get('_meta', {})
    sd_rows = data.get('structured_data', [])
    pws_rows = data.get('platform_weekly_summary', [])
    start_date = meta.get('start', '')

    if not sd_rows:
        print("✗ JSON 中没有 structured_data 数据")
        sys.exit(1)

    print(f"导入周: {meta.get('week', '?')}")
    print(f"  structured_data: {len(sd_rows)} 条")
    print(f"  platform_weekly_summary: {len(pws_rows)} 条")
    print(f"  目标数据库: {db_path}")

    # 备份数据库
    backup_path = db_path + f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"  备份: {backup_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 检查是否已存在该周数据
    existing = cur.execute(
        "SELECT COUNT(*) FROM structured_data WHERE 开始日期=?", (start_date,)
    ).fetchone()[0]

    if existing > 0:
        print(f"\n⚠ 数据库中已有 {start_date} 的 {existing} 条数据")
        ans = input("  覆盖？(y/N): ").strip().lower()
        if ans != 'y':
            print("取消导入")
            conn.close()
            sys.exit(0)
        cur.execute("DELETE FROM structured_data WHERE 开始日期=?", (start_date,))
        cur.execute("DELETE FROM platform_weekly_summary WHERE 开始日期=?", (start_date,))
        print(f"  已删除旧数据")

    # 写入 structured_data
    sd_cols = ['开始日期','结束日期','原始周标签','周标签','平台','指标大类',
               '一级对象','二级对象','指标名称','数值','单位','来源sheet',
               '来源单元格','来源标签','是否公式','公式说明']
    placeholders = ','.join(['?'] * len(sd_cols))
    for row in sd_rows:
        vals = [row.get(c) for c in sd_cols]
        cur.execute(f"INSERT INTO structured_data ({','.join(sd_cols)}) VALUES ({placeholders})", vals)

    # 写入 platform_weekly_summary
    pws_cols = ['开始日期','结束日期','周标签','平台','总成交','退款金额',
                '净成交','自营成交','合作成交','付费成交','支出合计']
    placeholders2 = ','.join(['?'] * len(pws_cols))
    for row in pws_rows:
        vals = [row.get(c) for c in pws_cols]
        cur.execute(f"INSERT INTO platform_weekly_summary ({','.join(pws_cols)}) VALUES ({placeholders2})", vals)

    conn.commit()

    # 验证
    total_sd = cur.execute("SELECT COUNT(*) FROM structured_data").fetchone()[0]
    total_pws = cur.execute("SELECT COUNT(*) FROM platform_weekly_summary").fetchone()[0]
    weeks = cur.execute("SELECT COUNT(DISTINCT 开始日期) FROM structured_data").fetchone()[0]
    conn.close()

    print(f"\n✓ 导入成功！")
    print(f"  数据库现有: {total_sd} 条 structured_data, {total_pws} 条 platform_weekly_summary, {weeks} 周")
    print(f"\n下一步: 运行任意 build 脚本生成看板")
    print(f"  python3 build_v3.py")

if __name__ == '__main__':
    main()
