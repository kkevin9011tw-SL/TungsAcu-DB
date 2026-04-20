"""一次性執行：升級 acupoint_images 表的欄位"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "dongzhen_new.db"

conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

cols = [row[1] for row in cur.execute("PRAGMA table_info(acupoint_images)").fetchall()]

if "image_data" not in cols:
    cur.execute("ALTER TABLE acupoint_images ADD COLUMN image_data TEXT")
    print("新增 image_data 欄位")

if "figure_ref" not in cols:
    cur.execute("ALTER TABLE acupoint_images ADD COLUMN figure_ref TEXT")
    print("新增 figure_ref 欄位")

if "match_method" not in cols:
    cur.execute("ALTER TABLE acupoint_images ADD COLUMN match_method TEXT")
    print("新增 match_method 欄位")

conn.commit()
conn.close()
print("完成")
