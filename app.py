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
LOGO_PATH = BASE / "assets/logo-seal.png"
EXTRACTED_DIR = BASE / "extracted_images"

_OCR_BASE = Path(
    "/Users/samue11in/Library/CloudStorage/SynologyDrive-中醫資料庫"
    "/AI_Projects/inbox/output"
)
_OCR_PARTS = [
    _OCR_BASE / f"dongzhen_quanshi_part{i}/dongzhen_quanshi/hybrid_auto/dongzhen_quanshi.md"
    for i in range(1, 5)
]

MODES = ["📍 穴位", "💊 症狀", "🔗 對針"]
SYMPTOM_REGION_ORDER = [
    "頭面",
    "眼耳鼻喉",
    "頸肩",
    "上肢",
    "胸背",
    "腰腹",
    "下肢",
    "生殖泌尿",
    "其他",
]

STROKE_COUNT_MAP = {
    "一": 1, "乙": 1,
    "二": 2, "七": 2, "九": 2, "人": 2, "八": 2, "儿": 2, "入": 2, "几": 2, "刀": 2, "力": 2, "十": 2,
    "三": 3, "上": 3, "下": 3, "口": 3, "土": 3, "士": 3, "大": 3, "山": 3, "巾": 3, "干": 3, "工": 3,
    "中": 4, "五": 4, "六": 4, "內": 4, "內": 4, "公": 4, "分": 4, "反": 4, "天": 4, "少": 4, "手": 4,
    "支": 4, "文": 4, "方": 4, "日": 4, "月": 4, "木": 4, "欠": 4, "止": 4, "比": 4, "水": 4, "火": 4,
    "王": 4, "斗": 4,
    "丘": 5, "世": 5, "且": 5, "仆": 4, "仇": 4, "令": 5, "以": 5, "付": 5, "仙": 5, "代": 5, "仪": 5,
    "交": 6, "伍": 6, "京": 8, "仆": 4, "伏": 6, "光": 6, "兆": 6, "先": 6, "全": 6, "共": 6, "冰": 6,
    "再": 6, "冲": 6, "匠": 6, "危": 6, "印": 6, "各": 6, "合": 6, "向": 6, "回": 6, "在": 6, "地": 6,
    "多": 6, "奷": 6, "奸": 6, "好": 6, "如": 6, "宇": 6, "守": 6, "安": 6, "尖": 6, "州": 6, "年": 6,
    "式": 6, "曲": 6, "曳": 6, "有": 6, "次": 6, "此": 6, "死": 6, "气": 4, "汀": 5, "汀": 5, "江": 6,
    "关": 6, "共": 6, "会": 6, "后": 6, "听": 7, "名": 6, "因": 6, "回": 6, "在": 6,
    "兑": 7, "利": 7, "助": 7, "劫": 7, "医": 7, "即": 7, "听": 7, "吴": 7, "吹": 7, "坎": 7, "坏": 7,
    "壯": 7, "完": 7, "尾": 7, "局": 7, "希": 7, "床": 7, "序": 7, "廷": 6, "形": 7, "志": 7, "忍": 7,
    "扭": 7, "扶": 7, "技": 7, "攸": 7, "改": 7, "攻": 7, "束": 7, "李": 7, "杏": 7, "村": 7, "条": 7,
    "步": 7, "每": 7, "求": 7, "沙": 7, "沈": 7, "沖": 7, "状": 7, "牢": 7, "男": 7, "秀": 7, "私": 7,
    "究": 7, "系": 7, "良": 7, "見": 7, "角": 7, "言": 7, "谷": 7, "豆": 7, "足": 7, "身": 7,
    "亞": 8, "乳": 8, "事": 8, "些": 8, "京": 8, "佩": 8, "來": 8, "侖": 8, "兒": 8, "兩": 8, "其": 8,
    "典": 8, "到": 8, "制": 8, "刷": 8, "刺": 8, "前": 9, "勇": 9, "南": 9, "咽": 9, "垂": 8, "城": 9,
    "复": 9, "後": 9, "度": 9, "建": 8, "拜": 9, "指": 9, "按": 9, "施": 9, "是": 9, "星": 9, "春": 9,
    "映": 9, "柱": 9, "柳": 9, "洲": 9, "洞": 9, "炸": 9, "界": 9, "皆": 9, "省": 9, "相": 9, "秋": 9,
    "紅": 9, "約": 9, "美": 9, "胃": 9, "胁": 8, "背": 9, "苦": 8, "草": 9, "虹": 9, "計": 9, "軍": 9,
    "重": 9, "門": 8, "長": 8, "阿": 8, "雨": 8, "青": 8, "風": 9, "食": 9, "首": 9,
    "乘": 10, "冥": 10, "剛": 10, "原": 10, "唐": 10, "套": 10, "島": 10, "師": 10, "差": 10, "席": 10,
    "库": 10, "徐": 10, "徒": 10, "拿": 10, "旁": 10, "時": 10, "書": 10, "朔": 10, "栞": 10, "栗": 10,
    "气": 4, "梁": 11, "梅": 11, "梗": 11, "欲": 11, "毫": 11, "液": 11, "淡": 11, "深": 11, "清": 11,
    "烏": 10, "然": 12, "無": 12, "焦": 12, "發": 12, "番": 12, "痛": 12, "登": 12, "疏": 12, "發": 12,
    "睛": 13, "督": 13, "福": 13, "經": 13, "腰": 13, "腎": 13, "腮": 13, "董": 12, "落": 12, "解": 13,
    "肚": 7, "肝": 7, "肘": 7, "肩": 8, "肺": 8, "胸": 10, "脾": 12, "膀": 14, "膝": 15, "膻": 16, "臂": 17,
    "臨": 18, "聽": 22, "耳": 6, "眼": 11, "神": 9, "璇": 15, "環": 17, "玉": 5, "申": 5, "百": 6,
    "穴": 5, "竹": 6, "米": 6, "羊": 6, "老": 6, "而": 6, "至": 6, "舟": 6, "虫": 6, "血": 6, "行": 6,
    "虎": 8, "表": 8, "門": 8, "金": 8, "雨": 8, "鱼": 8, "馬": 10, "馬": 10, "高": 10, "鬼": 10,
    "健": 11, "副": 11, "區": 11, "密": 11, "寄": 11, "寅": 11, "康": 11, "張": 11, "強": 11, "彩": 11,
    "患": 11, "接": 11, "推": 11, "救": 11, "敗": 11, "旋": 11, "梧": 11, "條": 11, "欲": 11, "毫": 11,
    "淚": 11, "淘": 11, "添": 11, "清": 11, "淋": 11, "涵": 11, "焉": 11, "理": 11, "球": 11, "票": 11,
    "符": 11, "第": 11, "粗": 11, "細": 11, "終": 11, "紹": 11, "組": 11, "脳": 11, "脛": 11, "般": 10,
    "術": 11, "被": 10, "規": 11, "訊": 10, "訪": 11, "豚": 11, "貫": 11, "通": 10, "郄": 8, "陰": 11,
    "陽": 12, "陷": 10, "陶": 10, "頂": 11, "領": 14, "颊": 12, "飛": 9, "馬": 10, "魚": 11, "鼻": 14,
}

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
  --vermillion:   #7B2D1E;
  --vermillion-dk:#5F2116;
  --ink:          #2C1C10;
  --ink-lt:       #5C3D25;
  --ink-mute:     #8A6347;
  --divider:      #D4B887;
  --tag-bg:       rgba(219,168,76,.15);
  --tag-border:   rgba(196,147,58,.45);
  --ap-count:     "234 穴";
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
[data-testid="stHeader"] {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  height: 64px !important;
  background: linear-gradient(90deg, var(--vermillion-dk) 0%, var(--vermillion) 52%, #8C3825 100%) !important;
  box-shadow: 0 2px 14px rgba(44,28,16,.18) !important;
  z-index: 1002 !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] { display: none !important; }
.app-topbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1003;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 8px 24px 8px 18px;
  pointer-events: none;
}
.app-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.app-logo {
  width: 42px;
  height: 42px;
  border-radius: 6px;
  object-fit: cover;
  flex-shrink: 0;
  box-shadow: 0 1px 6px rgba(44,28,16,.22);
  transform: rotate(90deg);
}
.app-title-wrap {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}
.app-title-zh {
  font-family: 'Noto Serif TC', serif;
  font-size: 1.55em;
  font-weight: 700;
  color: #F7EDD8;
  line-height: 1.02;
  white-space: nowrap;
}
.app-title-en {
  font-size: .58em;
  letter-spacing: .08em;
  color: rgba(247,237,216,.8);
  margin-top: 2px;
  white-space: nowrap;
}
.app-topbar-count {
  background: rgba(247,237,216,.14);
  border: 1px solid rgba(247,237,216,.26);
  border-radius: 999px;
  padding: 5px 12px;
  font-size: .82em;
  color: #F7EDD8;
  line-height: 1.4;
  flex-shrink: 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background-color: var(--parchment-dk) !important;
  border-right: 1px solid var(--divider) !important;
  min-width: 280px !important;
  max-width: 340px !important;
  z-index: 1000 !important;
}
[data-testid="stSidebar"] > div:first-child {
  padding-top: 4.2rem !important;
}

