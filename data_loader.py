"""
CSV/MD 後端載入層。供 app.py 取代原本的 SQLite 查詢函式。

慣例：
- 所有 DataFrame loader 用 @st.cache_data 快取
- 寫入 CSV 後呼叫 invalidate_cache() 清快取
- 「id」是 DataFrame row index + 1（穩定隨著 CSV 行順序）
"""
from __future__ import annotations
import re
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
CSV_ACUPOINTS = DATA_DIR / "穴位表.csv"
CSV_PAIRS = DATA_DIR / "對針表.csv"
CSV_SYMPTOMS = DATA_DIR / "症狀治療.csv"
CSV_REGIONS = DATA_DIR / "部位表.csv"
CSV_SYMPTOM_STANDARDS = DATA_DIR / "症狀標準詞表.csv"
CSV_SYMPTOM_MAPPINGS = DATA_DIR / "症狀映射表.csv"
IMG_DIR = DATA_DIR / "images"
NOTES_DIR = DATA_DIR / "notes"


# ── 基礎載入 ─────────────────────────────────────────────────────────────
@st.cache_data
def load_acupoints_df() -> pd.DataFrame:
    df = pd.read_csv(CSV_ACUPOINTS, dtype=str).fillna("")
    df.insert(0, "id", df.index + 1)
    return df


@st.cache_data
def load_regions_df() -> pd.DataFrame:
    return pd.read_csv(CSV_REGIONS, dtype=str).fillna("")


@st.cache_data
def load_pairs_df() -> pd.DataFrame:
    df = pd.read_csv(CSV_PAIRS, dtype=str).fillna("")
    if "目錄排序" in df.columns:
        df["目錄排序"] = pd.to_numeric(df["目錄排序"], errors="coerce").fillna(9999).astype(int)
    else:
        df["目錄排序"] = 9999
    df["排序"] = df["目錄排序"]
    return df


@st.cache_data
def load_symptoms_df() -> pd.DataFrame:
    return pd.read_csv(CSV_SYMPTOMS, dtype=str).fillna("")


@st.cache_data
def load_symptom_standards_df() -> pd.DataFrame:
    df = pd.read_csv(CSV_SYMPTOM_STANDARDS, dtype=str).fillna("")
    df["排序"] = pd.to_numeric(df["排序"], errors="coerce").fillna(9999).astype(int)
    return df


@st.cache_data
def load_symptom_mappings_df() -> pd.DataFrame:
    return pd.read_csv(CSV_SYMPTOM_MAPPINGS, dtype=str).fillna("")


def invalidate_cache():
    load_acupoints_df.clear()
    load_regions_df.clear()
    load_pairs_df.clear()
    load_symptoms_df.clear()
    load_symptom_standards_df.clear()
    load_symptom_mappings_df.clear()
    load_note.clear()


# ── 部位 ─────────────────────────────────────────────────────────────────
def list_regions():
    """回傳 [(code, name, body_part), ...]，依 CSV 行序"""
    df = load_regions_df()
    return [tuple(r) for r in df[["部位代碼", "部位", "身體分區"]].itertuples(index=False)]


def region_by_code(code: str):
    df = load_regions_df()
    row = df[df["部位代碼"] == code]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def acupoints_in_region(code: str):
    """同一部位的穴位（保持 CSV 行序）"""
    df = load_acupoints_df()
    return df[df["部位代碼"] == code]


# ── 穴位 ─────────────────────────────────────────────────────────────────
def get_acupoint(ap_id: int) -> dict:
    df = load_acupoints_df()
    row = df[df["id"] == ap_id]
    if row.empty:
        return {}
    return row.iloc[0].to_dict()


def get_acupoint_by_name(name: str) -> dict:
    df = load_acupoints_df()
    row = df[df["穴名"] == name]
    if row.empty:
        # 容錯：去掉「穴」
        bare = name.replace("穴", "")
        row = df[df["穴名"].str.replace("穴", "") == bare]
    if row.empty:
        return {}
    return row.iloc[0].to_dict()


