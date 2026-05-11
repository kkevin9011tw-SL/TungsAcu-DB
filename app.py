"""
董氏奇穴穴位詮釋解 — 檢索工具（CSV 後端版）
資料：data/*.csv + data/notes/*.md + data/images/*.jpg
"""
import base64 as _b64
import re
import shutil
import sys
from pathlib import Path

# 把 script 目錄加進 sys.path（Streamlit 1.30+ 不自動加）
_BASE_DIR = Path(__file__).parent.resolve()
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

import streamlit as st

import data_loader as dl

BASE = Path(__file__).parent
LOGO_PATH = BASE / "assets/logo-seal.png"
EXTRACTED_DIR = BASE / "extracted_images"

MODES = ["📍 穴位", "💊 症狀", "🔗 對針"]

st.set_page_config(
    page_title="董氏奇穴",
    page_icon="☯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── CSS ───────────────────────────────────────────────────────────────────
def _inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@300;400;500;600;700&family=Noto+Sans+TC:wght@300;400;500&display=swap');

:root {
  --parchment:    #F7EDD8;
  --parchment-dk: #EDD9A3;
  --gold:         #C4933A;
  --gold-lt:      #DBA84C;
  --vermillion:   #7B2D1E;
  --vermillion-dk:#5F2116;
  --ink:          #2C1C10;
  --ink-lt:       #5C3D25;
  --ink-mute:     #8A6347;
  --divider:      #D4B887;
  --tag-bg:       rgba(219,168,76,.15);
  --tag-border:   rgba(196,147,58,.45);
}

html, body, [class*="css"], .stApp {
  font-family: 'Noto Sans TC', sans-serif !important;
  background-color: var(--parchment) !important;
  color: var(--ink) !important;
}

#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"] {
  position: fixed !important; top: 0 !important; left: 0 !important; right: 0 !important;
  height: 64px !important;
  background: linear-gradient(90deg, var(--vermillion-dk) 0%, var(--vermillion) 52%, #8C3825 100%) !important;
  box-shadow: 0 2px 14px rgba(44,28,16,.18) !important;
  z-index: 1002 !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] { display: none !important; }

.app-topbar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 1003;
  height: 64px; display: flex; align-items: center; justify-content: space-between;
  gap: 18px; padding: 8px 24px 8px 18px; pointer-events: none;
}
.app-brand { display: flex; align-items: center; gap: 12px; min-width: 0; }
.app-logo {
  width: 42px; height: 42px; border-radius: 6px; object-fit: cover; flex-shrink: 0;
  box-shadow: 0 1px 6px rgba(44,28,16,.22); transform: rotate(90deg);
}
.app-title-wrap { display: flex; flex-direction: column; justify-content: center; min-width: 0; }
.app-title-zh {
  font-family: 'Noto Serif TC', serif; font-size: 1.55em; font-weight: 700;
  color: #F7EDD8; line-height: 1.02; white-space: nowrap;
}
.app-title-en {
  font-size: .58em; letter-spacing: .08em; color: rgba(247,237,216,.8);
  margin-top: 2px; white-space: nowrap;
}
.app-topbar-count {
  background: rgba(247,237,216,.14); border: 1px solid rgba(247,237,216,.26);
  border-radius: 999px; padding: 5px 12px; font-size: .82em; color: #F7EDD8;
  line-height: 1.4; flex-shrink: 0;
}

[data-testid="stSidebar"] {
  background-color: var(--parchment-dk) !important;
  border-right: 1px solid var(--divider) !important;
  min-width: 280px !important; max-width: 340px !important; z-index: 1000 !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 4.2rem !important; }
[data-testid="block-container"] {
  background-color: var(--parchment) !important;
  padding: 5.3rem 2rem 1.5rem !important; max-width: 900px !important;
}

[data-testid="stTextInput"] > div > div > input {
  background: rgba(255,255,255,.7) !important; border: 1px solid var(--divider) !important;
  border-radius: 20px !important; color: var(--ink) !important;
  font-family: 'Noto Sans TC', sans-serif !important; padding: 6px 14px !important;
}
[data-testid="stTextInput"] > div > div > input:focus {
  border-color: var(--gold) !important; box-shadow: 0 0 0 2px rgba(196,147,58,.2) !important;
}
[data-testid="stSelectbox"] > div > div {
  background: rgba(255,255,255,.5) !important; border: 1px solid var(--divider) !important;
  border-radius: 6px !important;
}

hr { border: none !important; border-top: 1px solid var(--divider) !important; margin: 8px 0 !important; }

.detail-header {
  display: flex; align-items: flex-start; gap: 20px;
  padding-bottom: 16px; border-bottom: 2px solid var(--divider); margin-bottom: 20px;
}
.detail-code-circle {
  width: 60px; height: 60px; border: 2px solid var(--gold); border-radius: 50%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  flex-shrink: 0; background: var(--tag-bg);
}
.detail-code-num { font-family: 'Noto Serif TC', serif; font-size: .85em; color: var(--gold); font-weight: 600; line-height: 1.2; }
.detail-code-label { font-size: .6em; color: var(--ink-mute); letter-spacing: .05em; }
.detail-title {
  font-family: 'Noto Serif TC', serif; font-size: 2.4em; font-weight: 700;
  color: var(--vermillion); line-height: 1.1; margin-bottom: 6px;
}
.detail-badges { display: flex; gap: 8px; flex-wrap: wrap; }
.detail-badge {
  display: inline-block; background: var(--tag-bg); border: 1px solid var(--tag-border);
  border-radius: 4px; padding: 2px 10px; font-size: .78em; color: var(--ink-lt);
}

