#!/usr/bin/env python3
"""一次性遷移（2026-06-10 顥軒校對後）：

A. 刪除 17 筆截斷重複列，刪除前把其 主治關鍵字 併入母穴（去重）。
B. 刪除 4 筆「圖X-X」假條目（內容為下一穴的重複）。
C. 刪除 士耳穴、雙風穴、「指五金穴、指千金穴」（異體字／重複穴組）。
D. 耳背穴：保留「。耳背穴」的內容（木耳穴上三分處），改名為 耳背穴、補 99.07；
   刪除原 耳背穴（耳輪外緣）列。
   腑快穴：保留「鼻角外開五分」列，刪除「人中外開一寸四分」列（為六快穴內容）。
   州穴：刪除。
E. 部位改名：背腰部位 → 十一部位（部位表 + 穴位表，代碼不動）。

被刪列的 notes 檔移到 data/notes/_merged_fragments/ 留存。
"""
import csv
import shutil
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
ARCHIVE = DATA_DIR / "notes" / "_merged_fragments"

# 碎片 → 母穴（主治關鍵字併入對象）
MERGE_INTO = {
    "五穴": "手五金穴", "千穴": "手千金穴", "人穴": "人士穴",
    "英穴": "首英穴", "雲穴": "雲白穴", "硬穴": "火硬穴",
    "主穴": "火主穴", "菊穴": "火菊穴", "四花穴": "四花裡穴",
    "姐妹穴": "姐妹一穴", "全穴": "火全穴", "前下穴": "金前下穴",
    "中九穴": "中九里穴", "內通穴": "內通山穴", "上穴": "上裡穴",
    "四腑穴": "四腑一穴", "馬穴": "馬金水穴",
}
DELETE_PLAIN = {
    "圖4-4 首英穴", "圖4-10 地宗穴", "圖7-6 正士穴", "圖7-26 足千金穴",
    "士耳穴", "雙風穴", "指五金穴、指千金穴", "州穴",
}


def split_kw(s):
    import re
    return [p.strip() for p in re.split(r"[，,、；;]+", s) if p.strip()]


def main():
    ARCHIVE.mkdir(exist_ok=True)
    path = DATA_DIR / "穴位表.csv"
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    by_name = {}
    for r in rows:
        by_name.setdefault(r["穴名"].strip(), []).append(r)

    merged_report, kept = [], []
    deleted_names = []

    # A：先把碎片關鍵字併入母穴
    for frag, host in MERGE_INTO.items():
        if frag not in by_name or host not in by_name:
            print(f"⚠ 找不到 {frag} 或 {host}，跳過")
            continue
        f_kw = split_kw(by_name[frag][0]["主治關鍵字"])
        h_row = by_name[host][0]
        h_kw = split_kw(h_row["主治關鍵字"])
        new = [k for k in f_kw if k not in h_kw and not k.startswith("同")]
        if new:
            h_row["主治關鍵字"] = "，".join(h_kw + new)
            merged_report.append(f"{frag} → {host}：併入 {len(new)} 個關鍵字（{('、'.join(new[:4]))}…）" if len(new) > 4 else f"{frag} → {host}：併入 {('、'.join(new))}")

    to_delete = set(MERGE_INTO) | DELETE_PLAIN

    for r in rows:
        name = r["穴名"].strip()
        if name in to_delete:
            deleted_names.append(name)
            continue
        # D-1：耳背穴雙列——刪「耳輪之外緣」那筆，保留另一筆
        if name == "耳背穴" and "耳輪" in r["取穴定位"]:
            deleted_names.append("耳背穴（耳輪外緣版）")
            continue
        # D-2：腑快穴雙列——刪「人中…一寸四分」那筆（六快穴內容）
        if name == "腑快穴" and "一寸四分" in r["取穴定位"]:
            deleted_names.append("腑快穴（人中外開版＝六快內容）")
            continue
        # D-1：「。耳背穴」改名 耳背穴、補 99.07
        if name == "。耳背穴":
            r["穴名"] = "耳背穴"
            r["穴號"] = "99.07"
            if r["詳細筆記"].strip() == "notes/。耳背穴.md":
                r["詳細筆記"] = "notes/耳背穴.md"
        # E：背腰部位 → 十一部位
        if r["部位"] == "背腰部位":
            r["部位"] = "十一部位"
        kept.append(r)

    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(kept)

    # 部位表改名
    rpath = DATA_DIR / "部位表.csv"
    with open(rpath, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rfields = reader.fieldnames
        rrows = list(reader)
    for r in rrows:
        if r["部位"] == "背腰部位":
            r["部位"] = "十一部位"
    with open(rpath, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rfields)
        w.writeheader()
        w.writerows(rrows)

    # notes 檔處理：被刪列的筆記移到 _merged_fragments；。耳背穴.md 改名
    for name in list(MERGE_INTO) + ["五穴", "州穴", "士耳穴", "雙風穴"]:
        src = DATA_DIR / "notes" / f"{name}.md"
        if src.exists():
            shutil.move(str(src), str(ARCHIVE / src.name))
    old_eb = DATA_DIR / "notes" / "。耳背穴.md"
    new_eb = DATA_DIR / "notes" / "耳背穴.md"
    if old_eb.exists():
        if new_eb.exists():
            shutil.move(str(new_eb), str(ARCHIVE / "耳背穴（耳輪外緣版）.md"))
        shutil.move(str(old_eb), str(new_eb))

    print(f"刪除 {len(deleted_names)} 列：{deleted_names}")
    print(f"保留 {len(kept)} 列")
    print("關鍵字合併：")
    for m in merged_report:
        print(f"  {m}")


if __name__ == "__main__":
    main()