def same_acupoint_refs(text: str) -> list[dict]:
    """解析「同XX穴」類主治關鍵字，回傳可跳轉的穴位列。"""
    if not text or "同" not in text or "穴" not in text:
        return []
    refs: list[dict] = []
    seen = set()
    for target in re.findall(r"同([^，,、；;及又\s]+穴)", text):
        row = get_acupoint_by_name(target)
        if row and row.get("穴名") not in seen:
            seen.add(row.get("穴名"))
            refs.append(row)
    return refs


def search_acupoints_df(keyword: str) -> pd.DataFrame:
    df = load_acupoints_df()
    if not keyword:
        return df.head(0)
    mask = (
        df["穴名"].str.contains(keyword, na=False)
        | df["主治關鍵字"].str.contains(keyword, na=False)
        | df["董楊思維"].str.contains(keyword, na=False)
        | df["穴號"].str.contains(keyword, na=False)
        | df["備註"].str.contains(keyword, na=False)  # 別名（又名腎關、內九、肺叉…）寫在備註
    )
    return df[mask].head(80)


def resolve_symptom_query(keyword: str) -> list[str]:
    """把使用者輸入轉成正式症狀詞與相關別名，保留原輸入作 fallback。"""
    keyword = (keyword or "").strip()
    if not keyword:
        return []
    terms = [keyword]
    std = load_symptom_standards_df()
    mappings = load_symptom_mappings_df()

    exact = mappings[mappings["關鍵字"].str.casefold() == keyword.casefold()]
    for value in exact["標準症狀"].tolist():
        if value and value not in terms:
            terms.append(value)

    exact_std = std[std["標準症狀"].str.casefold() == keyword.casefold()]
    for value in exact_std["標準症狀"].tolist():
        if value and value not in terms:
            terms.append(value)

    partial = mappings[
        mappings["關鍵字"].str.contains(keyword, case=False, na=False, regex=False)
        | mappings["標準症狀"].str.contains(keyword, case=False, na=False, regex=False)
    ]
    for col in ("標準症狀", "關鍵字"):
        for value in partial[col].tolist():
            if value and value not in terms:
                terms.append(value)
    return terms[:20]


def standardize_keywords(keywords: list[str]) -> tuple[list[str], list[str]]:
    """將原主治關鍵字拆成正式症狀詞與未映射補充詞。"""
    std_names = set(load_symptom_standards_df()["標準症狀"].tolist())
    mappings = load_symptom_mappings_df()
    formal: list[str] = []
    supplemental: list[str] = []

    for kw in keywords:
        kw = (kw or "").strip()
        if not kw:
            continue
        mapped: list[str] = []
        if kw in std_names:
            mapped.append(kw)

        exact = mappings[mappings["關鍵字"].str.casefold() == kw.casefold()]
        for value in exact["標準症狀"].tolist():
            if value in std_names and value not in mapped:
                mapped.append(value)

        if mapped:
            for value in mapped:
                if value not in formal:
                    formal.append(value)
        elif kw not in supplemental:
            supplemental.append(kw)

    return formal, supplemental


def standardize_text_keywords(text: str) -> list[str]:
    """從長句主治文字中抓出可對齊的正式症狀詞。"""
    text = text or ""
    if not text:
        return []
    found: list[str] = []
    std = load_symptom_standards_df().sort_values("排序")
    mappings = load_symptom_mappings_df()
    for _, row in std.iterrows():
        name = row["標準症狀"]
        if name and name in text and name not in found:
            found.append(name)

    for _, row in mappings.iterrows():
        keyword = row.get("關鍵字", "")
        target = row.get("標準症狀", "")
        if keyword and target and keyword in text and target not in found:
            found.append(target)
    filtered: list[str] = []
    for term in sorted(found, key=len, reverse=True):
        if any(term != kept and term in kept for kept in filtered):
            continue
        filtered.append(term)
    return sorted(filtered, key=found.index)[:12]


