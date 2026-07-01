"""
從《楊維傑-董氏奇穴治療析要》原書 markdown 抽取五個區塊，
轉繁體後寫回 治療析要目錄候選.csv，新增五個欄位：
  概述 / 董師原書設穴 / 解析 / 臨床常用選穴 / 解說
"""

import re
import sys
import pandas as pd
import opencc

SOURCE_MD = (
    "/Users/samue11in/Library/CloudStorage/SynologyDrive-中醫資料庫/"
    "AI_Projects/04-書籍資料庫/converted-md/"
    "楊維傑-董氏奇穴治療析要/楊維傑-董氏奇穴治療析要.md"
)
CATALOG_CSV = "/Users/samue11in/Projects/TungsAcu-DB/data/治療析要目錄候選.csv"

# opencc: 簡體 → 繁體（台灣用詞）
_converter = opencc.OpenCC("s2twp")


def to_trad(text: str) -> str:
    if not text:
        return text
    return _converter.convert(text)


def strip_images(text: str) -> str:
    """移除 ![](_page_xxx.jpeg) 之類的圖片行。"""
    return re.sub(r"!\[.*?\]\(.*?\)\s*\n?", "", text)


def clean_block(text: str) -> str:
    text = strip_images(text)
    # 移除多餘空行（最多保留一個連續空行）
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── 章節邊界 regex ─────────────────────────────────────────────────────────
# 各種標題都可能混搭 #/##/###/####，以正文關鍵字匹配為主
_RE_DONG = re.compile(
    r"^#{1,6}\s*[\(（]一[\)）]\s*董[师師]原[书書][设設]穴", re.MULTILINE
)
_RE_JIEXI = re.compile(r"^#{1,6}\s*【解析】", re.MULTILINE)
_RE_LINCHUANG = re.compile(
    r"^#{1,6}\s*(?:[\(（]二[\)）]\s*)?[临臨][床]常用[选選]穴", re.MULTILINE
)
_RE_JIESHOU = re.compile(r"^#{1,6}\s*【解[说說]】", re.MULTILINE)

# 同時捕捉無括號的「董師原書設穴」（少數條目格式特殊）
_RE_DONG_ALT = re.compile(r"^#{1,6}\s*董[师師]原[书書][设設]穴", re.MULTILINE)


def find_section(block: str, pattern, fallback=None):
    """找到 pattern 匹配位置；若沒有則試 fallback；都沒有回傳 -1。"""
    m = pattern.search(block)
    if m:
        return m
    if fallback:
        m2 = fallback.search(block)
        if m2:
            return m2
    return None


def parse_sections(block: str) -> dict:
    """
    把一個症狀的原文區塊拆成五個欄位。
    回傳 dict: 概述 / 董師原書設穴 / 解析 / 臨床常用選穴 / 解說
    所有欄位在找不到內容時回傳空字串。
    """
    result = {k: "" for k in ("概述", "董師原書設穴", "解析", "臨床常用選穴", "解說")}

    # 找各分節標題位置
    m_dong = find_section(block, _RE_DONG, _RE_DONG_ALT)
    m_jiexi = find_section(block, _RE_JIEXI)
    m_linchuang = find_section(block, _RE_LINCHUANG)
    m_jieshou = find_section(block, _RE_JIESHOU)

    # 把有效的錨點排序
    anchors = []
    for key, m in [
        ("董師原書設穴", m_dong),
        ("解析", m_jiexi),
        ("臨床常用選穴", m_linchuang),
        ("解說", m_jieshou),
    ]:
        if m:
            anchors.append((m.start(), m.end(), key))
    anchors.sort(key=lambda x: x[0])

    # 概述 = 第一個錨點之前的文字（跳過症狀標題那一行）
    first_anchor_start = anchors[0][0] if anchors else len(block)
    overview_raw = block[:first_anchor_start]
    # 去掉第一行（症狀標題 heading）
    ov_lines = overview_raw.splitlines()
    body_lines = []
    skip_first = True
    for ln in ov_lines:
        if skip_first and ln.strip().startswith("#"):
            skip_first = False
            continue
        skip_first = False
        body_lines.append(ln)
    result["概述"] = clean_block("\n".join(body_lines))

    # 各分節內容
    for i, (start, end, key) in enumerate(anchors):
        next_start = anchors[i + 1][0] if i + 1 < len(anchors) else len(block)
        # 從標題行結束位置到下一個錨點開始
        content = block[end:next_start]
        result[key] = clean_block(content)

    return result


def extract_block(lines: list[str], start_line: int, end_line: int) -> str:
    """
    抽取原書 lines[start_line-1 : end_line-1]（1-indexed）。
    去掉純空行開頭。
    """
    chunk = lines[start_line - 1 : end_line - 1]
    return "".join(chunk)


def main():
    print("載入原書…")
    with open(SOURCE_MD, encoding="utf-8") as f:
        lines = f.readlines()
    total_lines = len(lines)
    print(f"  → {total_lines} 行")

    print("載入目錄 CSV…")
    df = pd.read_csv(CATALOG_CSV, dtype=str).fillna("")
    print(f"  → {len(df)} 筆")

    # 補上疲勞的來源行（OCR 遺漏標題）
    mask_fatigue = df["目錄症狀"] == "疲勞"
    if df.loc[mask_fatigue, "來源行"].eq("").any():
        df.loc[mask_fatigue, "來源行"] = "8542"
        print("  ⚠️  疲勞 來源行補為 8542")

    # 轉成整數，空的標記 0
    df["_src_line"] = pd.to_numeric(df["來源行"], errors="coerce").fillna(0).astype(int)

    # 計算各條目的結束行：下一個非 0 的起始行 - 1
    src_lines = df["_src_line"].tolist()
    end_lines = []
    for i in range(len(src_lines)):
        # 找下一個有效行
        end = total_lines + 1
        for j in range(i + 1, len(src_lines)):
            if src_lines[j] > 0:
                end = src_lines[j]
                break
        end_lines.append(end)
    df["_end_line"] = end_lines

    # 準備五個新欄位
    for col in ("概述", "董師原書設穴", "解析", "臨床常用選穴", "解說"):
        if col not in df.columns:
            df[col] = ""

    missing = 0
    for idx, row in df.iterrows():
        sl = row["_src_line"]
        el = row["_end_line"]
        symptom = row["目錄症狀"]

        if sl == 0:
            print(f"  ⚠️  [{idx}] {symptom} 無來源行，跳過")
            missing += 1
            continue

        block_raw = extract_block(lines, sl, el)
        sections = parse_sections(block_raw)

        # 繁體轉換
        for col in ("概述", "董師原書設穴", "解析", "臨床常用選穴", "解說"):
            df.at[idx, col] = to_trad(sections[col])

        # 進度
        has = sum(1 for v in sections.values() if v)
        print(f"  [{idx+1:3d}] {symptom[:14]:<14} 行{sl}-{el-1}  {has}/5 個區塊")

    # 移除輔助欄
    df = df.drop(columns=["_src_line", "_end_line"])

    df.to_csv(CATALOG_CSV, index=False, encoding="utf-8-sig")
    print(f"\n✅  已寫入 {CATALOG_CSV}")
    print(f"   {len(df) - missing} 筆完成，{missing} 筆因缺來源行跳過")


if __name__ == "__main__":
    main()
