"""
董氏奇穴穴位詮釋解 — 檢索工具
資料來源：楊維傑醫師著作《董氏奇穴穴位詮釋解》及其他著作
"""
import sqlite3
from pathlib import Path
import streamlit as st

BASE      = Path(__file__).parent
DB_PATH   = BASE / "dongzhen_new.db"
DB_OLD    = BASE / "dongshi.db"

st.set_page_config(
    page_title="董氏奇穴",
    page_icon="🫙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────
st.markdown("""
<style>
.ap-card {
    background: var(--background-color, #1e1e1e);
    border: 1px solid #333;
    border-left: 4px solid #2e86de;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 6px 0;
}
.ap-name { font-size: 1.15em; font-weight: bold; color: #5ba4e5; }
.ap-indications { font-size: 0.88em; color: #aaa; margin-top: 4px; line-height: 1.5; }
.detail-section {
    background: #111;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 8px 0;
}
.field-label { color: #2e86de; font-weight: bold; font-size: 0.9em; margin-bottom: 4px; }
.field-value { color: #ddd; font-size: 0.95em; line-height: 1.7; }
.region-badge {
    display: inline-block;
    background: #1a3a5c; color: #5ba4e5;
    border-radius: 4px; padding: 2px 10px;
    font-size: 0.82em; margin-bottom: 8px;
}
.pair-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
}
.pair-points { font-size: 1.05em; font-weight: bold; color: #79c0ff; }
.pair-indication { color: #cdd9e5; font-size: 0.92em; margin: 4px 0; }
.source-tag { color: #768390; font-size: 0.82em; }
.sym-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
}
.sym-name { color: #cdd9e5; font-size: 0.95em; }
.sym-treatment { color: #79c0ff; font-size: 0.92em; margin: 4px 0; }
</style>
""", unsafe_allow_html=True)


# ── DB connections ────────────────────────────────────
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


# ── 資料查詢 ──────────────────────────────────────────
@st.cache_data
def load_regions():
    return q("SELECT id, code, name, body_part FROM regions ORDER BY id")

@st.cache_data
def load_acupoints_by_region(region_id):
    return q("""
        SELECT id, name, dong_indications, dong_location
        FROM acupoints WHERE region_id=? ORDER BY id
    """, (region_id,))

@st.cache_data
def search_acupoints(keyword):
    like = f"%{keyword}%"
    return q("""
        SELECT a.id, a.name, a.dong_indications, r.name
        FROM acupoints a JOIN regions r ON a.region_id=r.id
        WHERE a.dong_indications LIKE ? OR a.new_applications LIKE ?
           OR a.commentary LIKE ? OR a.name LIKE ?
        ORDER BY
            CASE WHEN a.name LIKE ? THEN 0
                 WHEN a.dong_indications LIKE ? THEN 1
                 ELSE 2 END, a.id
        LIMIT 60
    """, (like, like, like, like, like, like))

@st.cache_data
def load_acupoint(ap_id):
    conn = get_conn()
    SQL = """
        SELECT a.*, r.name as region_name, r.body_part as region_body
        FROM acupoints a JOIN regions r ON a.region_id=r.id WHERE a.id=?
    """
    cur = conn.execute(SQL, (ap_id,))
    row = cur.fetchone()
    if not row:
        return None, {}
    cols = [d[0] for d in cur.description]
    return row, dict(zip(cols, row))

@st.cache_data
def load_pairs_for_acupoint(name: str):
    """從舊資料庫找此穴的對針組合"""
    bare = name.replace("穴", "")
    like = f"%{bare}%"
    return qo("""
        SELECT point1, point2, indication, theory, needle_method, source, page_number
        FROM acupoint_pairs
        WHERE (point1 LIKE ? OR point2 LIKE ?)
          AND source LIKE '楊維傑-%'
        ORDER BY source
        LIMIT 40
    """, (like, like))

@st.cache_data
def load_symptoms_for_acupoint(name: str):
    """從舊資料庫找此穴出現的症狀主治記錄"""
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
def load_symptom_acupoints(symptom_kw: str):
    """症狀模式：搜尋症狀關鍵字 → 列出穴位"""
    like = f"%{symptom_kw}%"
    return q("""
        SELECT DISTINCT a.id, a.name, a.dong_indications, r.name
        FROM acupoints a JOIN regions r ON a.region_id=r.id
        WHERE a.dong_indications LIKE ? OR a.new_applications LIKE ?
        ORDER BY a.id LIMIT 60
    """, (like, like))


# ── 穴位詳情 ──────────────────────────────────────────
def show_acupoint_detail(ap_id: int):
    _, d = load_acupoint(ap_id)
    if not d:
        st.error("找不到此穴位")
        return

    ap_name = d.get("name", "")

    region_label = d.get('region_name', '') + ('　' + d.get('region_body','') if d.get('region_body') else '')
    page_num = d.get('page_number')
    page_badge = f"　<span style='color:#888;font-size:0.85em'>《董氏奇穴穴位詮釋解》p.{page_num}</span>" if page_num else ""
    st.markdown(f"<div class='region-badge'>📍 {region_label}</div>",
                unsafe_allow_html=True)
    st.markdown(f"# {ap_name}{page_badge}", unsafe_allow_html=True)

    tab_dong, tab_jie, tab_sym, tab_pairs = st.tabs(
        ["📜 董師原文", "🔬 詮解發揮", "💊 其他書籍主治", "🔗 對針組合"]
    )

    # ── 董師原文 ──
    with tab_dong:
        for label, key in [
            ("部位", "dong_location"),
            ("主治", "dong_indications"),
            ("取穴", "dong_method"),
            ("手術", "dong_needle"),
            ("注意", "dong_caution"),
        ]:
            val = d.get(key, "")
            if val:
                st.markdown(f"""
                <div class="detail-section">
                  <div class="field-label">{label}</div>
                  <div class="field-value">{val}</div>
                </div>""", unsafe_allow_html=True)

    # ── 詮解發揮 ──
    with tab_jie:
        for label, key in [
            ("穴名闡釋",  "name_explanation"),
            ("定位及取穴","location_detail"),
            ("現代解剖",  "anatomy"),
            ("維傑新用",  "new_applications"),
            ("解說及發揮","commentary"),
            ("比較",      "comparison_text"),
            ("引申",      "extension_text"),
        ]:
            val = d.get(key, "")
            if val:
                st.markdown(f"""
                <div class="detail-section">
                  <div class="field-label">{label}</div>
                  <div class="field-value">{val}</div>
                </div>""", unsafe_allow_html=True)

    # ── 其他書籍主治 ──
    with tab_sym:
        rows = load_symptoms_for_acupoint(ap_name)
        if not rows:
            st.info("其他著作中未找到此穴的症狀主治記錄")
        else:
            st.caption(f"以下資料來自楊維傑醫師其他著作，共 {len(rows)} 筆")
            cur_src = None
            for sym_name, treatment, source, page_num in rows:
                book = source.replace("楊維傑-楊維傑", "").replace("楊維傑-", "")
                if book != cur_src:
                    st.markdown(f"**📖 {book}**")
                    cur_src = book
                page_tag = f"<span style='color:#888;font-size:0.8em'>　p.{page_num}</span>" if page_num else ""
                st.markdown(f"""
                <div class="sym-card">
                  <div class="sym-name">🩺 {sym_name}{page_tag}</div>
                  <div class="sym-treatment">推薦穴位：{treatment}</div>
                </div>""", unsafe_allow_html=True)

    # ── 對針組合 ──
    with tab_pairs:
        rows = load_pairs_for_acupoint(ap_name)
        if not rows:
            st.info("其他著作中未找到含此穴的對針組合")
        else:
            st.caption(f"以下資料來自楊維傑醫師其他著作，共 {len(rows)} 筆")
            cur_src = None
            for p1, p2, indication, theory, method, source, page_num in rows:
                book = source.replace("楊維傑-楊維傑", "").replace("楊維傑-", "")
                if book != cur_src:
                    st.markdown(f"**📖 {book}**")
                    cur_src = book
                page_tag = f"　p.{page_num}" if page_num else ""
                with st.expander(f"**{p1}  ✦  {p2}**　｜　{(indication or '')[:50]}{page_tag}"):
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**穴1：** {p1}")
                    c2.markdown(f"**穴2：** {p2}")
                    if indication: st.markdown(f"**主治：** {indication}")
                    if theory:     st.markdown(f"**理論：** {theory}")
                    if method:     st.markdown(f"**針法：** {method}")
                    if page_num:   st.caption(f"📄 {book} p.{page_num}")

    if st.button("← 返回列表"):
        st.session_state.selected_ap = None
        st.rerun()


# ── 穴位卡片列表 ──────────────────────────────────────
def show_acupoint_list(rows, show_region=False):
    if not rows:
        st.warning("找不到符合的穴位")
        return
    for ap_id, name, indications, extra in rows:
        ind_short = (indications or "")[:80]
        col1, col2 = st.columns([5, 1])
        with col1:
            badge = f"<div class='region-badge'>{extra}</div>" if show_region and extra else ""
            st.markdown(f"""
            <div class="ap-card">
              <div class="ap-name">{name}</div>
              {badge}
              <div class="ap-indications">{ind_short}{"…" if len(indications or "") > 80 else ""}</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.write("")
            st.write("")
            if st.button("查看", key=f"ap_{ap_id}"):
                st.session_state.selected_ap = ap_id
                st.rerun()


# ── 側欄 ──────────────────────────────────────────────
def render_sidebar():
    st.sidebar.title("🫙 董氏奇穴")
    st.sidebar.caption("楊維傑醫師《董氏奇穴穴位詮釋解》")
    st.sidebar.divider()

    mode = st.sidebar.radio(
        "瀏覽方式",
        ["📍 按部位", "💊 按症狀主治"],
        key="sidebar_mode",
    )

    st.sidebar.divider()

    if mode == "📍 按部位":
        for reg_id, code, name, body_part in load_regions():
            count = q1("SELECT COUNT(*) FROM acupoints WHERE region_id=?", (reg_id,))[0]
            if st.sidebar.button(f"{name}　`{count}`", key=f"reg_{reg_id}",
                                 use_container_width=True):
                st.session_state.selected_region = reg_id
                st.session_state.selected_ap     = None
                st.session_state.search_val      = ""
                st.session_state.symptom_val     = ""
                st.rerun()

    else:  # 按症狀主治
        sym_kw = st.sidebar.text_input(
            "輸入症狀關鍵字",
            value=st.session_state.get("symptom_val", ""),
            placeholder="頭痛、失眠、膝痛…",
            key="symptom_input",
        )
        st.session_state.symptom_val     = sym_kw
        st.session_state.selected_region = None
        st.session_state.search_val      = ""

    st.sidebar.divider()
    total = q1("SELECT COUNT(*) FROM acupoints")[0]
    st.sidebar.caption(f"共 {total} 個穴位")


# ── 主程式 ────────────────────────────────────────────
def main():
    for key, default in [
        ("selected_ap", None), ("selected_region", None),
        ("search_val", ""),    ("symptom_val", ""),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    render_sidebar()

    # 詳情頁優先
    if st.session_state.selected_ap:
        show_acupoint_detail(st.session_state.selected_ap)
        return

    mode = st.session_state.get("sidebar_mode", "📍 按部位")

    # ── 症狀主治模式 ──
    if mode == "💊 按症狀主治":
        sym_kw = st.session_state.get("symptom_val", "")
        st.markdown("## 💊 按症狀主治找穴位")
        if sym_kw:
            results = load_symptom_acupoints(sym_kw)
            st.markdown(f"**症狀「{sym_kw}」— 找到 {len(results)} 個穴位**")
            show_acupoint_list(results, show_region=True)
        else:
            st.info("在左側輸入症狀關鍵字，例如：頭痛、失眠、膝痛")
        return

    # ── 部位模式 ──
    keyword = st.text_input(
        "🔍 輸入症狀或穴名搜尋",
        value=st.session_state.search_val,
        placeholder="頭痛、膝痛、靈骨…",
    )
    st.session_state.search_val = keyword
    st.divider()

    if keyword:
        results = search_acupoints(keyword)
        st.markdown(f"**搜尋「{keyword}」— 找到 {len(results)} 個穴位**")
        show_acupoint_list(results, show_region=True)

    elif st.session_state.selected_region:
        region = q1("SELECT name, body_part FROM regions WHERE id=?",
                    (st.session_state.selected_region,))
        st.markdown(f"### {region[0]}　<small style='color:#888'>{region[1]}</small>",
                    unsafe_allow_html=True)
        rows = load_acupoints_by_region(st.session_state.selected_region)
        show_acupoint_list([(r[0], r[1], r[2], r[3]) for r in rows])

    else:
        st.markdown("## 歡迎使用董氏奇穴檢索工具")
        st.markdown("左側選擇部位瀏覽穴位，或在上方輸入關鍵字搜尋")
        st.divider()
        regions = load_regions()
        cols = st.columns(4)
        for i, (reg_id, code, name, body_part) in enumerate(regions):
            count = q1("SELECT COUNT(*) FROM acupoints WHERE region_id=?", (reg_id,))[0]
            cols[i % 4].metric(name, f"{count} 穴")

if __name__ == "__main__":
    main()