.section-label {
  font-family: 'Noto Serif TC', serif; font-size: .82em; font-weight: 600;
  color: var(--ink-mute); letter-spacing: .1em;
  border-bottom: 1px solid var(--divider); padding-bottom: 5px;
  margin: 26px 0 12px;
}
.section-body { font-size: .95em; color: var(--ink); line-height: 1.85; margin-bottom: 14px; }
.section-body:last-child { margin-bottom: 0; }
.principle-tag {
  display: inline-block; font-family: 'Noto Serif TC', serif; font-size: .78em;
  color: var(--gold); background: var(--tag-bg); border: 1px solid var(--tag-border);
  border-radius: 4px; padding: 1px 8px; margin: 16px 0 6px; letter-spacing: .04em;
}
.principle-tag:first-child { margin-top: 4px; }

[data-baseweb="tab-list"] { margin-top: 8px !important; padding-bottom: 4px !important; }
[data-baseweb="tab-panel"] { padding-top: 6px !important; }

.kw-wrap { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }
.kw-pill {
  background: var(--tag-bg); border: 1px solid var(--tag-border); border-radius: 20px;
  padding: 4px 14px; font-size: .88em; color: var(--ink-lt); cursor: pointer; transition: all .15s;
}
.kw-pill:hover { background: var(--gold-lt, #DBA84C); color: white; }

.needle-card {
  background: rgba(255,255,255,.6); border: 1px solid var(--divider); border-radius: 8px;
  padding: 14px 18px; margin: 8px 0 14px;
}
.needle-row { display: flex; gap: 12px; padding: 4px 0; border-bottom: 1px solid rgba(212,184,135,.3); }
.needle-row:last-child { border-bottom: none; }
.needle-lbl { font-size: .8em; color: var(--gold); font-weight: 600; min-width: 44px; }
.needle-val { font-size: .92em; color: var(--ink); line-height: 1.7; }

.src-block {
  background: rgba(255,255,255,.4); border: 1px solid var(--divider); border-radius: 6px;
  padding: 12px 16px; margin: 10px 0; font-size: .9em; color: var(--ink-lt); line-height: 1.75;
}
.src-block b { color: var(--ink); }
.src-book-title {
  font-family: 'Noto Serif TC', serif; font-size: .92em; color: var(--vermillion);
  font-weight: 600; margin: 18px 0 6px;
}

[data-testid="stExpander"] { margin-bottom: 8px !important; }

[data-testid="stSidebar"] button[kind="secondary"] {
  background: transparent !important; border: none !important;
  border-bottom: 1px solid rgba(212,184,135,.4) !important; border-radius: 0 !important;
  color: var(--ink-lt) !important; text-align: left !important; padding: 6px 10px !important;
  font-family: 'Noto Sans TC', sans-serif !important; font-size: .9em !important; width: 100% !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
  color: var(--vermillion) !important; background: rgba(196,147,58,.1) !important;
}
.sidebar-section-title {
  font-family: 'Noto Serif TC', serif; font-size: .76em; font-weight: 700;
  letter-spacing: .08em; color: var(--ink-mute); margin: 4px 0 8px;
}
.sidebar-preview {
  font-size: .8em; color: var(--ink-mute); line-height: 1.7; padding: 0 4px 6px;
}
</style>
""", unsafe_allow_html=True)


# ── 小工具 ─────────────────────────────────────────────────────────────────
def _img_to_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    ext = path.suffix.lower().lstrip(".") or "png"
    mime = "image/png" if ext == "png" else f"image/{ext}"
    return f"data:{mime};base64,{_b64.b64encode(path.read_bytes()).decode('ascii')}"


# ── 詳情面板 ───────────────────────────────────────────────────────────────
@st.fragment
def show_detail(ap_id: int):
    d = dl.get_acupoint(ap_id)
    if not d:
        st.error("找不到此穴位")
        return

    name = d.get("穴名", "")
    fig = d.get("穴號", "") or ""
    rname = d.get("部位", "")
    rbody = d.get("身體分區", "") or ""
    page = d.get("頁碼", "")

    badge_region = f"<span class='detail-badge'>📍 {rname}{('　'+rbody) if rbody else ''}</span>"
    badge_page = f"<span class='detail-badge'>《穴位詮釋解》p.{page}</span>" if page else ""
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

    loc = d.get("取穴定位", "")
    needle = d.get("針法", "")
    caution = d.get("備註", "")
    kw_raw = d.get("主治關鍵字", "")
    kws = dl.split_kw(kw_raw)
    dy = d.get("董楊思維", "")
    img_rel = d.get("穴位圖", "")
    note_rel = d.get("詳細筆記", "")
    note_md = dl.load_note(note_rel)

    img_abs = dl.image_abs_path(img_rel)

    tab_labels = ["取穴定位", "主治原理", "臨床配伍"]
    if st.session_state.get("admin_mode"):
        tab_labels.append("✏️ 編輯")
    tabs = st.tabs(tab_labels)

    # ── Tab 0：取穴定位 ──
    with tabs[0]:
        col_text, col_img = st.columns([1, 1], gap="large")
        with col_text:
            if loc:
                st.markdown(
                    "<div class='section-label'>位置</div>"
                    f"<div class='section-body'>{loc}</div>",
                    unsafe_allow_html=True,
                )
            if needle:
                st.markdown(
                    "<div class='section-label'>針法</div>"
                    f"<div class='needle-card'>"
                    f"<div class='needle-row'><span class='needle-lbl'>針法</span>"
                    f"<span class='needle-val'>{needle}</span></div></div>",
                    unsafe_allow_html=True,
                )
            if caution:
                st.markdown(
                    "<div class='section-label'>備註</div>"
                    f"<div class='section-body'>{caution}</div>",
                    unsafe_allow_html=True,
                )
        with col_img:
            st.markdown("<div class='section-label'>穴位圖</div>", unsafe_allow_html=True)
            if img_abs:
                st.image(str(img_abs), width=320)
                if fig:
                    st.caption(fig)
            else:
                st.caption("此穴尚無圖")

        # 現代解剖（從 note 抽）
        anatomy = dl.extract_md_section(note_md, "現代解剖")
        if anatomy:
            st.markdown(
                "<div class='section-label'>現代解剖</div>"
                f"<div class='section-body'>{anatomy}</div>",
                unsafe_allow_html=True,
            )

        with st.expander("📜 詳細筆記（董師原文 + 詮解發揮）"):
            if note_md:
                st.markdown(note_md)
            else:
                st.caption("此穴暫無詳細筆記")

    # ── Tab 1：主治原理 ──
    with tabs[1]:
        if kws:
            st.markdown("<div class='section-label'>主治關鍵字</div>", unsafe_allow_html=True)
            n_cols = 4
            cols = st.columns(n_cols)
            for i, kw in enumerate(kws):
                with cols[i % n_cols]:
                    if st.button(kw, key=f"kw_{ap_id}_{i}", use_container_width=True):
                        st.session_state._pending_mode = "💊 症狀"
                        st.session_state._pending_symptom = kw
                        st.session_state._set_search_kw = kw
                        st.session_state.selected_ap = None
                        st.rerun()
        else:
            st.caption("此穴暫無主治關鍵字")

        if dy:
            st.markdown(
                "<div class='section-label'>董楊思維</div>"
                f"<div class='section-body'>{dy}</div>",
                unsafe_allow_html=True,
            )

        # 從 md 抽各區塊
        parts = []
        for label in ("維傑新用 / 董楊思維", "解說及發揮", "比較", "引申", "穴名闡釋"):
            body = dl.extract_md_section(note_md, label) if note_md else ""
            if not body:
                # 在 md 裡這些是 ### 子層，extract_md_section 只抓 ##，要另抓
                pat = rf"^###\s+{re.escape(label)}\s*$"
                if note_md and re.search(pat, note_md, re.MULTILINE):
                    lines = note_md.splitlines()
                    start = None
                    for i, line in enumerate(lines):
                        if re.match(pat, line):
                            start = i + 1
                            break
                    if start is not None:
                        end = len(lines)
                        for j in range(start, len(lines)):
                            if lines[j].startswith("### ") or lines[j].startswith("## "):
                                end = j
                                break
                        body = "\n".join(lines[start:end]).strip()
            if body:
                parts.append((label, body))
        if parts:
            blocks = "".join(
                f"<div class='principle-tag'>{lbl}</div>"
                f"<div class='section-body'>{body}</div>"
                for lbl, body in parts
            )
            st.markdown(
                "<div class='section-label'>原理與發揮</div>" + blocks,
                unsafe_allow_html=True,
            )

    # ── Tab 2：臨床配伍 ──
    with tabs[2]:
        # 對針
        st.markdown("<div class='section-label'>對針</div>", unsafe_allow_html=True)
        pairs = dl.pairs_for_acupoint(name)
        if pairs.empty:
            st.caption("《區位易象特效對針》未見含此穴之對針組合")
        else:
            st.caption(f"共 {len(pairs)} 組，依排序")
            for _, p in pairs.iterrows():
                pts = [x.strip() for x in (p["穴位"] or "").split(",")]
                p1 = pts[0] if pts else ""
                p2 = pts[1] if len(pts) > 1 else ""
                ind = p.get("主治關鍵字", "")
                theory = p.get("理論", "")
                method = p.get("針法", "")
                pg = p.get("頁碼", "")
                with st.expander(f"**{p1} ✦ {p2}**　｜　{(ind or '')[:50]}"):
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**穴1：** {p1}")
                    c2.markdown(f"**穴2：** {p2}")
                    if ind: st.markdown(f"**主治：** {ind}")
                    if theory: st.markdown(f"**理論：** {theory}")
                    if method: st.markdown(f"**針法：** {method}")
                    if pg: st.caption(f"p.{pg}")

        # 常見病 / 痛症 / 其他著作
        sym_df = dl.symptoms_for_acupoint(name)
        common, pain, others = dl.split_symptom_rows_by_book(sym_df)

        def _src_html(df):
            parts = []
            for _, r in df.iterrows():
                pg = r.get("頁碼", "")
                pg_s = f" <small style='color:var(--ink-mute)'>p.{pg}</small>" if pg else ""
                parts.append(
                    f"<div class='src-block'>🩺 <b>{r['症狀']}</b>{pg_s}"
                    f"<br>推薦穴位：{r['推薦穴位']}</div>"
                )
            return "".join(parts)

        if not common.empty:
            st.markdown(
                "<div class='section-label'>常見病</div>" + _src_html(common),
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<div class='section-label'>常見病</div>", unsafe_allow_html=True)
            st.caption("常見病資料暫缺")

        if not pain.empty:
            st.markdown(
                "<div class='section-label'>痛症</div>" + _src_html(pain),
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<div class='section-label'>痛症</div>", unsafe_allow_html=True)
            st.caption("痛症資料暫缺")

        if not others.empty:
            cur_src = None
            chunks = ["<div class='section-label'>其他著作</div>"]
            for src_name, grp in others.groupby("來源", sort=False):
                chunks.append(f"<div class='src-book-title'>📖 {src_name}</div>")
                chunks.append(_src_html(grp))
            st.markdown("".join(chunks), unsafe_allow_html=True)
        else:
            st.markdown("<div class='section-label'>其他著作</div>", unsafe_allow_html=True)
            st.caption("其他著作資料暫缺")

    # ── Tab 3：✏️ 編輯（admin）──
    if st.session_state.get("admin_mode") and len(tabs) > 3:
        with tabs[3]:
            st.caption("⚠️ 修改後直接寫回 data/穴位表.csv")
            edit_fields = [
                ("取穴定位", "取穴定位"),
                ("針法", "針法"),
                ("主治關鍵字", "主治關鍵字"),
                ("董楊思維", "董楊思維"),
                ("備註", "備註"),
                ("穴位圖（相對路徑）", "穴位圖"),
            ]
            edited = {}
            for label, col in edit_fields:
                val = d.get(col, "") or ""
                nv = st.text_area(label, value=val, height=90, key=f"e_{ap_id}_{col}")
                if nv != val:
                    edited[col] = nv
            if st.button("💾 儲存到 CSV", type="primary", disabled=not edited):
                if dl.update_acupoint_row(ap_id, edited):
                    st.success(f"已儲存 {len(edited)} 個欄位到穴位表.csv")
                    st.rerun()
                else:
                    st.error("寫入失敗")

            st.markdown("---")
            st.caption("⚠️ 危險區")
            confirm = st.checkbox(
                f"我確認要從穴位表.csv 永久刪除「{name}」（同時刪 notes/ md 檔）",
                key=f"del_confirm_{ap_id}",
            )
            if st.button("🗑 刪除此穴", key=f"del_{ap_id}", disabled=not confirm):
                if dl.delete_acupoint_row(ap_id):
                    st.session_state.selected_ap = None
                    st.success(f"已刪除 {name}")
                    st.rerun()
                else:
                    st.error("刪除失敗")

    if st.button("← 返回", key=f"detail_back_{ap_id}"):
        st.session_state.selected_ap = None
        st.rerun()


# ── 穴位卡片列表（主區域）──────────────────────────────────────────────────
def show_cards_df(df):
    if df.empty:
        st.warning("找不到符合的穴位")
        return
    cols = st.columns(3)
    for i, (_, row) in enumerate(df.iterrows()):
        ap_id = row["id"]
        name = row["穴名"]
        fig = row.get("穴號", "")
        rname = row.get("部位", "")
        snippet = (row.get("主治關鍵字") or row.get("董楊思維") or "")[:55]
        fig_s = f"<span style='font-size:.75em;color:var(--gold)'>{fig}</span> " if fig else ""
        reg_s = (
            f"<span style='font-size:.7em;background:var(--tag-bg);border:1px solid "
            f"var(--tag-border);border-radius:10px;padding:1px 7px;color:var(--ink-mute)'>"
            f"{rname}</span>"
        ) if rname else ""
        with cols[i % 3]:
            st.markdown(f"""
<div style="background:rgba(255,255,255,.55);border:1px solid var(--divider);
  border-left:4px solid var(--gold);border-radius:6px;padding:12px 14px;margin:4px 0">
  <div style="font-family:'Noto Serif TC',serif;font-size:1.05em;
    font-weight:600;color:var(--vermillion)">{fig_s}{name}</div>
  <div style="margin:3px 0">{reg_s}</div>
  <div style="font-size:.82em;color:var(--ink-mute);margin-top:5px;line-height:1.5">
    {snippet}{"…" if len(row.get('主治關鍵字') or row.get('董楊思維') or '') > 55 else ""}
  </div>
</div>""", unsafe_allow_html=True)
            if st.button("查看", key=f"v_{ap_id}_{i}"):
                st.session_state.selected_ap = int(ap_id)
                st.rerun()


# ── Sidebar ────────────────────────────────────────────────────────────────
def render_sidebar():
    if "_set_search_kw" in st.session_state:
        st.session_state.search_kw = st.session_state.pop("_set_search_kw")
    if "_set_pending_pair" in st.session_state:
        st.session_state._pending_pair = st.session_state.pop("_set_pending_pair")

    mode_idx = st.session_state.get("mode_idx", 0)
    sel = st.sidebar.selectbox("模式切換", MODES, index=mode_idx,
                               key="mode_select", label_visibility="collapsed")
    new_mode_idx = MODES.index(sel)
    prev_mode_idx = st.session_state.get("_prev_mode_idx", new_mode_idx)
    if prev_mode_idx != new_mode_idx:
        for k in ("search_kw", "_pending_symptom", "_pending_pair", "_set_search_kw"):
            st.session_state.pop(k, None)
        st.session_state.selected_ap = None
        st.session_state.selected_region = None
        st.session_state.mode_idx = new_mode_idx
        st.session_state._prev_mode_idx = new_mode_idx
        st.rerun()
    st.session_state.mode_idx = new_mode_idx
    st.session_state._prev_mode_idx = new_mode_idx
    mode = sel

    placeholder = {"📍 穴位": "輸入穴位名稱或編號…",
                   "💊 症狀": "輸入症狀關鍵字…",
                   "🔗 對針": "輸入症狀或穴位名稱…"}.get(mode, "")
    search = st.sidebar.text_input("搜尋", placeholder=placeholder,
                                   key="search_kw", label_visibility="collapsed")
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)

    if mode == "📍 穴位":
        if not search:
            regions = dl.list_regions()
            sel_reg = st.session_state.get("selected_region_code")
            pills = [(code, name) for code, name, _ in regions]
            for row_start in range(0, len(pills), 3):
                chunk = pills[row_start:row_start + 3]
                cols = st.sidebar.columns(len(chunk))
                for ci, (code, _name) in enumerate(chunk):
                    with cols[ci]:
                        if st.button(code, key=f"pill_{code}", use_container_width=True):
                            st.session_state.selected_region_code = code
                            st.session_state.selected_ap = None
                            st.rerun()
            st.sidebar.markdown("<hr>", unsafe_allow_html=True)
            if sel_reg:
                rdf = dl.acupoints_in_region(sel_reg)
                reg_info = dl.region_by_code(sel_reg)
                if reg_info:
                    st.sidebar.markdown(
                        f"<div style='font-size:.78em;color:var(--gold);padding:4px 10px;"
                        f"font-family:Noto Serif TC,serif'>{reg_info['部位']}</div>",
                        unsafe_allow_html=True,
                    )
                for _, r in rdf.iterrows():
                    fig_s = f"{r['穴號']} " if r["穴號"] else ""
                    if st.sidebar.button(f"{fig_s}{r['穴名']}",
                                         key=f"sb_{r['id']}", use_container_width=True):
                        st.session_state.selected_ap = int(r["id"])
                        st.rerun()
            else:
                st.sidebar.caption("選擇部位瀏覽穴位，或輸入關鍵字搜尋")
        else:
            results = dl.search_acupoints_df(search)
            st.sidebar.caption(f"找到 {len(results)} 穴")
            for _, r in results.iterrows():
                fig_s = f"{r['穴號']} " if r["穴號"] else ""
                if st.sidebar.button(f"{fig_s}{r['穴名']}",
                                     key=f"ss_{r['id']}", use_container_width=True):
                    st.session_state.selected_ap = int(r["id"])
                    st.rerun()

    elif mode == "💊 症狀":
        symptom_kw = search or st.session_state.get("_pending_symptom", "")
        if symptom_kw:
            results = dl.search_symptoms_in_acupoints(symptom_kw)
            st.sidebar.caption(f"「{symptom_kw}」— {len(results)} 穴")
            for _, r in results.iterrows():
                fig_s = f"{r['穴號']} " if r["穴號"] else ""
                if st.sidebar.button(f"{fig_s}{r['穴名']}",
                                     key=f"sym_{r['id']}", use_container_width=True):
                    st.session_state.selected_ap = int(r["id"])
                    st.rerun()
        else:
            groups = dl.default_symptom_groups()
            total = sum(len(items) for _, items in groups)
            st.sidebar.caption(f"症狀預設清單，共 {total} 項")
            for section, items in groups:
                st.sidebar.markdown(
                    f"<div class='sidebar-section-title'>{section}</div>",
                    unsafe_allow_html=True,
                )
                preview = "、".join(items[:18]) + ("…" if len(items) > 18 else "")
                st.sidebar.markdown(
                    f"<div class='sidebar-preview'>{preview}</div>",
                    unsafe_allow_html=True,
                )
                selected_symptom = st.sidebar.selectbox(
                    f"{section}預設症狀",
                    [""] + items, index=0,
                    key=f"sym_default_{section}",
                    label_visibility="collapsed",
                )
                if selected_symptom and st.session_state.get("search_kw") != selected_symptom:
                    st.session_state._set_search_kw = selected_symptom
                    st.session_state._pending_symptom = selected_symptom
                    st.session_state.selected_ap = None
                    st.rerun()

    elif mode == "🔗 對針":
        pending_pair = st.session_state.get("_pending_pair")
        if search:
            results = dl.search_pairs_df(search)
            st.sidebar.caption(f"找到 {len(results)} 組對針")
            for _, p in results.iterrows():
                pts = [x.strip() for x in (p["穴位"] or "").split(",")]
                p1 = pts[0] if pts else ""
                p2 = pts[1] if len(pts) > 1 else ""
                ind = p.get("主治關鍵字", "")
                st.sidebar.markdown(
                    f"<div style='font-size:.82em;padding:5px 8px;border-bottom:"
                    f"1px solid var(--divider);color:var(--ink-lt)'>"
                    f"<b>{p1} ✦ {p2}</b><br>"
                    f"<span style='color:var(--ink-mute)'>{(ind or '')[:35]}</span></div>",
                    unsafe_allow_html=True,
                )
        elif pending_pair:
            p1, p2 = pending_pair
            st.sidebar.caption(f"已選對針：{p1} ✦ {p2}")
        else:
            combos = dl.all_pair_combos()
            st.sidebar.caption(f"對針預設清單，共 {len(combos)} 組")
            preview = [f"{a} ✦ {b}" for a, b in combos[:24]]
            st.sidebar.markdown(
                f"<div class='sidebar-preview'>{'<br>'.join(preview)}"
                f"{'<br>…' if len(combos) > 24 else ''}</div>",
                unsafe_allow_html=True,
            )
            options = [""] + [f"{a} ✦ {b}" for a, b in combos]
            selected = st.sidebar.selectbox(
                "預設對針", options, index=0,
                key="pair_default_select", label_visibility="collapsed",
            )
            if selected:
                a, b = selected.split(" ✦ ", 1)
                if st.session_state.get("_pending_pair") != (a, b):
                    st.session_state._set_search_kw = ""
                    st.session_state._set_pending_pair = (a, b)
                    st.rerun()

    # Admin
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    if st.session_state.get("admin_mode"):
        st.sidebar.success("✏️ 編輯模式已開啟")
        if st.sidebar.button("➕ 新增穴位", key="open_create_ap", use_container_width=True):
            st.session_state.create_ap_open = True
            st.session_state.image_review_open = False
            st.rerun()
        if st.sidebar.button("🖼 圖片審核", key="open_image_review", use_container_width=True):
            st.session_state.image_review_open = True
            st.session_state.create_ap_open = False
            st.rerun()
        if st.sidebar.button("關閉編輯模式", key="close_admin"):
            st.session_state.admin_mode = False
            st.session_state.image_review_open = False
            st.session_state.create_ap_open = False
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


# ── 圖片審核（admin）──────────────────────────────────────────────────────
def render_image_review():
    import json
    st.markdown("<div class='section-label'>🖼 穴位圖審核</div>", unsafe_allow_html=True)
    if st.button("← 結束審核", key="exit_review"):
        st.session_state.image_review_open = False
        st.rerun()

    manifest_path = EXTRACTED_DIR / "manifest.json"
    if not manifest_path.exists():
        st.warning("尚未抽圖。先執行：python extract_images_v2.py")
        return
    items = json.loads(manifest_path.read_text(encoding="utf-8"))

    pending = [i for i in items if i.get("status") not in ("adopted", "skipped")]
    adopted = [i for i in items if i.get("status") == "adopted"]
    skipped = [i for i in items if i.get("status") == "skipped"]
    st.caption(
        f"待審核 {len(pending)}　｜　已採用 {len(adopted)}　｜　已跳過 {len(skipped)}　"
        f"｜　共 {len(items)} 張"
    )

    method_opts = ["全部", "caption_fig", "caption_name", "same_page", "noref"]
    sel_method = st.selectbox("比對來源", method_opts, index=0, key="rv_method_filter")
    pool = items if st.checkbox("顯示已處理", key="rv_show_done") else pending
    if sel_method != "全部":
        pool = [i for i in pool if i.get("match_method") == sel_method]

    if not pool:
        st.success("這個過濾條件下沒有待審核項目")
        return

    page_size = 6
    page = st.number_input(
        "頁次", min_value=1,
        max_value=max(1, (len(pool) + page_size - 1) // page_size),
        value=1, step=1, key="rv_page",
    )
    chunk = pool[(page - 1) * page_size: page * page_size]
    st.caption(f"顯示 {(page-1)*page_size+1}–{(page-1)*page_size+len(chunk)} / {len(pool)} 張")

    df_ap = dl.load_acupoints_df()
    name_to_id = {row["穴名"]: int(row["id"]) for _, row in df_ap.iterrows()}
    ap_id_list = list(name_to_id.values())
    id_to_label = {int(row["id"]): f"{row['穴名']} ({row['穴號'] or '-'})"
                   for _, row in df_ap.iterrows()}

    for item in chunk:
        global_idx = items.index(item)
        st.markdown("---")
        col_img, col_meta = st.columns([1, 2])
        img_path = EXTRACTED_DIR / item["file"]
        with col_img:
            if img_path.exists():
                st.image(str(img_path), use_container_width=True)
            else:
                st.error(f"檔案不存在：{item['file']}")
        with col_meta:
            st.markdown(
                f"**part {item['part']}　p.{item['page']}**　"
                f"<small style='color:var(--ink-mute)'>來源：{item.get('match_method','-')}　"
                f"size {int(item['size'][0])}×{int(item['size'][1])}</small>",
                unsafe_allow_html=True,
            )
            cap = item.get("caption", "")
            if cap:
                st.caption(f"caption: {cap[:80]}")
            if item.get("status") == "adopted":
                st.success(f"已採用 → acupoint id={item.get('adopted_to')}")
                continue
            if item.get("status") == "skipped":
                st.info("已跳過")
                continue
            cands = item.get("candidates", [])
            target_id = None
            if cands:
                cand_labels = [
                    f"{c['name']} ({c.get('ref','-')})  [id={c['id']}]"
                    for c in cands
                ]
                idx = st.radio(
                    "候選穴位（自動比對）",
                    list(range(len(cands))),
                    format_func=lambda x: cand_labels[x],
                    key=f"rv_cand_{global_idx}",
                )
                cand_name = cands[idx]["name"]
                target_id = name_to_id.get(cand_name)
            else:
                st.warning("自動無候選，請手動指定")

            with st.expander("手動指定／覆寫穴位"):
                pick = st.selectbox(
                    "選穴位",
                    [None] + ap_id_list,
                    format_func=lambda x: "－" if x is None else id_to_label[x],
                    key=f"rv_pick_{global_idx}",
                )
                if pick:
                    target_id = int(pick)

            b1, b2, b3 = st.columns(3)
            if b1.button("✅ 採用", key=f"rv_adopt_{global_idx}",
                         disabled=target_id is None,
                         use_container_width=True, type="primary"):
                # 複製到 data/images/，寫回 穴位表.csv「穴位圖」欄
                ap_row = df_ap[df_ap["id"] == target_id].iloc[0]
                fig = ap_row["穴號"] or "noref"
                ap_name = ap_row["穴名"]
                safe = re.sub(r"[/\\:*?\"<>|\s]", "", f"{fig}_{ap_name}")
                dst_name = f"{safe}.jpg"
                dst = dl.IMG_DIR / dst_name
                if dst.exists():
                    n = 2
                    while True:
                        c = dl.IMG_DIR / f"{safe}_{n}.jpg"
                        if not c.exists():
                            dst = c
                            break
                        n += 1
                shutil.copyfile(img_path, dst)
                dl.set_acupoint_image(int(target_id), f"images/{dst.name}")
                item["status"] = "adopted"
                item["adopted_to"] = int(target_id)
                manifest_path.write_text(
                    json.dumps(items, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                st.rerun()
            if b2.button("⏭ 跳過", key=f"rv_skip_{global_idx}", use_container_width=True):
                item["status"] = "skipped"
                manifest_path.write_text(
                    json.dumps(items, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                st.rerun()
            if b3.button("🔄 重置", key=f"rv_reset_{global_idx}", use_container_width=True):
                item.pop("status", None)
                item.pop("adopted_to", None)
                manifest_path.write_text(
                    json.dumps(items, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                st.rerun()


# ── 新增穴位（admin）─────────────────────────────────────────────────────
def render_create_acupoint():
    st.markdown("<div class='section-label'>➕ 新增穴位</div>", unsafe_allow_html=True)
    if st.button("← 取消", key="exit_create"):
        st.session_state.create_ap_open = False
        st.rerun()

    regions = dl.list_regions()
    region_codes = [code for code, _, _ in regions]
    region_label = {code: f"{code} - {name}" for code, name, _ in regions}

    with st.form("create_ap_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("穴名 *", placeholder="例：靈骨穴")
            code = st.selectbox("部位代碼 *", region_codes,
                                format_func=lambda x: region_label.get(x, x))
            fig = st.text_input("穴號", placeholder="例：圖2-11")
        with c2:
            kw = st.text_area("主治關鍵字（逗號分隔）", height=70)
            dy = st.text_area("董楊思維（100 字內精華）", height=70)
        loc = st.text_area("取穴定位", height=90)
        needle = st.text_input("針法")
        caution = st.text_input("備註")
        submitted = st.form_submit_button("✅ 建立", type="primary")
        if submitted:
            if not name.strip():
                st.error("穴名不可空白")
            elif name in list(dl.load_acupoints_df()["穴名"]):
                st.error(f"穴名「{name}」已存在")
            else:
                reg_info = dl.region_by_code(code) or {}
                new_id = dl.create_acupoint_row({
                    "穴名": name.strip(),
                    "部位代碼": code,
                    "部位": reg_info.get("部位", ""),
                    "身體分區": reg_info.get("身體分區", ""),
                    "穴號": fig.strip(),
                    "取穴定位": loc,
                    "針法": needle,
                    "主治關鍵字": kw,
                    "董楊思維": dy,
                    "備註": caution,
                    "穴位圖": "",
                    "詳細筆記": "",
                    "頁碼": "",
                })
                st.success(f"已新增「{name}」（id={new_id}）")
                st.session_state.create_ap_open = False
                st.session_state.selected_ap = int(new_id)
                st.rerun()


# ── 主區域 ────────────────────────────────────────────────────────────────
def render_main():
    if st.session_state.get("admin_mode") and st.session_state.get("create_ap_open"):
        render_create_acupoint()
        return
    if st.session_state.get("admin_mode") and st.session_state.get("image_review_open"):
        render_image_review()
        return

    mode = MODES[st.session_state.get("mode_idx", 0)]
    search = st.session_state.get("search_kw", "")
    sel_ap = st.session_state.get("selected_ap")

    if sel_ap:
        show_detail(sel_ap)
        return

    if mode == "💊 症狀":
        kw = search or st.session_state.get("_pending_symptom", "")
        st.markdown("<div class='section-label'>按症狀查穴位</div>", unsafe_allow_html=True)
        if kw:
            results = dl.search_symptoms_in_acupoints(kw)
            st.markdown(f"**「{kw}」— 找到 {len(results)} 個穴位**")
            if st.button("← 返回症狀清單", key="symptom_back"):
                st.session_state._set_search_kw = ""
                st.session_state.pop("_pending_symptom", None)
                st.rerun()
            show_cards_df(results)
        else:
            groups = dl.default_symptom_groups()
            st.info("左側已展開症狀預設清單，可直接點選，或輸入症狀關鍵字查詢。")
            for section, items in groups:
                st.markdown(f"**{section}**")
                st.caption("、".join(items[:24]) + ("…" if len(items) > 24 else ""))
        return

    if mode == "🔗 對針":
        st.markdown("<div class='section-label'>對針組合查詢</div>", unsafe_allow_html=True)
        pending_pair = st.session_state.get("_pending_pair")
        if search:
            results = dl.search_pairs_df(search)
            st.markdown(f"**「{search}」— 找到 {len(results)} 組對針**")
            for _, p in results.iterrows():
                pts = [x.strip() for x in (p["穴位"] or "").split(",")]
                p1 = pts[0] if pts else ""
                p2 = pts[1] if len(pts) > 1 else ""
                ind = p.get("主治關鍵字", "")
                theory = p.get("理論", "")
                method = p.get("針法", "")
                pg = p.get("頁碼", "")
                with st.expander(f"**{p1} ✦ {p2}**　｜　{(ind or '')[:60]}"):
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**穴1：** {p1}")
                    c2.markdown(f"**穴2：** {p2}")
                    if ind: st.markdown(f"**主治：** {ind}")
                    if theory: st.markdown(f"**理論：** {theory}")
                    if method: st.markdown(f"**針法：** {method}")
                    if pg: st.caption(f"p.{pg}")
        elif pending_pair:
            row = dl.find_pair(*pending_pair)
            if row:
                pts = [x.strip() for x in (row["穴位"] or "").split(",")]
                p1 = pts[0] if pts else ""
                p2 = pts[1] if len(pts) > 1 else ""
                st.markdown(f"**{p1} ✦ {p2}**")
                if row.get("主治關鍵字"): st.markdown(f"**主治：** {row['主治關鍵字']}")
                if row.get("理論"): st.markdown(f"**理論：** {row['理論']}")
                if row.get("針法"): st.markdown(f"**針法：** {row['針法']}")
                if row.get("頁碼"): st.caption(f"p.{row['頁碼']}")
                if st.button("← 返回對針清單", key="pair_back"):
                    st.session_state.pop("_pending_pair", None)
                    st.rerun()
            else:
                st.warning("找不到這組對針")
        else:
            st.info("左側已展開對針預設清單，可直接點選，或輸入症狀／穴位名查詢。")
        return

    # 穴位模式
    if search:
        results = dl.search_acupoints_df(search)
        st.markdown(f"**搜尋「{search}」— 找到 {len(results)} 個穴位**")
        show_cards_df(results)
        return

    sel_reg = st.session_state.get("selected_region_code")
    if sel_reg:
        reg_info = dl.region_by_code(sel_reg)
        if reg_info:
            bp = f"　<small style='color:var(--ink-mute)'>{reg_info['身體分區']}</small>" if reg_info["身體分區"] else ""
            st.markdown(
                f"<h3 style='font-family:Noto Serif TC,serif;color:var(--vermillion)'>"
                f"{reg_info['部位']}{bp}</h3>",
                unsafe_allow_html=True,
            )
        rdf = dl.acupoints_in_region(sel_reg)
        show_cards_df(rdf)
        return

    # 首頁
    st.markdown("""
<div style="padding: 20px 0 30px">
  <div style="font-family:'Noto Serif TC',serif;font-size:2.2em;
    font-weight:700;color:var(--vermillion)">董氏奇穴查詢系統</div>
  <div style="color:var(--ink-mute);font-size:.95em;margin-top:6px">
    楊維傑醫師《董氏奇穴穴位詮釋解》及其他著作
  </div>
</div>
<hr>""", unsafe_allow_html=True)

    regions = dl.list_regions()
    df_ap = dl.load_acupoints_df()
    cols = st.columns(4)
    for i, (code, name, body) in enumerate(regions):
        count = len(df_ap[df_ap["部位代碼"] == code])
        with cols[i % 4]:
            st.markdown(f"""
<div style="background:rgba(255,255,255,.55);border:1px solid var(--divider);
  border-top:3px solid var(--gold);border-radius:6px;padding:14px 12px;
  text-align:center;margin:4px 0">
  <div style="font-family:'Noto Serif TC',serif;font-size:1em;
    font-weight:600;color:var(--vermillion)">{name}</div>
  <div style="font-size:.75em;color:var(--ink-mute);margin:2px 0">{body or ''}</div>
  <div style="font-size:1.4em;font-weight:700;color:var(--gold);margin-top:4px">{count}</div>
  <div style="font-size:.7em;color:var(--ink-mute)">穴</div>
</div>""", unsafe_allow_html=True)
            if st.button("瀏覽", key=f"home_{code}", use_container_width=True):
                st.session_state.selected_region_code = code
                st.session_state.selected_ap = None
                st.rerun()


# ── 主程式 ────────────────────────────────────────────────────────────────
def main():
    _inject_css()
    df_ap = dl.load_acupoints_df()
    total = len(df_ap)
    logo_uri = _img_to_data_uri(LOGO_PATH)
    logo_html = f"<img class='app-logo' src='{logo_uri}' alt='董氏奇穴印章'>" if logo_uri else ""
    st.markdown(f"""
<div class="app-topbar">
  <div class="app-brand">
    {logo_html}
    <div class="app-title-wrap">
      <div class="app-title-zh">董氏奇穴查詢系統</div>
      <div class="app-title-en">Tung's Acupuncture Points Reference</div>
    </div>
  </div>
  <div class="app-topbar-count">{total} 穴</div>
</div>
""", unsafe_allow_html=True)

    for k, v in [("selected_ap", None), ("selected_region_code", None),
                 ("mode_idx", 0), ("admin_mode", False),
                 ("image_review_open", False), ("create_ap_open", False)]:
        st.session_state.setdefault(k, v)

    if "_pending_mode" in st.session_state:
        pending = st.session_state.pop("_pending_mode")
        st.session_state.mode_idx = MODES.index(pending)
        st.session_state.mode_select = pending

    render_sidebar()
    render_main()

    if "_pending_symptom" in st.session_state and not st.session_state.get("selected_ap"):
        if st.session_state.get("search_kw"):
            st.session_state.pop("_pending_symptom", None)
    if st.session_state.get("search_kw"):
        st.session_state.pop("_pending_pair", None)


if __name__ == "__main__":
    main()
