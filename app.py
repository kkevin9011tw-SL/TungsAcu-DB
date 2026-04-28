"""
董氏奇穴穴位詮釋解 — 檢索工具
資料來源：楊維傑醫師著作《董氏奇穴穴位詮釋解》及其他著作
"""
import base64 as _b64
import re
import sqlite3
from pathlib import Path

import streamlit as st

BASE    = Path(__file__).parent
DB_PATH = BASE / "dongzhen_new.db"
DB_OLD  = BASE / "dongshi.db"

_OCR_BASE = Path(
    "/Users/samue11in/Library/CloudStorage/SynologyDrive-中醫資料庫"
    "/AI_Projects/inbox/output"
)
_OCR_PARTS = [
    _OCR_BASE / f"dongzhen_quanshi_part{i}/dongzhen_quanshi/hybrid_auto/dongzhen_quanshi.md"
    for i in range(1, 5)
]

MODES = ["📍 穴位", "💊 症狀", "🔗 對針"]

st.set_page_config(
    page_title="董氏奇穴",
    page_icon="☯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS（用 @import，不用 <link>，才不會被 Streamlit 當文字渲染）────────────
def _inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@300;400;500;600;700&family=Noto+Sans+TC:wght@300;400;500&display=swap');

:root {
  --parchment:    #F7EDD8;
  --parchment-dk: #EDD9A3;
  --gold:         #C4933A;
  --gold-lt:      #DBA84C;
  --vermillion:   #8B3A2A;
  --vermillion-dk:#6B2A1A;
  --ink:          #2C1C10;
  --ink-lt:       #5C3D25;
  --ink-mute:     #8A6347;
  --divider:      #D4B887;
  --tag-bg:       rgba(219,168,76,.15);
  --tag-border:   rgba(196,147,58,.45);
}

/* ── 全站底色與字型 ── */
html, body, [class*="css"], .stApp {
  font-family: 'Noto Sans TC', sans-serif !important;
  background-color: var(--parchment) !important;
  color: var(--ink) !important;
}

/* ── 隱藏 Streamlit 預設元素 ── */
#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background-color: var(--parchment-dk) !important;
  border-right: 1px solid var(--divider) !important;
  min-width: 280px !important;
  max-width: 340px !important;
}
[data-testid="stSidebar"] > div:first-child {
  padding-top: 0 !important;
}

/* ── 主區域 ── */
[data-testid="block-container"] {
  background-color: var(--parchment) !important;
  padding: 1.5rem 2rem !important;
  max-width: 900px !important;
}

/* ── 輸入框 ── */
[data-testid="stTextInput"] > div > div > input {
  background: rgba(255,255,255,.7) !important;
  border: 1px solid var(--divider) !important;
  border-radius: 20px !important;
  color: var(--ink) !important;
  font-family: 'Noto Sans TC', sans-serif !important;
  padding: 6px 14px !important;
}
[data-testid="stTextInput"] > div > div > input:focus {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 2px rgba(196,147,58,.2) !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
  background: rgba(255,255,255,.5) !important;
  border: 1px solid var(--divider) !important;
  border-radius: 6px !important;
}

/* ── 分隔線 ── */
hr { border: none !important; border-top: 1px solid var(--divider) !important; margin: 8px 0 !important; }

/* ── Sidebar 部位 pills ── */
button[data-testid="baseButton-secondary"].pill-btn {
  background: rgba(255,255,255,.5) !important;
  border: 1px solid var(--divider) !important;
  border-radius: 16px !important;
  color: var(--ink-lt) !important;
  font-size: .78em !important;
  padding: 2px 8px !important;
}

/* ── Sidebar 穴位列表行 ── */
.ap-row {
  display: flex;
  align-items: center;
  padding: 7px 10px;
  border-bottom: 1px solid rgba(212,184,135,.4);
  cursor: pointer;
  transition: background .12s;
}
.ap-row:hover { background: rgba(196,147,58,.1); }
.ap-row.active { background: var(--parchment-dk); border-left: 3px solid var(--vermillion); }
.ap-code {
  font-size: .75em;
  color: var(--gold);
  font-family: 'Noto Serif TC', serif;
  min-width: 52px;
}
.ap-name-sm {
  flex: 1;
  font-size: .92em;
  color: var(--ink);
  font-family: 'Noto Serif TC', serif;
}
.ap-tag {
  font-size: .68em;
  background: var(--tag-bg);
  border: 1px solid var(--tag-border);
  border-radius: 10px;
  color: var(--ink-mute);
  padding: 1px 6px;
}