/* ── 主區域 ── */
[data-testid="block-container"] {
  background-color: var(--parchment) !important;
  padding: 5.3rem 2rem 1.5rem !important;
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
  font-size: .82em;
  font-weight: 600;
  color: var(--ink-mute);
  letter-spacing: .1em;
  border-bottom: 1px solid var(--divider);
  padding-bottom: 5px;
  margin: 26px 0 12px;
}
.section-body {
  font-size: .95em;
  color: var(--ink);
  line-height: 1.85;
  margin-bottom: 14px;
}
.section-body:last-child { margin-bottom: 0; }
.principle-tag {
  display: inline-block;
  font-family: 'Noto Serif TC', serif;
  font-size: .78em;
  color: var(--gold);
  background: var(--tag-bg);
  border: 1px solid var(--tag-border);
  border-radius: 4px;
  padding: 1px 8px;
  margin: 16px 0 6px;
  letter-spacing: .04em;
}
.principle-tag:first-child { margin-top: 4px; }

/* tab bar 與標題之間呼吸 */
[data-baseweb="tab-list"] { margin-top: 8px !important; padding-bottom: 4px !important; }
[data-baseweb="tab-panel"] { padding-top: 6px !important; }

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
  padding: 14px 18px;
  margin: 8px 0 14px;
}
.needle-row { display: flex; gap: 12px; padding: 4px 0; border-bottom: 1px solid rgba(212,184,135,.3); }
.needle-row:last-child { border-bottom: none; }
.needle-lbl { font-size: .8em; color: var(--gold); font-weight: 600; min-width: 44px; }
.needle-val { font-size: .92em; color: var(--ink); line-height: 1.7; }

