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

# OCR 原文路徑（供「原始段落」展開用）
_OCR_BASE = Path(
    "/Users/samue11in/Library/CloudStorage/SynologyDrive-中醫資料庫"
    "/AI_Projects/inbox/output"
)
_OCR_PARTS = [
    _OCR_BASE / f"dongzhen_quanshi_part{i}/dongzhen_quanshi/hybrid_auto/dongzhen_quanshi.md"
    for i in range(1, 5)
]

st.set_page_config(
    page_title="董氏奇穴",
    page_icon="☯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Google Fonts + 全站 CSS ───────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@300;400;500;600;700&family=Noto+Sans+TC:wght@300;400;500&display=swap" rel="stylesheet">
<style>
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
  --tag-bg:       rgba(219,168,76,.13);
  --tag-border:   rgba(196,147,58,.4);
}

/* 全站字型 */
html, body, [class*="css"] {
  font-family: 'Noto Sans TC', sans-serif;
  color: var(--ink);
}
h1,h2,h3,h4 {
  font-family: 'Noto Serif TC', serif;
  color: var(--vermillion);
}

/* Sidebar 底色 */
[data-testid="stSidebar"] {
  background-color: var(--parchment-dk) !important;
  border-right: 2px solid var(--divider);
}
[data-testid="stSidebar"] * {
  font-family: 'Noto Sans TC', sans-serif;
  color: var(--ink) !important;
}

/* 主區底色 */
[data-testid="stAppViewContainer"] > .main {
  background-color: var(--parchment);
}
[data-testid="block-container"] {
  background-color: var(--parchment);
  padding-top: 1.5rem;
}

/* Sidebar 按鈕：部位色塊 */
.region-btn button {
  background: var(--parchment) !important;
  border: 1px solid var(--divider) !important;
  border-left: 4px solid var(--gold) !important;
  color: var(--ink) !important;
  font-family: 'Noto Serif TC', serif !important;
  font-weight: 500 !important;
  text-align: left !important;
  border-radius: 4px !important;
  margin: 2px 0 !important;
}
.region-btn button:hover {
  background: var(--parchment-dk) !important;
  border-left-color: var(--vermillion) !important;
}
.region-btn-active button {
  background: var(--parchment-dk) !important;
  border-left: 4px solid var(--vermillion) !important;
  font-weight: 700 !important;
}

/* Sidebar 穴位列表項目 */
.ap-item button {
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid var(--divider) !important;
  color: var(--ink-lt) !important;
  text-align: left !important;
  padding: 4px 8px !important;
  font-size: 0.92em !important;
  border-radius: 0 !important;
  width: 100% !important;
}
.ap-item button:hover {
  color: var(--vermillion) !important;
  background: var(--tag-bg) !important;
}

/* 詳情面板：穴名區 */
.ap-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--divider);
}
.ap-figure-ref {
  font-family: 'Noto Serif TC', serif;
  font-size: 1.1em;
  color: var(--gold);
  font-weight: 500;
  white-space: nowrap;
  padding-top: 6px;
  min-width: 52px;
}
.ap-title {
  font-family: 'Noto Serif TC', serif;
  font-size: 2em;
  font-weight: 700;
  color: var(--vermillion);
  line-height: 1.1;
}
.ap-region-badge {
  display: inline-block;
  background: var(--tag-bg);
  border: 1px solid var(--tag-border);
  color: var(--ink-lt);
  border-radius: 4px;
  padding: 2px 10px;
  font-size: 0.8em;
  margin-top: 4px;
}

/* 關鍵字標籤 */
.kw-container { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0; }
.kw-tag {
  background: var(--tag-bg);
  border: 1px solid var(--tag-border);
  color: var(--ink-lt);
  border-radius: 20px;
  padding: 3px 12px;
  font-size: 0.88em;
  cursor: pointer;
  transition: all .15s;
}
.kw-tag:hover { background: var(--gold-lt); color: white; border-color: var(--gold); }

/* 詳情區塊 */
.detail-section {
  background: rgba(255,255,255,0.55);
  border: 1px solid var(--divider);
  border-left: 4px solid var(--gold);
  border-radius: 6px;
  padding: 14px 18px;
  margin: 10px 0;
}
.detail-section.vermillion { border-left-color: var(--vermillion); }
.field-label {
  font-family: 'Noto Serif TC', serif;
  color: var(--vermillion);
  font-weight: 600;
  font-size: 0.88em;
  letter-spacing: .06em;
  margin-bottom: 6px;
}
.field-value {
  color: var(--ink);
  font-size: 0.95em;
  line-height: 1.8;
}