/* ── 詳情面板 ── */
.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--divider);
  margin-bottom: 20px;
}
.detail-code-circle {
  width: 60px; height: 60px;
  border: 2px solid var(--gold);
  border-radius: 50%;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  flex-shrink: 0;
  background: var(--tag-bg);
}
.detail-code-num {
  font-family: 'Noto Serif TC', serif;
  font-size: .85em;
  color: var(--gold);
  font-weight: 600;
  line-height: 1.2;
}
.detail-code-label {
  font-size: .6em;
  color: var(--ink-mute);
  letter-spacing: .05em;
}
.detail-title {
  font-family: 'Noto Serif TC', serif;
  font-size: 2.4em;
  font-weight: 700;
  color: var(--vermillion);
  line-height: 1.1;
  margin-bottom: 6px;
}
.detail-badges { display: flex; gap: 8px; flex-wrap: wrap; }
.detail-badge {
  display: inline-block;
  background: var(--tag-bg);
  border: 1px solid var(--tag-border);
  border-radius: 4px;
  padding: 2px 10px;
  font-size: .78em;
  color: var(--ink-lt);
}

/* ── 詳情各區塊 ── */
.section-label {
  font-family: 'Noto Serif TC', serif;
  font-size: .8em;
  font-weight: 600;
  color: var(--ink-mute);
  letter-spacing: .12em;
  text-transform: uppercase;
  border-bottom: 1px solid var(--divider);
  padding-bottom: 4px;
  margin: 20px 0 8px;
}
.section-body {
  font-size: .95em;
  color: var(--ink);
  line-height: 1.85;
}