/* ── source block ── */
.src-block {
  background: rgba(255,255,255,.4);
  border: 1px solid var(--divider);
  border-radius: 6px;
  padding: 12px 16px;
  margin: 10px 0;
  font-size: .9em;
  color: var(--ink-lt);
  line-height: 1.75;
}
.src-block b { color: var(--ink); }
.src-book-title {
  font-family: 'Noto Serif TC', serif;
  font-size: .92em;
  color: var(--vermillion);
  font-weight: 600;
  margin: 18px 0 6px;
}

/* expander 之間呼吸 */
[data-testid="stExpander"] { margin-bottom: 8px !important; }

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

.sidebar-section-title {
  font-family: 'Noto Serif TC', serif;
  font-size: .76em;
  font-weight: 700;
  letter-spacing: .08em;
  color: var(--ink-mute);
  margin: 4px 0 8px;
}
.sidebar-preview {
  font-size: .8em;
  color: var(--ink-mute);
  line-height: 1.7;
  padding: 0 4px 6px;
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


@st.cache_resource
def _opencc_converter():
    try:
        import opencc
        return opencc.OpenCC("s2twp")
    except Exception:
        return None

def t(text):
    if not text:
        return text
    cc = _opencc_converter()
    if cc is None:
        return text
    try:
        return cc.convert(str(text))
    except Exception:
        return text


def _img_to_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    ext = path.suffix.lower().lstrip(".") or "png"
    mime = "image/png" if ext == "png" else f"image/{ext}"
    return f"data:{mime};base64,{_b64.b64encode(path.read_bytes()).decode('ascii')}"


def _zh_sort_key(text: str):
    return (text or "").strip()


def _normalize_symptom(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip())


def _stroke_count_for_char(ch: str) -> int:
    return STROKE_COUNT_MAP.get(ch, 99)


def _pair_canonical_order(point1: str, point2: str):
    pair = [(point1 or "").strip(), (point2 or "").strip()]
    pair.sort(key=lambda text: (_stroke_count_for_char(text[:1]), _zh_sort_key(text)))
    return tuple(pair)


def _pair_sort_key(point1: str, point2: str):
    p1, p2 = _pair_canonical_order(point1, point2)
    return (
        _stroke_count_for_char(p1[:1]),
        _zh_sort_key(p1),
        _stroke_count_for_char(p2[:1]),
        _zh_sort_key(p2),
    )


def _symptom_bucket(name: str) -> str:
    rules = [
        ("頭面", ("頭", "面", "顏", "臉", "口", "牙", "舌", "腮", "鼻樑", "鼻骨")),
        ("眼耳鼻喉", ("眼", "目", "耳", "鼻", "喉", "咽", "扁桃", "聲", "聽")),
        ("頸肩", ("頸", "項", "肩", "臂不舉", "落枕")),
        ("上肢", ("手", "肘", "腕", "臂", "肩臂", "指", "掌")),
        ("胸背", ("胸", "心", "肺", "乳", "背", "脊", "肋", "膈", "氣管")),
        ("腰腹", ("腰", "腹", "胃", "腸", "肝", "膽", "脾", "胰", "臍", "小腹")),
        ("下肢", ("腿", "膝", "踝", "腳", "足", "髖", "股", "臀", "下肢")),
        ("生殖泌尿", ("子宮", "月經", "經痛", "白帶", "陰", "卵", "睪丸", "攝護腺", "前列腺", "尿", "腎", "膀胱", "生殖", "不孕")),
    ]
    for bucket, keywords in rules:
        if any(keyword in name for keyword in keywords):
            return bucket
    return "其他"


@st.cache_data
def load_default_symptom_groups():
    rows = q("""
        SELECT indications_kw
        FROM acupoints
        WHERE indications_kw IS NOT NULL AND TRIM(indications_kw) <> ''
    """)
    buckets = {name: [] for name in SYMPTOM_REGION_ORDER}
    seen = set()
    for (raw,) in rows:
        for part in re.split(r"[，,、；;]", raw or ""):
            symptom = _normalize_symptom(part)
            if not symptom or symptom in seen or len(symptom) > 12:
                continue
            seen.add(symptom)
            buckets[_symptom_bucket(symptom)].append(symptom)

    grouped = []
    for bucket in SYMPTOM_REGION_ORDER:
        items = sorted(buckets[bucket], key=_zh_sort_key)
        if items:
            grouped.append((bucket, items))
    return grouped


@st.cache_data
def load_default_pair_list():
    rows = qo("""
        SELECT point1, point2
        FROM acupoint_pairs
        WHERE source LIKE '%區位易象特效對針%'
        GROUP BY point1, point2
    """)
    normalized_rows = []
    for point1, point2 in rows:
        p1 = t((point1 or "").strip())
        p2 = t((point2 or "").strip())
        if p1 and p2:
            normalized_rows.append(_pair_canonical_order(p1, p2))
    return sorted(
        set(normalized_rows),
        key=lambda row: _pair_sort_key(row[0], row[1]),
    )

# ── 圖片審核 helper ─────────────────────────────────────────────────────
def _manifest_path():
    return EXTRACTED_DIR / "manifest.json"

def load_manifest():
    p = _manifest_path()
    if not p.exists():
        return []
    import json
    return json.loads(p.read_text(encoding="utf-8"))

def save_manifest(items):
    import json
    _manifest_path().write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def adopt_image(item, acupoint_id, caption_override=None):
    """採用一張圖：寫入 acupoint_images，並把 manifest 標 adopted。"""
    img_path = EXTRACTED_DIR / item["file"]
    img_bytes = img_path.read_bytes()
    b64 = _b64.b64encode(img_bytes).decode("ascii")
    cand_ref = ""
    for c in item.get("candidates", []):
        if c.get("id") == acupoint_id:
            cand_ref = c.get("ref", "")
            break
    caption = caption_override or item.get("caption", "")
    conn = get_conn()
    conn.execute(
        "INSERT INTO acupoint_images (acupoint_id, image_path, caption, "
        "image_data, figure_ref, match_method) VALUES (?,?,?,?,?,?)",
        (acupoint_id, item["file"], caption, b64, cand_ref,
         item.get("match_method", "manual")),
    )
    conn.commit()
    load_acupoint_images.clear()
    item["status"] = "adopted"
    item["adopted_to"] = acupoint_id

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
    kw_simp = keyword
    try:
        import opencc
        kw_simp = opencc.OpenCC("tw2sp").convert(keyword)
    except Exception:
        pass
    like = f"%{keyword}%"
    like_s = f"%{kw_simp}%"
    return qo("""
        SELECT point1, point2, indication, theory, needle_method,
               GROUP_CONCAT(source,'、') as sources,
               MIN(page_number) as page_number, COUNT(*) as freq
        FROM acupoint_pairs
        WHERE (indication LIKE ? OR point1 LIKE ? OR point2 LIKE ?
               OR indication LIKE ? OR point1 LIKE ? OR point2 LIKE ?)
          AND source LIKE '%區位易象特效對針%'
        GROUP BY point1, point2
        ORDER BY freq DESC, point1
        LIMIT 40
    """, (like, like, like, like_s, like_s, like_s))


@st.cache_data
def load_pair_exact(point1, point2):
    rows = qo("""
        SELECT point1, point2, indication, theory, needle_method,
               GROUP_CONCAT(source,'、') as sources,
               MIN(page_number) as page_number, COUNT(*) as freq
        FROM acupoint_pairs
        WHERE source LIKE '%區位易象特效對針%'
        GROUP BY point1, point2
    """)
    target = _pair_canonical_order(t(point1), t(point2))
    for row in rows:
        if _pair_canonical_order(t(row[0]), t(row[1])) == target:
            return row
    return None

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
    bare = name.replace("穴","")
    bare_s = bare
    try:
        import opencc
        bare_s = opencc.OpenCC("tw2sp").convert(bare)
    except Exception:
        pass
    like = f"%{bare}%"
    like_s = f"%{bare_s}%"
    return qo("""
        SELECT point1, point2, indication, theory, needle_method,
               GROUP_CONCAT(source,'、') as sources,
               MIN(page_number) as page_number, COUNT(*) as freq
        FROM acupoint_pairs
        WHERE (point1 LIKE ? OR point2 LIKE ? OR point1 LIKE ? OR point2 LIKE ?)
          AND source LIKE '%區位易象特效對針%'
        GROUP BY point1, point2 ORDER BY freq DESC, point1 LIMIT 40
    """, (like, like, like_s, like_s))

@st.cache_data
def load_symptoms_for_acupoint(name):
    bare = name.replace("穴","")
    bare_s = bare
    try:
        import opencc
        bare_s = opencc.OpenCC("tw2sp").convert(bare)
    except Exception:
        pass
    like = f"%{bare}%"
    like_s = f"%{bare_s}%"
    return qo("""
        SELECT s.name, st.treatment, st.source, st.page_number
        FROM symptoms s JOIN symptom_treatments st ON s.id=st.symptom_id
        WHERE (st.treatment LIKE ? OR st.treatment LIKE ?)
          AND st.source LIKE '楊維傑-%'
        ORDER BY st.source, s.name LIMIT 60
    """, (like, like_s))

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
    images = load_acupoint_images(ap_id)
    kw_raw = d.get("indications_kw") or d.get("dong_indications") or ""
    kws = [k.strip() for k in re.split(r"[，,、；;]+", kw_raw) if k.strip()]
    dongyangsiwei = d.get("new_applications") or ""
    commentary = d.get("commentary") or ""
    comparison_text = d.get("comparison_text") or ""
    extension_text = d.get("extension_text") or ""
    anatomy = d.get("anatomy") or ""
    symptom_rows = load_symptoms_for_acupoint(name)
    pair_rows = load_pairs_for_acupoint(name)
    pair_rows = [row for row in pair_rows if "區位易象特效對針" in (row[5] or "")]
    common_rows = []
    pain_rows = []
    other_book_rows = []
    for row in symptom_rows:
        src = row[2]
        if "常見病特效一針療法" in src:
            common_rows.append(row)
        elif "痛證特效一針療法" in src:
            pain_rows.append(row)
        else:
            other_book_rows.append(row)

    tab_labels = ["取穴定位", "主治原理", "臨床配伍"]
    if st.session_state.get("admin_mode"):
        tab_labels.append("✏️ 編輯")
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        if loc or method:
            st.markdown("<div class='section-label'>位置</div>", unsafe_allow_html=True)
            body_parts = [p for p in [loc, method] if p]
            st.markdown(f"<div class='section-body'>{'；'.join(body_parts)}</div>",
                        unsafe_allow_html=True)
        if needle:
            st.markdown("<div class='section-label'>針法</div>", unsafe_allow_html=True)
            st.markdown(f"""
<div class="needle-card">
  <div class="needle-row"><span class="needle-lbl">針法</span><span class="needle-val">{needle}</span></div>
</div>""", unsafe_allow_html=True)
        if images:
            st.markdown("<div class='section-label'>穴位圖</div>", unsafe_allow_html=True)
            img_cols = st.columns(len(images))
            for i, (img_data, caption, fig_r) in enumerate(images):
                with img_cols[i]:
                    st.image(_b64.b64decode(img_data), use_container_width=True)
                    if fig_r:
                        st.caption(fig_r)
                    elif caption:
                        st.caption(caption)
        if anatomy:
            st.markdown("<div class='section-label'>現代解剖</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-body'>{anatomy}</div>",
                        unsafe_allow_html=True)
        if caution:
            st.markdown("<div class='section-label'>備註</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-body'>{caution}</div>",
                        unsafe_allow_html=True)
        with st.expander("📜 原始文獻段落"):
            chunk = load_ocr_chunk(name)
            if chunk:
                st.text(chunk[:3000] + ("…" if len(chunk)>3000 else ""))
            else:
                st.caption("此穴位暫無 OCR 原文")

    with tabs[1]:
        if kws:
            st.markdown("<div class='section-label'>主治關鍵字</div>", unsafe_allow_html=True)
            n_cols = 4
            cols = st.columns(n_cols)
            for i, kw in enumerate(kws):
                with cols[i % n_cols]:
                    if st.button(kw, key=f"kw_{ap_id}_{i}", use_container_width=True):
                        st.session_state._pending_mode    = "💊 症狀"
                        st.session_state._pending_symptom = kw
                        st.session_state._set_search_kw   = kw
                        st.session_state.selected_ap      = None
                        st.rerun()
        else:
            st.caption("此穴暫無主治關鍵字")

        principle_items = [
            ("董楊思維／維傑新用", dongyangsiwei),
            ("解說及發揮", commentary),
            ("比較", comparison_text),
            ("引申", extension_text),
        ]
        principle_items = [(label, body) for label, body in principle_items if body]
        if principle_items:
            st.markdown("<div class='section-label'>原理與發揮</div>", unsafe_allow_html=True)
            for label, body in principle_items:
                st.markdown(
                    f"<div class='principle-tag'>{label}</div>"
                    f"<div class='section-body'>{body}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("此穴暫無原理相關補充")

    with tabs[2]:
        st.markdown("<div class='section-label'>對針</div>", unsafe_allow_html=True)
        if not pair_rows:
            st.caption("《區位易象特效對針》未見含此穴之對針組合")
        else:
            st.caption(f"共 {len(pair_rows)} 組，依出現頻次排序")
            for p1, p2, ind, theory, method, srcs, pg, freq in pair_rows:
                p1, p2, ind, theory, method = t(p1), t(p2), t(ind), t(theory), t(method)
                with st.expander(f"**{p1} ✦ {p2}**　｜　{(ind or '')[:50]}"):
                    c1,c2 = st.columns(2)
                    c1.markdown(f"**穴1：** {p1}"); c2.markdown(f"**穴2：** {p2}")
                    if ind:    st.markdown(f"**主治：** {ind}")
                    if theory: st.markdown(f"**理論：** {theory}")
                    if method: st.markdown(f"**針法：** {method}")
                    if pg:     st.caption(f"p.{pg}　（出現 {freq} 次）")
        st.markdown("<div class='section-label'>常見病</div>", unsafe_allow_html=True)
        if common_rows:
            for sym, treat, src, pg in common_rows:
                sym, treat = t(sym), t(treat)
                pg_s = f" <small style='color:var(--ink-mute)'>p.{pg}</small>" if pg else ""
                st.markdown(f"<div class='src-block'>🩺 <b>{sym}</b>{pg_s}<br>推薦穴位：{treat}</div>",
                            unsafe_allow_html=True)
        else:
            st.caption("常見病資料暫缺")

        st.markdown("<div class='section-label'>痛症</div>", unsafe_allow_html=True)
        if pain_rows:
            for sym, treat, src, pg in pain_rows:
                sym, treat = t(sym), t(treat)
                pg_s = f" <small style='color:var(--ink-mute)'>p.{pg}</small>" if pg else ""
                st.markdown(f"<div class='src-block'>🩺 <b>{sym}</b>{pg_s}<br>推薦穴位：{treat}</div>",
                            unsafe_allow_html=True)
        else:
            st.caption("痛症資料暫缺")

        st.markdown("<div class='section-label'>其他著作</div>", unsafe_allow_html=True)
        if other_book_rows:
            cur_src = None
            for sym, treat, src, pg in other_book_rows:
                book = src.replace("楊維傑-楊維傑","").replace("楊維傑-","")
                if book in {"楊維傑區位易象特效對針", "楊維傑常見病特效一針療法", "楊維傑痛證特效一針療法"}:
                    continue
                if book != cur_src:
                    st.markdown(f"<div class='src-book-title'>📖 {book}</div>",
                                unsafe_allow_html=True)
                    cur_src = book
                sym, treat = t(sym), t(treat)
                pg_s = f" <small style='color:var(--ink-mute)'>p.{pg}</small>" if pg else ""
                st.markdown(f"<div class='src-block'>🩺 <b>{sym}</b>{pg_s}<br>推薦穴位：{treat}</div>",
                            unsafe_allow_html=True)
        else:
            st.caption("其他著作資料暫缺")

    if st.session_state.get("admin_mode") and len(tabs) > 2:
        with tabs[3]:
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
    if "_set_search_kw" in st.session_state:
        st.session_state.search_kw = st.session_state.pop("_set_search_kw")
    if "_set_pending_pair" in st.session_state:
        st.session_state._pending_pair = st.session_state.pop("_set_pending_pair")

    # ── 模式切換 ──
    mode_idx = st.session_state.get("mode_idx", 0)
    sel = st.sidebar.selectbox("模式切換", MODES, index=mode_idx,
                               key="mode_select", label_visibility="collapsed")
    new_mode_idx = MODES.index(sel)
    prev_mode_idx = st.session_state.get("_prev_mode_idx", new_mode_idx)
    if prev_mode_idx != new_mode_idx:
        # 切換模式時自動清空搜尋與暫存，回到該模式的預設內容
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

    # ── 搜尋框 ──
    placeholder = {"📍 穴位":"輸入穴位名稱或編號…",
                   "💊 症狀":"輸入症狀關鍵字…",
                   "🔗 對針":"輸入症狀或穴位名稱…"}.get(mode,"")
    search = st.sidebar.text_input("搜尋", placeholder=placeholder,
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
        symptom_kw = search or st.session_state.get("_pending_symptom", "")
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
            groups = load_default_symptom_groups()
            total_count = sum(len(items) for _, items in groups)
            st.sidebar.caption(f"症狀預設清單，共 {total_count} 項")
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
                    [""] + items,
                    index=0,
                    key=f"sym_default_{section}",
                    label_visibility="collapsed",
                )
                if selected_symptom and st.session_state.get("search_kw") != selected_symptom:
                    st.session_state._set_search_kw = selected_symptom
                    st.session_state._pending_symptom = selected_symptom
                    st.session_state.selected_ap = None
                    st.rerun()

    # ── 對針模式 ──
    elif mode == "🔗 對針":
        pending_pair = st.session_state.get("_pending_pair")
        if search:
            results = search_pairs(search)
            st.sidebar.caption(f"找到 {len(results)} 組對針")
            for p1, p2, ind, *_ in results:
                p1, p2, ind = t(p1), t(p2), t(ind)
                st.sidebar.markdown(
                    f"<div style='font-size:.82em;padding:5px 8px;border-bottom:"
                    f"1px solid var(--divider);color:var(--ink-lt)'>"
                    f"<b>{p1} ✦ {p2}</b><br>"
                    f"<span style='color:var(--ink-mute)'>{(ind or '')[:35]}</span></div>",
                    unsafe_allow_html=True)
        elif pending_pair:
            point1, point2 = pending_pair
            st.sidebar.caption(f"已選對針：{point1} ✦ {point2}")
        else:
            pair_rows = load_default_pair_list()
            st.sidebar.caption(f"對針預設清單，共 {len(pair_rows)} 組")
            preview_pairs = [f"{point1} ✦ {point2}" for point1, point2 in pair_rows[:24]]
            st.sidebar.markdown(
                f"<div class='sidebar-preview'>{'<br>'.join(preview_pairs)}"
                f"{'<br>…' if len(pair_rows) > 24 else ''}</div>",
                unsafe_allow_html=True,
            )
            pair_options = [""] + [f"{point1} ✦ {point2}" for point1, point2 in pair_rows]
            selected_pair = st.sidebar.selectbox(
                "預設對針",
                pair_options,
                index=0,
                key="pair_default_select",
                label_visibility="collapsed",
            )
            if selected_pair:
                point1, point2 = selected_pair.split(" ✦ ", 1)
                if st.session_state.get("_pending_pair") != (point1, point2):
                    st.session_state._set_search_kw = ""
                    st.session_state._set_pending_pair = (point1, point2)
                    st.rerun()

    # ── Admin ──
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    if st.session_state.get("admin_mode"):
        st.sidebar.success("✏️ 編輯模式已開啟")
        if st.sidebar.button("🖼 圖片審核", key="open_image_review",
                             use_container_width=True):
            st.session_state.image_review_open = True
            st.rerun()
        if st.sidebar.button("關閉編輯模式", key="close_admin"):
            st.session_state.admin_mode = False
            st.session_state.image_review_open = False
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


# ── 圖片審核頁 ────────────────────────────────────────────────────────────
def render_image_review():
    st.markdown("<div class='section-label'>🖼 穴位圖審核</div>",
                unsafe_allow_html=True)
    if st.button("← 結束審核", key="exit_review"):
        st.session_state.image_review_open = False
        st.rerun()

    items = load_manifest()
    if not items:
        st.warning("尚未抽圖。先在 terminal 執行：python extract_images_v2.py")
        return

    pending = [i for i in items if i.get("status") not in ("adopted", "skipped")]
    adopted = [i for i in items if i.get("status") == "adopted"]
    skipped = [i for i in items if i.get("status") == "skipped"]
    st.caption(
        f"待審核 {len(pending)}　｜　已採用 {len(adopted)}　｜　"
        f"已跳過 {len(skipped)}　｜　共 {len(items)} 張"
    )

    # 過濾
    method_opts = ["全部", "caption_fig", "caption_name", "same_page", "noref"]
    sel_method = st.selectbox(
        "比對來源", method_opts, index=0, key="rv_method_filter",
    )
    pool = pending if not st.checkbox(
        "顯示已處理（含採用／跳過）", key="rv_show_done"
    ) else items
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
    chunk = pool[(page - 1) * page_size : page * page_size]
    st.caption(f"顯示第 {(page-1)*page_size+1}–{(page-1)*page_size+len(chunk)} 張，共 {len(pool)} 張")

    # 預載 acupoint 全名清單供「換穴位」
    all_aps = q("SELECT id, name, figure_ref FROM acupoints ORDER BY id")
    ap_label_map = {ap_id: f"{name} ({ref or '-'})" for ap_id, name, ref in all_aps}
    ap_id_list = [ap_id for ap_id, _, _ in all_aps]

    for i, item in enumerate(chunk):
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
                f"<small style='color:var(--ink-mute)'>"
                f"來源：{item.get('match_method','-')}　"
                f"size {int(item['size'][0])}×{int(item['size'][1])}</small>",
                unsafe_allow_html=True,
            )
            cap = item.get("caption", "")
            if cap:
                st.caption(f"caption: {cap[:80]}")
            cands = item.get("candidates", [])
            if item.get("status") == "adopted":
                st.success(f"已採用 → acupoint id={item.get('adopted_to')}")
                continue
            if item.get("status") == "skipped":
                st.info("已跳過")
                continue
            if cands:
                cand_labels = [
                    f"{c['name']} ({c.get('ref','-')})  [id={c['id']}]"
                    for c in cands
                ]
                idx = st.radio(
                    "候選穴位（自動比對）", list(range(len(cands))),
                    format_func=lambda x: cand_labels[x],
                    key=f"rv_cand_{global_idx}",
                    horizontal=False,
                )
                target_id = cands[idx]["id"]
            else:
                st.warning("自動無候選，請手動指定")
                target_id = None

            with st.expander("手動指定／覆寫穴位"):
                pick = st.selectbox(
                    "選穴位",
                    [None] + ap_id_list,
                    format_func=lambda x: "－" if x is None else ap_label_map[x],
                    key=f"rv_pick_{global_idx}",
                )
                if pick:
                    target_id = pick

            b1, b2, b3 = st.columns(3)
            if b1.button("✅ 採用", key=f"rv_adopt_{global_idx}",
                         disabled=target_id is None,
                         use_container_width=True, type="primary"):
                adopt_image(item, target_id)
                save_manifest(items)
                st.rerun()
            if b2.button("⏭ 跳過", key=f"rv_skip_{global_idx}",
                         use_container_width=True):
                item["status"] = "skipped"
                save_manifest(items)
                st.rerun()
            if b3.button("🔄 重置", key=f"rv_reset_{global_idx}",
                         use_container_width=True):
                item.pop("status", None)
                item.pop("adopted_to", None)
                save_manifest(items)
                st.rerun()


# ── 主區域 ────────────────────────────────────────────────────────────────────
def render_main():
    if st.session_state.get("admin_mode") and st.session_state.get("image_review_open"):
        render_image_review()
        return

    mode   = MODES[st.session_state.get("mode_idx", 0)]
    search = st.session_state.get("search_kw", "")
    sel_ap = st.session_state.get("selected_ap")

    if sel_ap:
        show_detail(sel_ap)
        return

    if mode == "💊 症狀":
        kw = search or st.session_state.get("_pending_symptom", "")
        st.markdown("<div class='section-label'>按症狀查穴位</div>", unsafe_allow_html=True)
        if kw:
            results = search_symptoms(kw)
            st.markdown(f"**「{kw}」— 找到 {len(results)} 個穴位**")
            if st.button("← 返回症狀清單", key="symptom_back"):
                st.session_state._set_search_kw = ""
                st.session_state.pop("_pending_symptom", None)
                st.rerun()
            show_cards(results)
        else:
            groups = load_default_symptom_groups()
            st.info("左側已展開症狀預設清單，可直接點選，或輸入症狀關鍵字查詢。")
            for section, items in groups:
                st.markdown(f"**{section}**")
                st.caption("、".join(items[:24]) + ("…" if len(items) > 24 else ""))
        return

    if mode == "🔗 對針":
        st.markdown("<div class='section-label'>對針組合查詢</div>", unsafe_allow_html=True)
        pending_pair = st.session_state.get("_pending_pair")
        if search:
            results = search_pairs(search)
            st.markdown(f"**「{search}」— 找到 {len(results)} 組對針**")
            for p1, p2, ind, theory, method, srcs, pg, freq in results:
                p1, p2, ind, theory, method = t(p1), t(p2), t(ind), t(theory), t(method)
                with st.expander(f"**{p1} ✦ {p2}**　｜　{(ind or '')[:60]}"):
                    c1,c2 = st.columns(2)
                    c1.markdown(f"**穴1：** {p1}"); c2.markdown(f"**穴2：** {p2}")
                    if ind:    st.markdown(f"**主治：** {ind}")
                    if theory: st.markdown(f"**理論：** {theory}")
                    if method: st.markdown(f"**針法：** {method}")
                    if pg:     st.caption(f"p.{pg}　（{freq} 次）")
        elif pending_pair:
            row = load_pair_exact(*pending_pair)
            if row:
                p1, p2, ind, theory, method, srcs, pg, freq = row
                p1, p2, ind, theory, method = t(p1), t(p2), t(ind), t(theory), t(method)
                st.markdown(f"**{p1} ✦ {p2}**")
                if ind:
                    st.markdown(f"**主治：** {ind}")
                if theory:
                    st.markdown(f"**理論：** {theory}")
                if method:
                    st.markdown(f"**針法：** {method}")
                if pg:
                    st.caption(f"p.{pg}　（出現 {freq} 次）")
                if st.button("← 返回對針清單", key="pair_back"):
                    st.session_state.pop("_pending_pair", None)
                    st.rerun()
            else:
                st.warning("找不到這組對針")
        else:
            st.info("左側已展開對針預設清單，可直接點選，或輸入症狀／穴位名查詢。")
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
    total = q1("SELECT COUNT(*) FROM acupoints")[0]
    logo_uri = _img_to_data_uri(LOGO_PATH)
    st.markdown(
        f"<style>:root {{ --ap-count: \"{total} 穴\"; }}</style>",
        unsafe_allow_html=True,
    )
    logo_html = f"<img class='app-logo' src='{logo_uri}' alt='董氏奇穴印章'>" if logo_uri else ""
    st.markdown(
        f"""
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
""",
        unsafe_allow_html=True,
    )

    for k, v in [("selected_ap",None),("selected_region",None),
                 ("mode_idx",0),("admin_mode",False)]:
        st.session_state.setdefault(k, v)

    # 處理 pending mode（主治關鍵字點擊後跳轉）
    if "_pending_mode" in st.session_state:
        pending = st.session_state.pop("_pending_mode")
        st.session_state.mode_idx = MODES.index(pending)
        st.session_state.mode_select = pending

    render_sidebar()
    render_main()

    # 用完 pending_symptom 就清掉
    if "_pending_symptom" in st.session_state and not st.session_state.get("selected_ap"):
        # 若已顯示結果且 search_kw 有值，清 pending
        if st.session_state.get("search_kw"):
            st.session_state.pop("_pending_symptom", None)
    if st.session_state.get("search_kw"):
        st.session_state.pop("_pending_pair", None)


if __name__ == "__main__":
    main()
