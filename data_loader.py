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
    df["排序"] = pd.to_numeric(df["排序"], errors="coerce").fillna(99).astype(int)
    return df


@st.cache_data
def load_symptoms_df() -> pd.DataFrame:
    return pd.read_csv(CSV_SYMPTOMS, dtype=str).fillna("")


def invalidate_cache():
    load_acupoints_df.clear()
    load_regions_df.clear()
    load_pairs_df.clear()
    load_symptoms_df.clear()
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


def search_acupoints_df(keyword: str) -> pd.DataFrame:
    df = load_acupoints_df()
    if not keyword:
        return df.head(0)
    mask = (
        df["穴名"].str.contains(keyword, na=False)
        | df["主治關鍵字"].str.contains(keyword, na=False)
        | df["董楊思維"].str.contains(keyword, na=False)
        | df["穴號"].str.contains(keyword, na=False)
    )
    return df[mask].head(80)


def search_symptoms_in_acupoints(keyword: str) -> pd.DataFrame:
    """依關鍵字搜出含此關鍵字主治的穴位"""
    df = load_acupoints_df()
    if not keyword:
        return df.head(0)
    mask = (
        df["主治關鍵字"].str.contains(keyword, na=False)
        | df["董楊思維"].str.contains(keyword, na=False)
    )
    return df[mask].head(80)


# ── 對針 ─────────────────────────────────────────────────────────────────
def all_pair_combos():
    """回傳 [(穴1, 穴2), ...] 依排序欄"""
    df = load_pairs_df().sort_values("排序")
    out = []
    for points in df["穴位"]:
        parts = [p.strip() for p in (points or "").split(",") if p.strip()]
        if len(parts) >= 2:
            out.append((parts[0], parts[1]))
    return out


def search_pairs_df(keyword: str) -> pd.DataFrame:
    df = load_pairs_df()
    if not keyword:
        return df.head(0)
    mask = (
        df["穴組名稱"].str.contains(keyword, na=False)
        | df["穴位"].str.contains(keyword, na=False)
        | df["主治關鍵字"].str.contains(keyword, na=False)
    )
    return df[mask].sort_values("排序").head(40)


def pairs_for_acupoint(name: str) -> pd.DataFrame:
    """含此穴的對針組合"""
    df = load_pairs_df()
    bare = name.replace("穴", "")
    mask = df["穴位"].str.contains(bare, na=False) | df["穴位"].str.contains(name, na=False)
    return df[mask].sort_values("排序")


def find_pair(p1: str, p2: str) -> dict | None:
    df = load_pairs_df()
    target = {p1.replace("穴", ""), p2.replace("穴", "")}
    for _, row in df.iterrows():
        parts = [p.strip().replace("穴", "") for p in (row["穴位"] or "").split(",")]
        if set(parts) == target:
            return row.to_dict()
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
SYMPTOM_REGION_ORDER = [
    "頭面", "眼耳鼻喉", "頸肩", "上肢", "胸背",
    "腰腹", "下肢", "生殖泌尿", "其他",
]


def _symptom_bucket(name: str) -> str:
    rules = [
        ("頭面", ("頭", "面", "顏", "臉", "口", "牙", "舌", "腮", "鼻樑", "鼻骨")),
        ("眼耳鼻喉", ("眼", "目", "耳", "鼻", "喉", "咽", "扁桃", "聲", "聽")),
        ("頸肩", ("頸", "項", "肩", "臂不舉", "落枕")),
        ("上肢", ("手", "肘", "腕", "臂", "肩臂", "指", "掌")),
        ("胸背", ("胸", "心", "肺", "乳", "背", "脊", "肋", "膈", "氣管")),
        ("腰腹", ("腰", "腹", "胃", "腸", "肝", "膽", "脾", "胰", "臍", "小腹")),
        ("下肢", ("腿", "膝", "踝", "腳", "足", "髖", "股", "臀", "下肢")),
        ("生殖泌尿", ("子宮", "月經", "經痛", "白帶", "陰", "卵", "睪丸", "攝護腺",
                  "前列腺", "尿", "腎", "膀胱", "生殖", "不孕")),
    ]
    for bucket, keywords in rules:
        if any(k in name for k in keywords):
            return bucket
    return "其他"


@st.cache_data
def default_symptom_groups():
    df = load_acupoints_df()
    buckets = {n: [] for n in SYMPTOM_REGION_ORDER}
    seen = set()
    for raw in df["主治關鍵字"]:
        for s in split_kw(raw):
            s2 = re.sub(r"\s+", "", s)
            if not s2 or s2 in seen or len(s2) > 12:
                continue
            seen.add(s2)
            buckets[_symptom_bucket(s2)].append(s2)
    out = []
    for bucket in SYMPTOM_REGION_ORDER:
        items = sorted(buckets[bucket])
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