def search_symptoms_in_acupoints(keyword: str) -> pd.DataFrame:
    """依標準詞/映射詞搜出含此關鍵字主治的穴位。"""
    df = load_acupoints_df()
    terms = resolve_symptom_query(keyword)
    if not terms:
        return df.head(0)
    mask = pd.Series(False, index=df.index)
    for term in terms:
        mask = mask | df["主治關鍵字"].str.contains(term, na=False, regex=False)
        mask = mask | df["董楊思維"].str.contains(term, na=False, regex=False)
    return df[mask].head(80)


# ── 對針 ─────────────────────────────────────────────────────────────────
@st.cache_data
def pair_groups_df() -> pd.DataFrame:
    df = load_pairs_df().sort_values(["目錄排序", "穴組名稱", "穴名"])
    groups = []
    for (order, name), group in df.groupby(["目錄排序", "穴組名稱"], sort=False):
        group = group.reset_index(drop=True)
        first = group.iloc[0].to_dict()
        first["第一穴"] = group.iloc[0]["穴名"]
        first["第二穴"] = group.iloc[1]["穴名"] if len(group) > 1 else ""
        first["穴位"] = "、".join(group["穴名"].tolist())
        first["排序"] = int(order)
        groups.append(first)
    return pd.DataFrame(groups).fillna("")


def pair_rows_for_name(pair_name: str) -> pd.DataFrame:
    df = load_pairs_df()
    if not pair_name:
        return df.head(0)
    row = df[df["穴組名稱"] == pair_name]
    if row.empty:
        return df.head(0)
    return row.sort_values(["目錄排序", "穴名"])


def all_pair_combos():
    """回傳所有對針穴組名稱，依目錄排序"""
    df = pair_groups_df().sort_values(["目錄排序", "穴組名稱"])
    return df["穴組名稱"].tolist()


def search_pairs_df(keyword: str) -> pd.DataFrame:
    df = pair_groups_df()
    if not keyword:
        return df.head(0)
    terms = resolve_symptom_query(keyword)
    mask = (
        df["穴組名稱"].str.contains(keyword, na=False, regex=False)
        | df["穴位"].str.contains(keyword, na=False, regex=False)
        | df["大類"].str.contains(keyword, na=False, regex=False)
        | df["次分類"].str.contains(keyword, na=False, regex=False)
    )
    for term in terms:
        mask = mask | df["主治關鍵字"].str.contains(term, na=False, regex=False)
    return df[mask].sort_values(["目錄排序", "穴組名稱"]).head(40)


def pairs_for_acupoint(name: str) -> pd.DataFrame:
    """含此穴的對針組合"""
    df = pair_groups_df()
    bare = name.replace("穴", "")
    mask = (
        df["穴位"].str.contains(bare, na=False, regex=False)
        | df["穴位"].str.contains(name, na=False, regex=False)
        | df["穴組名稱"].str.contains(bare, na=False, regex=False)
    )
    return df[mask].sort_values(["目錄排序", "穴組名稱"])


def find_pair(p1: str, p2: str) -> dict | None:
    df = load_pairs_df()
    target = {p1.replace("穴", ""), p2.replace("穴", "")}
    for (order, name), group in df.groupby(["目錄排序", "穴組名稱"], sort=False):
        parts = {p.strip().replace("穴", "") for p in group["穴名"].tolist()}
        if parts == target:
            row = pair_groups_df()[pair_groups_df()["穴組名稱"] == name]
            if not row.empty:
                return row.iloc[0].to_dict()
            return group.iloc[0].to_dict()
    return None


# ── 症狀治療 ─────────────────────────────────────────────────────────────
def symptoms_for_acupoint(name: str) -> pd.DataFrame:
    df = load_symptoms_df()
    bare = name.replace("穴", "")
    mask = df["推薦穴位"].str.contains(bare, na=False) | df["推薦穴位"].str.contains(name, na=False)
    return df[mask]


def split_symptom_rows_by_book(df: pd.DataFrame):
    """把症狀治療結果按書籍分桶：(common, pain, others)"""
    common = df[df["來源"].str.contains("常見病", na=False)]
    pain = df[df["來源"].str.contains("痛證|痛症", na=False, regex=True)]
    used = pd.concat([common, pain]).index
    others = df.drop(used)
    # 排除區位易象（已在對針 tab 顯示）
    others = others[~others["來源"].str.contains("區位易象", na=False)]
    return common, pain, others