/* 來源區塊 */
.source-block {
  background: rgba(255,255,255,0.35);
  border: 1px solid var(--divider);
  border-radius: 6px;
  padding: 12px 16px;
  margin: 8px 0;
  font-size: 0.88em;
  color: var(--ink-mute);
}

/* Streamlit 預設 input 美化 */
[data-testid="stTextInput"] input {
  background: rgba(255,255,255,0.7) !important;
  border: 1px solid var(--divider) !important;
  color: var(--ink) !important;
  border-radius: 6px !important;
}
[data-testid="stSelectbox"] > div {
  background: rgba(255,255,255,0.7) !important;
  border: 1px solid var(--divider) !important;
  border-radius: 6px !important;
}

/* 分隔線 */
hr { border-color: var(--divider) !important; }

/* 隱藏 Streamlit 預設 header/footer */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }
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
    vals = list(fields.values()) + [ap_id]
    conn.execute(f"UPDATE acupoints SET {set_clause} WHERE id=?", vals)
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
def search_acupoints(keyword):
    like = f"%{keyword}%"
    return q("""
        SELECT a.id, a.name, a.figure_ref, r.name as region_name,
               a.indications_kw, a.dong_indications
        FROM acupoints a JOIN regions r ON a.region_id=r.id
        WHERE a.dong_indications LIKE ? OR a.new_applications LIKE ?
           OR a.commentary LIKE ? OR a.name LIKE ? OR a.indications_kw LIKE ?
        ORDER BY
            CASE WHEN a.name LIKE ? THEN 0
                 WHEN a.indications_kw LIKE ? THEN 1
                 ELSE 2 END, a.id
        LIMIT 60
    """, (like,)*5 + (like,)*2)

@st.cache_data
def search_symptoms(keyword):
    """症狀模式：搜尋關鍵字 → 找穴位"""
    like = f"%{keyword}%"
    return q("""
        SELECT DISTINCT a.id, a.name, a.figure_ref, r.name,
               a.indications_kw, a.dong_indications
        FROM acupoints a JOIN regions r ON a.region_id=r.id
        WHERE a.dong_indications LIKE ? OR a.indications_kw LIKE ?
           OR a.new_applications LIKE ?
        ORDER BY
            CASE WHEN a.indications_kw LIKE ? THEN 0 ELSE 1 END, a.id
        LIMIT 60
    """, (like, like, like, like))

