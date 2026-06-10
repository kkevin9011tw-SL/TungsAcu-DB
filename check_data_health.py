#!/usr/bin/env python3
"""CSV 資料健康檢查。

掃描 data/ 下的核心 CSV，找出解析殘留與結構問題：
- 穴位表：必要欄位空白、穴名格式異常（圖X-X 開頭、標點開頭）、重複穴名、
  疑似截斷重複（穴號空白且穴名是同部位另一穴名的片段）、部位代碼對不上部位表、
  穴位圖 / 詳細筆記路徑不存在
- 對針表：必要欄位空白、圖片路徑不存在
- 症狀治療：必要欄位空白

只報告、不修改資料。ERROR 表示應修正，WARN 表示需人工判斷。
有 ERROR 時 exit code 為 1，可放進 CI 或 commit 前手動執行：

    python3 check_data_health.py
"""
import csv
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def load(name):
    with open(DATA_DIR / name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def is_punct(ch):
    return unicodedata.category(ch).startswith("P") or ch.isspace()


def stem(name):
    """穴名去掉結尾的「穴」字，供片段比對。"""
    return name[:-1] if name.endswith("穴") else name


def check_acupoints(regions):
    rows = load("穴位表.csv")
    region_codes = {r["部位代碼"] for r in regions}
    print(f"穴位表.csv：{len(rows)} 筆")

    by_region = {}
    for i, r in enumerate(rows, start=2):  # 第 1 列是表頭
        name = r["穴名"].strip()
        loc = f"列 {i}（穴名 {name!r}）"

        for col in ("穴名", "部位代碼", "部位"):
            if not r[col].strip():
                err(f"穴位表 {loc}：必要欄位「{col}」空白")
        if not name:
            continue

        if re.match(r"^圖\s*\d", name):
            err(f"穴位表 {loc}：穴名以圖片標題開頭，疑似解析時穴名被圖說取代")
        if is_punct(name[0]):
            err(f"穴位表 {loc}：穴名以標點或空白開頭")
        if is_punct(name[-1]):
            err(f"穴位表 {loc}：穴名以標點或空白結尾")

        if r["部位代碼"].strip() and r["部位代碼"] not in region_codes:
            err(f"穴位表 {loc}：部位代碼 {r['部位代碼']!r} 不在部位表中")

        for col in ("穴位圖", "詳細筆記"):
            p = r[col].strip()
            if p and not (DATA_DIR / p).exists():
                err(f"穴位表 {loc}：{col} 路徑不存在 {p!r}")

        by_region.setdefault(r["部位"], []).append(r)

    # 重複穴名（去掉前後標點後比對，可抓「。耳背穴」對「耳背穴」）
    norm = Counter()
    for r in rows:
        n = r["穴名"].strip()
        n = n.lstrip("".join(c for c in n if is_punct(c)))
        if n:
            norm[n] += 1
    for n, c in sorted(norm.items()):
        if c > 1:
            err(f"穴位表：穴名「{n}」出現 {c} 次（含標點變體）")

    # 疑似截斷重複：穴號（圖號）空白，且穴名片段含在另一個更長的穴名內。
    # 先比同部位，找不到再比全表（如八八的「解穴」對二二的「手解穴」）。
    # 註：穴號欄位放的是書中圖號（如「圖1-8」），兩穴共用一張圖時重複屬正常。
    all_stems = {stem(r["穴名"].strip()) for r in rows if r["穴名"].strip()}
    for region, rs in by_region.items():
        region_stems = {stem(r["穴名"].strip()) for r in rs}
        for r in rs:
            name = r["穴名"].strip()
            s = stem(name)
            if r["穴號"].strip() or not s:
                continue
            hosts = [t for t in region_stems if t != s and s in t]
            scope = "同部位"
            if not hosts:
                hosts = [t for t in all_stems if t != s and s in t]
                scope = "其他部位"
            if hosts:
                host_names = "、".join(f"{h}穴" for h in sorted(hosts)[:3])
                warn(f"穴位表 穴名「{name}」（{region}，無穴號）疑似{scope}「{host_names}」的截斷重複列，請人工比對後合併或刪除")

    blank_num = sum(1 for r in rows if not r["穴號"].strip())
    if blank_num:
        warn(f"穴位表：{blank_num} 筆穴號空白（共 {len(rows)} 筆）")


def check_pairs():
    rows = load("對針表.csv")
    print(f"對針表.csv：{len(rows)} 筆")
    missing_imgs = set()
    for i, r in enumerate(rows, start=2):
        loc = f"列 {i}（穴組 {r['穴組名稱']!r}）"
        for col in ("穴組名稱", "穴名"):
            if not r[col].strip():
                err(f"對針表 {loc}：必要欄位「{col}」空白")
        p = r["圖片"].strip()
        if p and not (DATA_DIR / p).exists():
            missing_imgs.add(p)
    if missing_imgs:
        sample = "、".join(sorted(missing_imgs)[:2])
        err(f"對針表：{len(missing_imgs)} 張圖片路徑不存在（app 會顯示「暫無圖片」），例如 {sample}")


def check_symptoms():
    rows = load("症狀治療.csv")
    print(f"症狀治療.csv：{len(rows)} 筆")
    blank_rec = []
    for i, r in enumerate(rows, start=2):
        if not r["症狀"].strip():
            err(f"症狀治療 列 {i}：必要欄位「症狀」空白")
        if not r["推薦穴位"].strip():
            blank_rec.append(r["症狀"])
    if blank_rec:
        sample = "、".join(blank_rec[:5])
        # 已知的待補狀態，由 症狀標準詞表_待補穴位.csv 追蹤人工補齊
        warn(f"症狀治療：{len(blank_rec)} 筆推薦穴位空白（待人工補齊），例如 {sample}")


def main():
    regions = load("部位表.csv")
    check_acupoints(regions)
    check_pairs()
    check_symptoms()

    print()
    print(f"━━ ERROR {len(errors)} 項 ━━")
    for m in errors:
        print(f"  ✗ {m}")
    print(f"━━ WARN {len(warnings)} 項 ━━")
    for m in warnings:
        print(f"  ⚠ {m}")
    print()
    if errors:
        print("結果：有 ERROR，請修正後重跑。")
        sys.exit(1)
    print("結果：無 ERROR。" + ("（WARN 需人工判斷）" if warnings else ""))


if __name__ == "__main__":
    main()
