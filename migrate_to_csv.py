"""
一次性遷移：SQLite (dongzhen_new.db + dongshi.db) → data/*.csv + data/images/ + data/notes/

執行：
  python migrate_to_csv.py

輸出（覆寫）：
  data/穴位表.csv
  data/對針表.csv
  data/症狀治療.csv
  data/部位表.csv
  data/images/{穴號}_{穴名}.jpg     (從 DB 解 base64)
  data/notes/{穴名}.md              (長文：董師原文 + 詮解發揮)
"""
import base64
import csv
import re
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent
# 自 2026-05-12 起 .db 已搬到 archive/，這個腳本只在需要重產 CSV 時跑
DB = BASE / "archive" / "dongzhen_new.db"
DB_OLD = BASE / "archive" / "dongshi.db"
if not DB.exists():
    DB = BASE / "dongzhen_new.db"
if not DB_OLD.exists():
    DB_OLD = BASE / "dongshi.db"

DATA = BASE / "data"
IMG_DIR = DATA / "images"
NOTES_DIR = DATA / "notes"
for d in (DATA, IMG_DIR, NOTES_DIR):
    d.mkdir(exist_ok=True, parents=True)

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row
conn_old = sqlite3.connect(str(DB_OLD))
conn_old.row_factory = sqlite3.Row


def safe_name(s):
    """檔名安全化：去掉 / 和空白"""
    return re.sub(r"[/\\:*?\"<>|\s]", "", s or "")


# ── 部位表 ─────────────────────────────────────────────
print("→ 部位表")
regions = conn.execute(
    "SELECT id, code, name, body_part FROM regions ORDER BY id"
).fetchall()
region_map = {r["id"]: r for r in regions}
with (DATA / "部位表.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["部位代碼", "部位", "身體分區"])
    for r in regions:
        w.writerow([r["code"], r["name"], r["body_part"] or ""])
print(f"  {len(regions)} 列")


# ── 圖片：從 acupoint_images base64 解碼為 jpg ─────────
print("→ 圖片")
images = conn.execute(
    "SELECT acupoint_id, image_data, caption, figure_ref FROM acupoint_images "
    "WHERE image_data IS NOT NULL AND image_data <> ''"
).fetchall()
acupoint_img_path = {}  # ap_id → 相對路徑（取第一張）
img_count = 0
for img in images:
    ap_id = img["acupoint_id"]
    ap_row = conn.execute(
        "SELECT name, figure_ref FROM acupoints WHERE id=?", (ap_id,)
    ).fetchone()
    if not ap_row:
        continue
    fig = img["figure_ref"] or ap_row["figure_ref"] or "noref"
    name = ap_row["name"]
    fname = f"{safe_name(fig)}_{safe_name(name)}.jpg"
    out = IMG_DIR / fname
    # 同穴多張：第 2 張起加 _2/_3
    if out.exists():
        idx = 2
        while True:
            cand = IMG_DIR / f"{safe_name(fig)}_{safe_name(name)}_{idx}.jpg"
            if not cand.exists():
                out = cand
                break
            idx += 1
    out.write_bytes(base64.b64decode(img["image_data"]))
    img_count += 1
    acupoint_img_path.setdefault(ap_id, f"images/{out.name}")
print(f"  {img_count} 張")


# ── 穴位表 + notes/*.md ────────────────────────────────
print("→ 穴位表 + notes/")
acupoints = conn.execute(
    "SELECT * FROM acupoints ORDER BY region_id, id"
).fetchall()

with (DATA / "穴位表.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "穴名", "部位代碼", "部位", "身體分區", "穴號",
        "取穴定位", "針法", "主治關鍵字", "董楊思維", "備註",
        "穴位圖", "詳細筆記", "頁碼",
    ])
    note_count = 0
    for a in acupoints:
        reg = region_map.get(a["region_id"])
        reg_code = reg["code"] if reg else ""
        reg_name = reg["name"] if reg else ""
        reg_body = (reg["body_part"] if reg else "") or ""
        name = a["name"]
        fig = a["figure_ref"] or ""

        # 取穴定位：合併 dong_location + dong_method + location_detail
        loc_parts = [
            (a["dong_location"] or "").strip(),
            (a["dong_method"] or "").strip(),
        ]
        if a["location_detail"] and a["location_detail"].strip() not in loc_parts:
            loc_parts.append(a["location_detail"].strip())
        loc = "；".join(p for p in loc_parts if p)

        needle = (a["dong_needle"] or "").strip()
        kw = (a["indications_kw"] or "").strip()
        new_apps = (a["new_applications"] or "").strip()
        # 董楊思維：取維傑新用前 200 字
        dy = new_apps[:200] + ("…" if len(new_apps) > 200 else "")
        note_caution = (a["dong_caution"] or "").strip()

        img_rel = acupoint_img_path.get(a["id"], "")

        # 詳細筆記 md
        note_path = NOTES_DIR / f"{safe_name(name)}.md"
        note_rel = f"notes/{note_path.name}"

        md_parts = [f"# {name}", ""]
        if fig:
            md_parts += [f"**穴號**：{fig}　**部位**：{reg_name}{('　'+reg_body) if reg_body else ''}", ""]

        # 董師原文
        dong_block = []
        for label, val in [
            ("部位", a["dong_location"]),
            ("主治", a["dong_indications"]),
            ("取穴", a["dong_method"]),
            ("手術", a["dong_needle"]),
            ("注意", a["dong_caution"]),
        ]:
            if val and val.strip():
                dong_block.append(f"- **{label}**：{val.strip()}")
        if dong_block:
            md_parts += ["## 董師原文", *dong_block, ""]

        # 詮解發揮
        ex_block = []
        for label, val in [
            ("穴名闡釋", a["name_explanation"]),
            ("維傑新用 / 董楊思維", a["new_applications"]),
            ("解說及發揮", a["commentary"]),
            ("比較", a["comparison_text"]),
            ("引申", a["extension_text"]),
        ]:
            if val and val.strip():
                ex_block += [f"### {label}", val.strip(), ""]
        if ex_block:
            md_parts += ["## 詮解發揮", *ex_block]

        if a["anatomy"] and a["anatomy"].strip():
            md_parts += ["## 現代解剖", a["anatomy"].strip(), ""]

        if a["page_number"]:
            md_parts += [f"---", f"《穴位詮釋解》p.{a['page_number']}"]

        md_text = "\n".join(md_parts).rstrip() + "\n"
        # 只有當 md 有實質內容時才寫檔；否則 note_rel 留空
        if any([dong_block, ex_block, a["anatomy"], a["page_number"]]):
            note_path.write_text(md_text, encoding="utf-8")
            note_count += 1
        else:
            note_rel = ""

        w.writerow([
            name, reg_code, reg_name, reg_body, fig,
            loc, needle, kw, dy, note_caution,
            img_rel, note_rel, a["page_number"] or "",
        ])