/* ── 主治 tags ── */
.kw-wrap { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }
.kw-pill {
  background: var(--tag-bg);
  border: 1px solid var(--tag-border);
  border-radius: 20px;
  padding: 4px 14px;
  font-size: .88em;
  color: var(--ink-lt);
  cursor: pointer;
  transition: all .15s;
}
.kw-pill:hover { background: var(--gold-lt, #DBA84C); color: white; }

/* ── 針法卡片 ── */
.needle-card {
  background: rgba(255,255,255,.6);
  border: 1px solid var(--divider);
  border-radius: 8px;
  padding: 12px 16px;
  margin: 6px 0;
}
.needle-row { display: flex; gap: 12px; padding: 4px 0; border-bottom: 1px solid rgba(212,184,135,.3); }
.needle-row:last-child { border-bottom: none; }
.needle-lbl { font-size: .8em; color: var(--gold); font-weight: 600; min-width: 44px; }
.needle-val { font-size: .88em; color: var(--ink); }

/* ── source block ── */
.src-block {
  background: rgba(255,255,255,.4);
  border: 1px solid var(--divider);
  border-radius: 6px;
  padding: 10px 14px;
  margin: 6px 0;
  font-size: .87em;
  color: var(--ink-lt);
  line-height: 1.6;
}

/* ── Streamlit button 覆寫：讓 st.button 不衝突 ── */
[data-testid="stSidebar"] button[kind="secondary"] {
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid rgba(212,184,135,.4) !important;
  border-radius: 0 !important;
  color: var(--ink-lt) !important;
  text-align: left !important;
  padding: 6px 10px !important;
  font-family: 'Noto Sans TC', sans-serif !important;
  font-size: .9em !important;
  width: 100% !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
  color: var(--vermillion) !important;
  background: rgba(196,147,58,.1) !important;
}
</style>
""", unsafe_allow_html=True)


# ── DB ────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_conn():
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)

@st.cache_resource
def get_old_conn():
    return sqlite3.connect(str(DB_OLD), check_same_thread=False)

def q(sql, params=()):
    return get_conn().execute(sql, params).fetchall()

def q1(sql, params=()):
    return get_conn().execute(sql, params).fetchone()

def qo(sql, params=()):
    return get_old_conn().execute(sql, params).fetchall()

def update_acupoint(ap_id: int, fields: dict):
    conn = get_conn()
    set_clause = ", ".join(f"{k}=?" for k in fields)
    conn.execute(f"UPDATE acupoints SET {set_clause} WHERE id=?",
                 list(fields.values()) + [ap_id])
    conn.commit()
    load_acupoint.clear()
    load_acupoints_by_region.clear()
    search_acupoints.clear()


# ── 資料查詢 ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_regions():
    return q("SELECT id, code, name, body_part FROM regions ORDER BY id")

@st.cache_data
def load_acupoints_by_region(region_id):
    return q("""
        SELECT id, name, figure_ref, indications_kw
        FROM acupoints WHERE region_id=? ORDER BY id
    """, (region_id,))

@st.cache_data
def load_all_acupoints():
    return q("""
        SELECT a.id, a.name, a.figure_ref, r.name as rname,
               a.indications_kw, a.dong_indications, r.id as rid
        FROM acupoints a JOIN regions r ON a.region_id=r.id
        ORDER BY a.region_id, a.id
    """)

@st.cache_data
def search_acupoints(keyword):
    like = f"%{keyword}%"
    return q("""
        SELECT a.id, a.name, a.figure_ref, r.name,
               a.indications_kw, a.dong_indications
        FROM acupoints a JOIN regions r ON a.region_id=r.id
        WHERE a.name LIKE ? OR a.indications_kw LIKE ?
           OR a.dong_indications LIKE ? OR a.new_applications LIKE ?
        ORDER BY CASE WHEN a.name LIKE ? THEN 0
                      WHEN a.indications_kw LIKE ? THEN 1 ELSE 2 END, a.id
        LIMIT 80
    """, (like,)*4 + (like,)*2)

@st.cache_data
def search_symptoms(keyword):
    like = f"%{keyword}%"
    return q("""
        SELECT DISTINCT a.id, a.name, a.figure_ref, r.name,
               a.indications_kw, a.dong_indications
        FROM acupoints a JOIN regions r ON a.region_id=r.id
        WHERE a.indications_kw LIKE ? OR a.dong_indications LIKE ?
           OR a.new_applications LIKE ?
        ORDER BY CASE WHEN a.indications_kw LIKE ? THEN 0 ELSE 1 END, a.id
        LIMIT 80
    """, (like,)*3 + (like,))

@st.cache_data
def search_pairs(keyword):
    like = f"%{keyword}%"
    return qo("""
        SELECT point1, point2, indication, theory, needle_method,
               GROUP_CONCAT(source,'、') as sources,
               MIN(page_number) as page_number, COUNT(*) as freq
        FROM acupoint_pairs
        WHERE (indication LIKE ? OR point1 LIKE ? OR point2 LIKE ?)
          AND source LIKE '楊維傑-%'
        GROUP BY point1, point2
        ORDER BY freq DESC, point1
        LIMIT 40
    """, (like, like, like))

@st.cache_data
def load_acupoint(ap_id):
    conn = get_conn()
    cur = conn.execute("""
        SELECT a.*, r.name as region_name, r.body_part as region_body
        FROM acupoints a JOIN regions r ON a.region_id=r.id WHERE a.id=?
    """, (ap_id,))
    row = cur.fetchone()
    if not row:
        return {}
    return dict(zip([d[0] for d in cur.description], row))

@st.cache_data
def load_acupoint_images(ap_id):
    try:
        return q("SELECT image_data, caption, figure_ref FROM acupoint_images WHERE acupoint_id=?", (ap_id,))
    except Exception:
        return []

@st.cache_data
def load_pairs_for_acupoint(name):
    bare, like = name.replace("穴",""), f"%{name.replace('穴','')}%"
    return qo("""
        SELECT point1, point2, indication, theory, needle_method,
               GROUP_CONCAT(source,'、') as sources,
               MIN(page_number) as page_number, COUNT(*) as freq
        FROM acupoint_pairs WHERE (point1 LIKE ? OR point2 LIKE ?)
          AND source LIKE '楊維傑-%'
        GROUP BY point1, point2 ORDER BY freq DESC, point1 LIMIT 40
    """, (like, like))

@st.cache_data
def load_symptoms_for_acupoint(name):
    like = f"%{name.replace('穴','')}%"
    return qo("""
        SELECT s.name, st.treatment, st.source, st.page_number
        FROM symptoms s JOIN symptom_treatments st ON s.id=st.symptom_id
        WHERE st.treatment LIKE ? AND st.source LIKE '楊維傑-%'
        ORDER BY st.source, s.name LIMIT 60
    """, (like,))

@st.cache_data
def load_ocr_chunk(name):
    heading_re = re.compile(r"^# (.{1,8}穴)[（(]图[\d\-]+[)）]", re.MULTILINE)
    for path in _OCR_PARTS:
        if not path.exists(): continue
        text = path.read_text(encoding="utf-8")
        matches = list(heading_re.finditer(text))
        for i, m in enumerate(matches):
            n = re.sub(r"[（(].*","",m.group(1)).strip()
            if n == name:
                end = matches[i+1].start() if i+1 < len(matches) else len(text)
                return text[m.start():end].strip()
    return ""


# ── 詳情面板 ──────────────────────────────────────────────────────────────────
def show_detail(ap_id):
    d = load_acupoint(ap_id)
    if not d:
        st.error("找不到此穴位")
        return

    name       = d.get("name","")
    fig        = d.get("figure_ref","") or ""
    rname      = d.get("region_name","")
    rbody      = d.get("region_body","")
    page_num   = d.get("page_number")

    # ── 標題區 ──
    badge_region = f"<span class='detail-badge'>📍 {rname}{'　'+rbody if rbody else ''}</span>"
    badge_page   = f"<span class='detail-badge'>《穴位詮釋解》p.{page_num}</span>" if page_num else ""
    st.markdown(f"""
<div class="detail-header">
  <div class="detail-code-circle">
    <span class="detail-code-num">{fig}</span>
    <span class="detail-code-label">穴號</span>
  </div>
  <div>
    <div class="detail-title">{name}</div>
    <div class="detail-badges">{badge_region}{badge_page}</div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── 取穴位置 ──
    loc    = d.get("dong_location") or d.get("location_detail") or ""
    method = d.get("dong_method") or ""
    needle = d.get("dong_needle") or ""
    caution= d.get("dong_caution") or ""

    if loc or method or needle:
        st.markdown("<div class='section-label'>取穴位置</div>", unsafe_allow_html=True)
        body_parts = [p for p in [loc, method] if p]
        st.markdown(f"<div class='section-body'>{'；'.join(body_parts)}</div>",
                    unsafe_allow_html=True)
        if needle:
            st.markdown(f"""
<div class="needle-card">
  <div class="needle-row"><span class="needle-lbl">針法</span><span class="needle-val">{needle}</span></div>
</div>""", unsafe_allow_html=True)

    # ── 主治（可點擊 pills）──
    kw_raw = d.get("indications_kw") or d.get("dong_indications") or ""
    if kw_raw:
        kws = [k.strip() for k in re.split(r"[，,、；;]+", kw_raw) if k.strip()]
        st.markdown("<div class='section-label'>主治</div>", unsafe_allow_html=True)
        # 每行最多 6 個
        n_cols = min(len(kws), 6)
        cols = st.columns(n_cols)
        for i, kw in enumerate(kws):
            with cols[i % n_cols]:
                if st.button(kw, key=f"kw_{ap_id}_{i}"):
                    st.session_state._pending_mode    = "💊 症狀"
                    st.session_state._pending_symptom = kw
                    st.session_state.selected_ap      = None
                    st.rerun()

    # ── 董楊思維 ──
    dongyangsiwei = d.get("new_applications") or d.get("commentary") or ""
    if dongyangsiwei:
        st.markdown("<div class='section-label'>董楊思維</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-body'>{dongyangsiwei}</div>",
                    unsafe_allow_html=True)

    # ── 備註 ──
    if caution:
        st.markdown("<div class='section-label'>備註</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-body'>{caution}</div>",
                    unsafe_allow_html=True)

    # ── 圖片 ──
    images = load_acupoint_images(ap_id)
    if images:
        st.markdown("<div class='section-label'>穴位圖</div>", unsafe_allow_html=True)
        img_cols = st.columns(len(images))
        for i, (img_data, caption, fig_r) in enumerate(images):
            with img_cols[i]:
                st.image(_b64.b64decode(img_data), use_container_width=True)
                if fig_r: st.caption(fig_r)

    # ── 原始段落 ──
    with st.expander("📜 原始文獻段落"):
        chunk = load_ocr_chunk(name)
        if chunk:
            st.text(chunk[:3000] + ("…" if len(chunk)>3000 else ""))
        else:
            st.caption("此穴位暫無 OCR 原文")

    # ── 其他著作（tabs）──
    st.markdown("<hr>", unsafe_allow_html=True)
    tab_labels = ["💊 其他著作主治", "🔗 對針組合"]
    if st.session_state.get("admin_mode"):
        tab_labels.append("✏️ 編輯")
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        rows = load_symptoms_for_acupoint(name)
        if not rows:
            st.caption("其他著作未見此穴症狀記錄")
        else:
            st.caption(f"共 {len(rows)} 筆，來自楊維傑醫師其他著作")
            cur_src = None
            for sym, treat, src, pg in rows:
                book = src.replace("楊維傑-楊維傑","").replace("楊維傑-","")
                if book != cur_src:
                    st.markdown(f"**📖 {book}**")
                    cur_src = book
                pg_s = f" <small style='color:var(--ink-mute)'>p.{pg}</small>" if pg else ""
                st.markdown(f"<div class='src-block'>🩺 <b>{sym}</b>{pg_s}<br>推薦穴位：{treat}</div>",
                            unsafe_allow_html=True)

    with tabs[1]:
        rows = load_pairs_for_acupoint(name)
        if not rows:
            st.caption("其他著作未見含此穴之對針組合")
        else:
            st.caption(f"共 {len(rows)} 組，依出現頻次排序")
            for p1, p2, ind, theory, method, srcs, pg, freq in rows:
                with st.expander(f"**{p1} ✦ {p2}**　｜　{(ind or '')[:50]}"):
                    c1,c2 = st.columns(2)
                    c1.markdown(f"**穴1：** {p1}"); c2.markdown(f"**穴2：** {p2}")
                    if ind:    st.markdown(f"**主治：** {ind}")
                    if theory: st.markdown(f"**理論：** {theory}")
                    if method: st.markdown(f"**針法：** {method}")
                    if pg:     st.caption(f"p.{pg}　（出現 {freq} 次）")

    if st.session_state.get("admin_mode") and len(tabs) > 2:
        with tabs[2]:
            st.caption("⚠️ 修改後直接寫入資料庫")
            edit_fields = [
                ("主治關鍵字","indications_kw"),("維傑新用／董楊思維","new_applications"),
                ("解說及發揮","commentary"),("比較","comparison_text"),("引申","extension_text"),
                ("備註","dong_caution"),("董師原文-部位","dong_location"),
                ("董師原文-主治","dong_indications"),("董師原文-取穴","dong_method"),
                ("董師原文-手術","dong_needle"),("穴名闡釋","name_explanation"),
                ("定位及取穴（詳）","location_detail"),("現代解剖","anatomy"),
            ]
            edited = {}
            for label, key in edit_fields:
                val = d.get(key,"") or ""
                nv = st.text_area(label, value=val, height=90, key=f"e_{ap_id}_{key}")
                if nv != val: edited[key] = nv
            if st.button("💾 儲存", type="primary", disabled=not edited):
                update_acupoint(ap_id, edited)
                st.success(f"已儲存 {len(edited)} 個欄位")
                st.rerun()

    st.button("← 返回",
              on_click=lambda: st.session_state.update(selected_ap=None))


# ── 穴位卡片列表（主區域）─────────────────────────────────────────────────────
def show_cards(rows):
    if not rows:
        st.warning("找不到符合的穴位")
        return
    cols = st.columns(3)
    for i, row in enumerate(rows):
        ap_id, name, fig, rname, kw, ind = row[:6]
        snippet = (kw or ind or "")[:55]
        fig_s = f"<span style='font-size:.75em;color:var(--gold)'>{fig}</span> " if fig else ""
        reg_s = f"<span style='font-size:.7em;background:var(--tag-bg);border:1px solid var(--tag-border);border-radius:10px;padding:1px 7px;color:var(--ink-mute)'>{rname}</span>" if rname else ""
        with cols[i % 3]:
            st.markdown(f"""
<div style="background:rgba(255,255,255,.55);border:1px solid var(--divider);
  border-left:4px solid var(--gold);border-radius:6px;padding:12px 14px;margin:4px 0">
  <div style="font-family:'Noto Serif TC',serif;font-size:1.05em;
    font-weight:600;color:var(--vermillion)">{fig_s}{name}</div>
  <div style="margin:3px 0">{reg_s}</div>
  <div style="font-size:.82em;color:var(--ink-mute);margin-top:5px;line-height:1.5">
    {snippet}{"…" if len(kw or ind or "")>55 else ""}
  </div>
</div>""", unsafe_allow_html=True)
            if st.button("查看", key=f"v_{ap_id}_{i}"):
                st.session_state.selected_ap = ap_id
                st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar():
    # ── Header ──
    total = q1("SELECT COUNT(*) FROM acupoints")[0]
    st.sidebar.markdown(f"""
<div style="background:var(--ink);padding:16px 18px;margin:-1rem -1rem 12px">
  <div style="font-family:'Noto Serif TC',serif;font-size:1.15em;
    font-weight:700;color:#F7EDD8">☯ 董氏奇穴查詢系統</div>
  <div style="font-size:.72em;color:var(--gold);margin-top:2px">
    Tung's Acupuncture Points Reference
    <span style="background:var(--vermillion);border-radius:10px;padding:1px 7px;
      margin-left:6px;color:white;font-size:.9em">{total} 穴</span>
  </div>
</div>""", unsafe_allow_html=True)

    # ── 模式切換 ──
    mode_idx = st.session_state.get("mode_idx", 0)
    sel = st.sidebar.selectbox("", MODES, index=mode_idx,
                               key="mode_select", label_visibility="collapsed")
    st.session_state.mode_idx = MODES.index(sel)
    mode = sel

    # ── 搜尋框 ──
    placeholder = {"📍 穴位":"輸入穴位名稱或編號…",
                   "💊 症狀":"輸入症狀關鍵字…",
                   "🔗 對針":"輸入症狀或穴位名稱…"}.get(mode,"")
    search = st.sidebar.text_input("", placeholder=placeholder,
                                   key="search_kw", label_visibility="collapsed")

    st.sidebar.markdown("<hr>", unsafe_allow_html=True)

    # ── 穴位模式：部位 pills + 穴位列表 ──
    if mode == "📍 穴位":
        if not search:
            regions = load_regions()
            sel_reg = st.session_state.get("selected_region")

            # 部位 pills（每行 3 個）
            pills = [(rid, code) for rid, code, name, _ in regions]
            for row_start in range(0, len(pills), 3):
                chunk = pills[row_start:row_start+3]
                cols = st.sidebar.columns(len(chunk))
                for ci, (rid, code) in enumerate(chunk):
                    is_active = sel_reg == rid
                    btn_style = (
                        "background:var(--vermillion)!important;color:white!important;"
                        "border-color:var(--vermillion)!important"
                    ) if is_active else (
                        "background:rgba(255,255,255,.5)!important;"
                        "border:1px solid var(--divider)!important;color:var(--ink-lt)!important"
                    )
                    with cols[ci]:
                        if st.button(code, key=f"pill_{rid}",
                                     help=None, use_container_width=True):
                            st.session_state.selected_region = rid
                            st.session_state.selected_ap     = None
                            st.rerun()

            st.sidebar.markdown("<hr>", unsafe_allow_html=True)

            # 穴位列表：只顯示選中部位，或全部
            if sel_reg:
                rows = load_acupoints_by_region(sel_reg)
                reg_name = q1("SELECT name FROM regions WHERE id=?", (sel_reg,))[0]
                st.sidebar.markdown(
                    f"<div style='font-size:.78em;color:var(--gold);padding:4px 10px;"
                    f"font-family:Noto Serif TC,serif'>{reg_name}</div>",
                    unsafe_allow_html=True)
                for ap_id, name, fig, kw in rows:
                    fig_s = f"{fig} " if fig else ""
                    if st.sidebar.button(f"{fig_s}{name}", key=f"sb_{ap_id}",
                                         use_container_width=True):
                        st.session_state.selected_ap = ap_id
                        st.rerun()
            else:
                st.sidebar.caption("選擇部位瀏覽穴位，或輸入關鍵字搜尋")
        else:
            results = search_acupoints(search)
            st.sidebar.caption(f"找到 {len(results)} 穴")
            for ap_id, name, fig, *_ in results:
                fig_s = f"{fig} " if fig else ""
                if st.sidebar.button(f"{fig_s}{name}", key=f"ss_{ap_id}",
                                     use_container_width=True):
                    st.session_state.selected_ap = ap_id
                    st.rerun()

    # ── 症狀模式 ──
    elif mode == "💊 症狀":
        symptom_kw = st.session_state.get("_pending_symptom","") or search
        if symptom_kw:
            results = search_symptoms(symptom_kw)
            st.sidebar.caption(f"「{symptom_kw}」— {len(results)} 穴")
            for ap_id, name, fig, *_ in results:
                fig_s = f"{fig} " if fig else ""
                if st.sidebar.button(f"{fig_s}{name}", key=f"sym_{ap_id}",
                                     use_container_width=True):
                    st.session_state.selected_ap = ap_id
                    st.rerun()
        else:
            st.sidebar.caption("輸入症狀關鍵字查詢穴位")

    # ── 對針模式 ──
    elif mode == "🔗 對針":
        if search:
            results = search_pairs(search)
            st.sidebar.caption(f"找到 {len(results)} 組對針")
            for p1, p2, ind, *_ in results:
                st.sidebar.markdown(
                    f"<div style='font-size:.82em;padding:5px 8px;border-bottom:"
                    f"1px solid var(--divider);color:var(--ink-lt)'>"
                    f"<b>{p1} ✦ {p2}</b><br>"
                    f"<span style='color:var(--ink-mute)'>{(ind or '')[:35]}</span></div>",
                    unsafe_allow_html=True)
        else:
            st.sidebar.caption("輸入症狀或穴位名搜尋對針組合")

    # ── Admin ──
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    if st.session_state.get("admin_mode"):
        st.sidebar.success("✏️ 編輯模式已開啟")
        if st.sidebar.button("關閉編輯模式", key="close_admin"):
            st.session_state.admin_mode = False
            st.rerun()
    else:
        with st.sidebar.expander("🔐 管理員"):
            pw = st.text_input("密碼", type="password", key="admin_pw")
            if st.button("登入", key="admin_login"):
                if pw == st.secrets.get("admin_password","admin123"):
                    st.session_state.admin_mode = True
                    st.rerun()
                else:
                    st.error("密碼錯誤")


# ── 主區域 ────────────────────────────────────────────────────────────────────
def render_main():
    mode   = MODES[st.session_state.get("mode_idx", 0)]
    search = st.session_state.get("search_kw", "")
    sel_ap = st.session_state.get("selected_ap")

    if sel_ap:
        show_detail(sel_ap)
        return

    if mode == "💊 症狀":
        kw = st.session_state.get("_pending_symptom","") or search
        st.markdown("<div class='section-label'>按症狀查穴位</div>", unsafe_allow_html=True)
        if kw:
            results = search_symptoms(kw)
            st.markdown(f"**「{kw}」— 找到 {len(results)} 個穴位**")
            show_cards(results)
        else:
            st.info("在左側搜尋框輸入症狀關鍵字，例如：頭痛、失眠、膝痛")
        return

    if mode == "🔗 對針":
        st.markdown("<div class='section-label'>對針組合查詢</div>", unsafe_allow_html=True)
        if search:
            results = search_pairs(search)
            st.markdown(f"**「{search}」— 找到 {len(results)} 組對針**")
            for p1, p2, ind, theory, method, srcs, pg, freq in results:
                with st.expander(f"**{p1} ✦ {p2}**　｜　{(ind or '')[:60]}"):
                    c1,c2 = st.columns(2)
                    c1.markdown(f"**穴1：** {p1}"); c2.markdown(f"**穴2：** {p2}")
                    if ind:    st.markdown(f"**主治：** {ind}")
                    if theory: st.markdown(f"**理論：** {theory}")
                    if method: st.markdown(f"**針法：** {method}")
                    if pg:     st.caption(f"p.{pg}　（{freq} 次）")
        else:
            st.info("在左側搜尋框輸入症狀或穴位名查詢對針組合")
        return

    # ── 穴位模式 ──
    if search:
        results = search_acupoints(search)
        st.markdown(f"**搜尋「{search}」— 找到 {len(results)} 個穴位**")
        show_cards(results)
        return

    sel_reg = st.session_state.get("selected_region")
    if sel_reg:
        region = q1("SELECT name, body_part FROM regions WHERE id=?", (sel_reg,))
        bp = f"　<small style='color:var(--ink-mute)'>{region[1]}</small>" if region[1] else ""
        st.markdown(f"<h3 style='font-family:Noto Serif TC,serif;color:var(--vermillion)'>"
                    f"{region[0]}{bp}</h3>", unsafe_allow_html=True)
        rows = load_acupoints_by_region(sel_reg)
        show_cards([(r[0],r[1],r[2],None,r[3],None) for r in rows])
        return

    # ── 首頁 ──
    st.markdown("""
<div style="padding: 20px 0 30px">
  <div style="font-family:'Noto Serif TC',serif;font-size:2.2em;
    font-weight:700;color:var(--vermillion)">董氏奇穴查詢系統</div>
  <div style="color:var(--ink-mute);font-size:.95em;margin-top:6px">
    楊維傑醫師《董氏奇穴穴位詮釋解》及其他著作
  </div>
</div>
<hr>""", unsafe_allow_html=True)

    regions = load_regions()
    cols = st.columns(4)
    for i, (rid, code, name, body_part) in enumerate(regions):
        count = q1("SELECT COUNT(*) FROM acupoints WHERE region_id=?", (rid,))[0]
        with cols[i % 4]:
            st.markdown(f"""
<div style="background:rgba(255,255,255,.55);border:1px solid var(--divider);
  border-top:3px solid var(--gold);border-radius:6px;padding:14px 12px;
  text-align:center;margin:4px 0">
  <div style="font-family:'Noto Serif TC',serif;font-size:1em;
    font-weight:600;color:var(--vermillion)">{name}</div>
  <div style="font-size:.75em;color:var(--ink-mute);margin:2px 0">{body_part or ''}</div>
  <div style="font-size:1.4em;font-weight:700;color:var(--gold);margin-top:4px">{count}</div>
  <div style="font-size:.7em;color:var(--ink-mute)">穴</div>
</div>""", unsafe_allow_html=True)
            if st.button("瀏覽", key=f"home_{rid}", use_container_width=True):
                st.session_state.selected_region = rid
                st.session_state.selected_ap     = None
                st.rerun()


# ── 主程式 ────────────────────────────────────────────────────────────────────
def main():
    _inject_css()

    # 處理 pending mode（主治關鍵字點擊後跳轉）
    if "_pending_mode" in st.session_state:
        pending = st.session_state.pop("_pending_mode")
        st.session_state.mode_idx = MODES.index(pending)
    # 處理 pending symptom
    if "_pending_symptom" in st.session_state and not st.session_state.get("selected_ap"):
        pass  # 保留讓 render_main 讀取

    for k, v in [("selected_ap",None),("selected_region",None),
                 ("mode_idx",0),("admin_mode",False)]:
        st.session_state.setdefault(k, v)

    render_sidebar()
    render_main()

    # 用完 pending_symptom 就清掉
    if "_pending_symptom" in st.session_state and not st.session_state.get("selected_ap"):
        # 若已顯示結果且 search_kw 有值，清 pending
        if st.session_state.get("search_kw"):
            st.session_state.pop("_pending_symptom", None)


if __name__ == "__main__":
    main()