# ── 詳細筆記（md）─────────────────────────────────────────────────────────
@st.cache_data
def load_note(note_path: str) -> str:
    if not note_path:
        return ""
    p = DATA_DIR / note_path
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def extract_md_section(md: str, heading: str) -> str:
    """抽取 ## 標題 區塊內容（直到下一個 ## 或檔尾）"""
    if not md:
        return ""
    pattern = rf"^##\s+{re.escape(heading)}\s*$"
    lines = md.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(pattern, line):
            start = i + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return "\n".join(lines[start:end]).strip()


# ── 圖片 ─────────────────────────────────────────────────────────────────
def image_abs_path(img_rel: str) -> Path | None:
    if not img_rel:
        return None
    p = DATA_DIR / img_rel
    return p if p.exists() else None


# ── 主治關鍵字解析 ────────────────────────────────────────────────────────
def split_kw(s: str) -> list[str]:
    if not s:
        return []
    parts = re.split(r"[，,、；;]+", s)
    return [p.strip() for p in parts if p.strip()]


# ── 預設清單 ─────────────────────────────────────────────────────────────
SYMPTOM_CATEGORY_ORDER = [
    "痛症", "內科", "頭面頸", "五官科", "婦兒科", "皮膚外科", "其他疾病",
]


@st.cache_data
def default_symptom_groups():
    df = load_symptom_standards_df().sort_values("排序")
    buckets = {n: [] for n in SYMPTOM_CATEGORY_ORDER}
    extras: dict[str, list[str]] = {}
    for _, row in df.iterrows():
        name = row.get("標準症狀", "")
        category = row.get("分類", "") or "其他疾病"
        if not name:
            continue
        if category in buckets:
            buckets[category].append(name)
        else:
            extras.setdefault(category, []).append(name)
    out = []
    for bucket in SYMPTOM_CATEGORY_ORDER:
        items = buckets[bucket]
        if items:
            out.append((bucket, items))
    for bucket, items in extras.items():
        if items:
            out.append((bucket, items))
    return out


# ── 寫入：直接改 CSV（admin 編輯用）─────────────────────────────────────
def update_acupoint_row(ap_id: int, fields: dict):
    df = load_acupoints_df().copy()
    idx = df.index[df["id"] == ap_id]
    if len(idx) == 0:
        return False
    for col, val in fields.items():
        if col in df.columns:
            df.at[idx[0], col] = val
    # 去掉 helper id 欄再寫回
    out = df.drop(columns=["id"])
    out.to_csv(CSV_ACUPOINTS, index=False, encoding="utf-8-sig")
    invalidate_cache()
    return True


def set_acupoint_image(ap_id: int, image_rel_path: str):
    return update_acupoint_row(ap_id, {"穴位圖": image_rel_path})


def create_acupoint_row(fields: dict) -> int:
    """新增一列穴位。回傳新 id（=新 row index+1）。"""
    df = load_acupoints_df().drop(columns=["id"])
    new = {col: "" for col in df.columns}
    for k, v in fields.items():
        if k in df.columns:
            new[k] = v
    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
    df.to_csv(CSV_ACUPOINTS, index=False, encoding="utf-8-sig")
    invalidate_cache()
    return len(df)  # 新 id = 新總列數


def delete_acupoint_row(ap_id: int) -> bool:
    df = load_acupoints_df()
    if not (df["id"] == ap_id).any():
        return False
    name = df.loc[df["id"] == ap_id, "穴名"].iloc[0]
    out = df[df["id"] != ap_id].drop(columns=["id"])
    out.to_csv(CSV_ACUPOINTS, index=False, encoding="utf-8-sig")
    # 連帶刪 notes/{name}.md
    safe = re.sub(r"[/\\:*?\"<>|\s]", "", name)
    note_p = NOTES_DIR / f"{safe}.md"
    if note_p.exists():
        note_p.unlink()
    invalidate_cache()
    return True