print(f"  穴位 {len(acupoints)} 列、notes/ {note_count} 檔")


# ── 對針表（從 dongshi.db 過濾出區位易象，繁體統一）─────
print("→ 對針表")
try:
    import opencc
    cc = opencc.OpenCC("s2twp")
    def t(s):
        return cc.convert(s or "")
except Exception:
    def t(s):
        return s or ""

pair_rows = conn_old.execute("""
    SELECT point1, point2, indication, theory, needle_method,
           MIN(page_number) as page_number, COUNT(*) as freq
    FROM acupoint_pairs
    WHERE source LIKE '%區位易象特效對針%'
    GROUP BY point1, point2
    ORDER BY freq DESC, point1
""").fetchall()

with (DATA / "對針表.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["穴組名稱", "穴位", "主治關鍵字", "排序", "理論", "針法", "頁碼"])
    for rank, p in enumerate(pair_rows, start=1):
        p1, p2 = t(p["point1"]), t(p["point2"])
        ind = t(p["indication"])
        # 穴組名稱：去掉「穴」字串接
        combo_name = (p1.replace("穴", "") + p2.replace("穴", ""))
        w.writerow([
            combo_name, f"{p1},{p2}", ind, rank,
            t(p["theory"]), t(p["needle_method"]), p["page_number"] or "",
        ])
print(f"  {len(pair_rows)} 列")


# ── 症狀治療表（dongshi.db symptom_treatments）─────────
print("→ 症狀治療表")
sym_rows = conn_old.execute("""
    SELECT s.name as symptom, st.treatment, st.source, st.page_number
    FROM symptoms s JOIN symptom_treatments st ON s.id=st.symptom_id
    WHERE st.source LIKE '楊維傑-%'
    ORDER BY st.source, s.name
""").fetchall()

with (DATA / "症狀治療.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["症狀", "推薦穴位", "來源", "頁碼"])
    for s in sym_rows:
        book = s["source"].replace("楊維傑-楊維傑", "").replace("楊維傑-", "")
        w.writerow([t(s["symptom"]), t(s["treatment"]), book, s["page_number"] or ""])
print(f"  {len(sym_rows)} 列")

print()
print("✅ 完成。所有檔在 data/")
print("   下一步：開啟 data/穴位表.csv 用 Excel/Numbers 確認，再進 Phase 2 改寫 app.py")