@st.cache_data
def search_pairs(keyword):
    """對針模式：搜尋關鍵字 → 找對針組合"""
    like = f"%{keyword}%"
    return qo("""
        SELECT point1, point2, indication, theory, needle_method,
               GROUP_CONCAT(source, '、') as sources,
               MIN(page_number) as page_number,
               COUNT(*) as freq
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
        return None, {}
    cols = [d[0] for d in cur.description]
    return row, dict(zip(cols, row))

@st.cache_data
def load_acupoint_images(ap_id: int):
    try:
        return q(
            "SELECT image_data, caption, figure_ref FROM acupoint_images WHERE acupoint_id=?",
            (ap_id,)
        )
    except Exception:
        return []

@st.cache_data
def load_pairs_for_acupoint(name: str):
    bare = name.replace("穴", "")
    like = f"%{bare}%"
    return qo("""
        SELECT point1, point2, indication, theory, needle_method,
               GROUP_CONCAT(source, '、') as sources,
               MIN(page_number) as page_number,
               COUNT(*) as freq
        FROM acupoint_pairs
        WHERE (point1 LIKE ? OR point2 LIKE ?)
          AND source LIKE '楊維傑-%'
        GROUP BY point1, point2
        ORDER BY freq DESC, point1
        LIMIT 40
    """, (like, like))

@st.cache_data
def load_symptoms_for_acupoint(name: str):
    bare = name.replace("穴", "")
    like = f"%{bare}%"
    return qo("""
        SELECT s.name, st.treatment, st.source, st.page_number
        FROM symptoms s JOIN symptom_treatments st ON s.id=st.symptom_id
        WHERE st.treatment LIKE ?
          AND st.source LIKE '楊維傑-%'
        ORDER BY st.source, s.name
        LIMIT 60
    """, (like,))

@st.cache_data
def load_ocr_chunk(acupoint_name: str) -> str:
    """從 part1-4 的 OCR md 找到對應穴位的段落文字（快取）。"""
    heading_re = re.compile(
        r"^# (.{1,8}穴)[（(]图[\d\-]+[)）]",
        re.MULTILINE,
    )
    for part_path in _OCR_PARTS:
        if not part_path.exists():
            continue
        text = part_path.read_text(encoding="utf-8")
        matches = list(heading_re.finditer(text))
        for i, m in enumerate(matches):
            name = re.sub(r"[（(].*", "", m.group(1)).strip()
            if name == acupoint_name:
                start = m.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                return text[start:end].strip()
    return ""


# ── 詳情面板 ──────────────────────────────────────────────────────────────────
def show_acupoint_detail(ap_id: int):
    _, d = load_acupoint(ap_id)
    if not d:
        st.error("找不到此穴位")
        return

    name        = d.get("name", "")
    figure_ref  = d.get("figure_ref", "") or ""
    region_name = d.get("region_name", "")
    region_body = d.get("region_body", "")
    page_num    = d.get("page_number")

    # ── 穴名標題 ──
    region_label = region_name + (f"　{region_body}" if region_body else "")
    st.markdown(f"""
    <div class="ap-header">
      <div class="ap-figure-ref">{figure_ref}</div>
      <div>
        <div class="ap-title">{name}</div>
        <div>
          <span class="ap-region-badge">📍 {region_label}</span>
          {"<span class='ap-region-badge' style='margin-left:6px'>《穴位詮釋解》p." + str(page_num) + "</span>" if page_num else ""}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 取穴 + 圖片（並排）──
    images = load_acupoint_images(ap_id)
    col_text, col_img = st.columns([3, 2]) if images else (st.container(), None)

    with col_text:
        location = d.get("dong_location") or d.get("location_detail") or ""
        method   = d.get("dong_method") or ""
        needle   = d.get("dong_needle") or ""
        quixue_parts = [p for p in [location, method, needle] if p]
        if quixue_parts:
            st.markdown(f"""
            <div class="detail-section">
              <div class="field-label">▪ 取穴與針法</div>
              <div class="field-value">{"；".join(quixue_parts)}</div>
            </div>""", unsafe_allow_html=True)

    if images and col_img:
        with col_img:
            for img_data, caption, fig in images:
                img_bytes = _b64.b64decode(img_data)
                st.image(img_bytes, use_container_width=True)
                if fig:
                    st.caption(fig)

    # ── 主治關鍵字（可點擊）──
    kw_raw = d.get("indications_kw") or d.get("dong_indications") or ""
    if kw_raw:
        kws = [k.strip() for k in re.split(r"[，,、；;]+", kw_raw) if k.strip()]
        st.markdown("<div class='field-label' style='margin-top:14px'>▪ 主治關鍵字</div>",
                    unsafe_allow_html=True)
        cols = st.columns(min(len(kws), 6))
        for i, kw in enumerate(kws):
            with cols[i % len(cols)]:
                if st.button(kw, key=f"kw_{ap_id}_{i}", use_container_width=True):
                    st.session_state.mode         = "💊 症狀"
                    st.session_state.symptom_val  = kw
                    st.session_state.selected_ap  = None
                    st.rerun()

    # ── 董楊思維 ──
    dongyangsiwei = d.get("new_applications") or d.get("commentary") or ""
    if dongyangsiwei:
        st.markdown(f"""
        <div class="detail-section vermillion">
          <div class="field-label">▪ 董楊思維</div>
          <div class="field-value">{dongyangsiwei}</div>
        </div>""", unsafe_allow_html=True)

    # ── 備註 ──
    caution = d.get("dong_caution") or ""
    if caution:
        st.markdown(f"""
        <div class="detail-section">
          <div class="field-label">▪ 備註</div>
          <div class="field-value">{caution}</div>
        </div>""", unsafe_allow_html=True)

    # ── 原始段落 ──
    with st.expander("📜 原始文獻段落"):
        chunk = load_ocr_chunk(name)
        if chunk:
            st.text(chunk[:3000] + ("…（截斷）" if len(chunk) > 3000 else ""))
        else:
            st.caption("此穴位暫無 OCR 原文（可能為增補穴位或名稱略有差異）")

    # ── 其他書籍（tabs）──
    st.divider()
    tab_sym, tab_pairs, *tab_admin = st.tabs(
        ["💊 其他著作主治", "🔗 對針組合"]
        + (["✏️ 編輯資料"] if st.session_state.get("admin_mode") else [])
    )

    with tab_sym:
        rows = load_symptoms_for_acupoint(name)
        if not rows:
            st.caption("其他著作中未找到此穴的症狀記錄")
        else:
            st.caption(f"來自楊維傑醫師其他著作，共 {len(rows)} 筆")
            cur_src = None
            for sym_name, treatment, source, pg in rows:
                book = source.replace("楊維傑-楊維傑", "").replace("楊維傑-", "")
                if book != cur_src:
                    st.markdown(f"**📖 {book}**")
                    cur_src = book
                pg_tag = f"<span style='color:var(--ink-mute);font-size:.8em'> p.{pg}</span>" if pg else ""
                st.markdown(f"""
                <div class="source-block">
                  🩺 <strong>{sym_name}</strong>{pg_tag}<br>
                  <span style="color:var(--ink-lt)">推薦穴位：{treatment}</span>
                </div>""", unsafe_allow_html=True)

    with tab_pairs:
        rows = load_pairs_for_acupoint(name)
        if not rows:
            st.caption("其他著作中未找到含此穴的對針組合")
        else:
            st.caption(f"來自楊維傑醫師其他著作，共 {len(rows)} 組，依出現頻次排序")
            for p1, p2, indication, theory, method, sources, pg, freq in rows:
                with st.expander(f"**{p1}  ✦  {p2}**　｜　{(indication or '')[:50]}"):
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**穴1：** {p1}")
                    c2.markdown(f"**穴2：** {p2}")
                    if indication: st.markdown(f"**主治：** {indication}")
                    if theory:     st.markdown(f"**理論：** {theory}")
                    if method:     st.markdown(f"**針法：** {method}")
                    if pg:         st.caption(f"p.{pg}")

    if st.session_state.get("admin_mode") and tab_admin:
        with tab_admin[0]:
            st.caption("⚠️ 修改後直接寫入資料庫，請確認內容正確再儲存")
            edit_fields = [
                ("主治關鍵字", "indications_kw"),
                ("維傑新用／董楊思維", "new_applications"),
                ("解說及發揮", "commentary"),
                ("比較", "comparison_text"),
                ("引申", "extension_text"),
                ("備註／注意", "dong_caution"),
                ("董師原文-部位", "dong_location"),
                ("董師原文-主治", "dong_indications"),
                ("董師原文-取穴", "dong_method"),
                ("董師原文-手術", "dong_needle"),
                ("穴名闡釋", "name_explanation"),
                ("定位及取穴（詳）", "location_detail"),
                ("現代解剖", "anatomy"),
            ]
            edited = {}
            for label, key in edit_fields:
                val = d.get(key, "") or ""
                new_val = st.text_area(label, value=val, height=100, key=f"edit_{ap_id}_{key}")
                if new_val != val:
                    edited[key] = new_val
            if st.button("💾 儲存修改", type="primary", disabled=not edited):
                update_acupoint(ap_id, edited)
                st.success(f"已儲存 {len(edited)} 個欄位")
                st.rerun()
            elif edited:
                st.info(f"有 {len(edited)} 個欄位待儲存")

    st.button("← 返回", on_click=lambda: st.session_state.update(selected_ap=None))


# ── 側邊欄 ────────────────────────────────────────────────────────────────────
def render_sidebar():
    st.sidebar.markdown(
        "<h2 style='font-family:Noto Serif TC,serif;color:#8B3A2A;"
        "margin-bottom:2px;font-size:1.4em'>☯ 董氏奇穴</h2>"
        "<p style='font-size:.78em;color:#8A6347;margin:0'>楊維傑醫師《穴位詮釋解》</p>",
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    mode = st.sidebar.selectbox(
        "瀏覽方式",
        ["📍 穴位", "💊 症狀", "🔗 對針"],
        key="mode",
        label_visibility="collapsed",
    )

    search = st.sidebar.text_input(
        "搜尋",
        placeholder={"📍 穴位": "穴名…", "💊 症狀": "頭痛、失眠、膝痛…", "🔗 對針": "症狀或穴位名…"}.get(mode, ""),
        key="search_input",
        label_visibility="collapsed",
    )

    st.sidebar.divider()

    # ── 穴位模式：部位色塊 + 細項 ──
    if mode == "📍 穴位":
        if not search:
            regions = load_regions()
            sel_reg = st.session_state.get("selected_region")
            for reg_id, code, name, body_part in regions:
                count = q1("SELECT COUNT(*) FROM acupoints WHERE region_id=?", (reg_id,))[0]
                is_active = sel_reg == reg_id
                css_class = "region-btn-active" if is_active else "region-btn"
                st.sidebar.markdown(f"<div class='{css_class}'>", unsafe_allow_html=True)
                label = f"{name}　`{count}`"
                if st.sidebar.button(label, key=f"reg_{reg_id}", use_container_width=True):
                    st.session_state.selected_region = reg_id
                    st.session_state.selected_ap     = None
                    st.rerun()
                st.sidebar.markdown("</div>", unsafe_allow_html=True)
        else:
            # 搜尋模式：在側欄顯示搜尋結果列表
            results = search_acupoints(search)
            st.sidebar.caption(f"找到 {len(results)} 穴")
            for ap_id, name, fig, region_name, kw, _ in results:
                st.sidebar.markdown("<div class='ap-item'>", unsafe_allow_html=True)
                if st.sidebar.button(name, key=f"ap_s_{ap_id}", use_container_width=True):
                    st.session_state.selected_ap = ap_id
                    st.rerun()
                st.sidebar.markdown("</div>", unsafe_allow_html=True)

    # ── 症狀模式：搜尋後顯示穴位列表 ──
    elif mode == "💊 症狀":
        if search:
            results = search_symptoms(search)
            st.sidebar.caption(f"找到 {len(results)} 穴")
            for ap_id, name, fig, region_name, kw, _ in results:
                st.sidebar.markdown("<div class='ap-item'>", unsafe_allow_html=True)
                if st.sidebar.button(name, key=f"ap_sym_{ap_id}", use_container_width=True):
                    st.session_state.selected_ap = ap_id
                    st.rerun()
                st.sidebar.markdown("</div>", unsafe_allow_html=True)
        else:
            st.sidebar.caption("輸入症狀關鍵字查詢穴位")

    # ── 對針模式 ──
    elif mode == "🔗 對針":
        if search:
            results = search_pairs(search)
            st.sidebar.caption(f"找到 {len(results)} 組對針")
            for p1, p2, indication, *_ in results:
                st.sidebar.markdown(
                    f"<div style='font-size:.85em;padding:4px 6px;"
                    f"border-bottom:1px solid var(--divider);color:var(--ink-lt)'>"
                    f"<strong>{p1} ✦ {p2}</strong><br>"
                    f"<span style='font-size:.9em'>{(indication or '')[:40]}</span></div>",
                    unsafe_allow_html=True
                )
        else:
            st.sidebar.caption("輸入症狀或穴位名搜尋對針組合")

    # ── Admin ──
    st.sidebar.divider()
    if st.session_state.get("admin_mode"):
        st.sidebar.success("✏️ 編輯模式")
        if st.sidebar.button("關閉編輯模式", key="close_admin"):
            st.session_state.admin_mode = False
            st.rerun()
    else:
        with st.sidebar.expander("🔐 管理員"):
            pw = st.text_input("密碼", type="password", key="admin_pw")
            if st.button("登入", key="admin_login"):
                if pw == st.secrets.get("admin_password", "admin123"):
                    st.session_state.admin_mode = True
                    st.rerun()
                else:
                    st.error("密碼錯誤")


# ── 主區域 ────────────────────────────────────────────────────────────────────
def render_main():
    mode   = st.session_state.get("mode", "📍 穴位")
    search = st.session_state.get("search_input", "")
    sel_ap = st.session_state.get("selected_ap")

    # 穴位詳情（任何模式下點選穴位都優先顯示）
    if sel_ap:
        show_acupoint_detail(sel_ap)
        return

    # ── 症狀模式 ──
    if mode == "💊 症狀":
        st.markdown("## 💊 按症狀查穴位")
        # 若從主治關鍵字點擊跳轉，session_state.symptom_val 會有值
        kw = st.session_state.get("symptom_val", "") or search
        if kw:
            results = search_symptoms(kw)
            st.markdown(f"**「{kw}」— 找到 {len(results)} 個穴位**")
            _show_acupoint_cards(results)
        else:
            st.info("在左側搜尋框輸入症狀關鍵字，例如：頭痛、失眠、膝痛")
        return

    # ── 對針模式 ──
    if mode == "🔗 對針":
        st.markdown("## 🔗 對針組合查詢")
        if search:
            results = search_pairs(search)
            st.markdown(f"**「{search}」— 找到 {len(results)} 組對針**")
            for p1, p2, indication, theory, method, sources, pg, freq in results:
                with st.expander(f"**{p1}  ✦  {p2}**　｜　{(indication or '')[:60]}"):
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**穴1：** {p1}")
                    c2.markdown(f"**穴2：** {p2}")
                    if indication: st.markdown(f"**主治：** {indication}")
                    if theory:     st.markdown(f"**理論：** {theory}")
                    if method:     st.markdown(f"**針法：** {method}")
                    if pg:         st.caption(f"p.{pg}　（出現 {freq} 次）")
        else:
            st.info("在左側搜尋框輸入症狀或穴位名稱查詢對針組合")
        return

    # ── 穴位模式 ──
    if search:
        results = search_acupoints(search)
        st.markdown(f"**搜尋「{search}」— 找到 {len(results)} 個穴位**")
        _show_acupoint_cards(results)
        return

    sel_reg = st.session_state.get("selected_region")
    if sel_reg:
        region = q1("SELECT name, body_part FROM regions WHERE id=?", (sel_reg,))
        bp = f"　<small style='color:var(--ink-mute)'>{region[1]}</small>" if region[1] else ""
        st.markdown(f"### {region[0]}{bp}", unsafe_allow_html=True)
        rows = load_acupoints_by_region(sel_reg)
        _show_acupoint_cards(
            [(r[0], r[1], r[2], None, r[3], None) for r in rows]
        )
        return

    # ── 首頁 ──
    total = q1("SELECT COUNT(*) FROM acupoints")[0]
    st.markdown(
        f"<h1 style='font-family:Noto Serif TC,serif;color:#8B3A2A'>"
        f"董氏奇穴檢索工具</h1>"
        f"<p style='color:var(--ink-mute)'>楊維傑醫師《董氏奇穴穴位詮釋解》．共 {total} 個穴位</p>",
        unsafe_allow_html=True,
    )
    st.divider()
    regions = load_regions()
    cols = st.columns(4)
    for i, (reg_id, code, name, body_part) in enumerate(regions):
        count = q1("SELECT COUNT(*) FROM acupoints WHERE region_id=?", (reg_id,))[0]
        with cols[i % 4]:
            if st.button(f"**{name}**\n\n{count} 穴", key=f"home_reg_{reg_id}",
                         use_container_width=True):
                st.session_state.selected_region = reg_id
                st.session_state.selected_ap     = None
                st.rerun()


def _show_acupoint_cards(rows):
    """穴位卡片列表（rows: id, name, figure_ref, region_name, kw, indications）"""
    if not rows:
        st.warning("找不到符合的穴位")
        return
    cols = st.columns(3)
    for i, row in enumerate(rows):
        ap_id, name, fig, region_name, kw, indications = row
        display_kw = (kw or indications or "")[:60]
        fig_str = f"<span style='font-size:.8em;color:var(--gold)'>{fig}</span> " if fig else ""
        region_str = (
            f"<span class='ap-region-badge'>{region_name}</span>" if region_name else ""
        )
        with cols[i % 3]:
            st.markdown(f"""
            <div class="detail-section" style="cursor:pointer">
              <div style="font-family:Noto Serif TC,serif;font-size:1.05em;
                          font-weight:600;color:var(--vermillion)">
                {fig_str}{name}
              </div>
              {region_str}
              <div style="font-size:.85em;color:var(--ink-mute);margin-top:6px;
                          line-height:1.6">{display_kw}{"…" if len(kw or indications or "") > 60 else ""}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("查看", key=f"view_{ap_id}_{i}", use_container_width=True):
                st.session_state.selected_ap = ap_id
                st.rerun()


# ── 主程式 ────────────────────────────────────────────────────────────────────
def main():
    for k, v in [
        ("selected_ap", None), ("selected_region", None),
        ("symptom_val", ""), ("admin_mode", False),
    ]:
        st.session_state.setdefault(k, v)

    render_sidebar()
    render_main()


if __name__ == "__main__":
    main()
