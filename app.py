"""
董氏奇穴穴位詮釋解 — 檢索工具（CSV 後端版）
資料：data/*.csv + data/notes/*.md + data/images/*.jpg
"""
import base64 as _b64
import html as _html
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

# 把 script 目錄加進 sys.path（Streamlit 1.30+ 不自動加）
_BASE_DIR = Path(__file__).parent.resolve()
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

import streamlit as st
import streamlit.components.v1 as components

import data_loader as dl

BASE = Path(__file__).parent
LOGO_PATH = BASE / "assets/logo-seal.png"
EXTRACTED_DIR = BASE / "extracted_images"

MODES = ["📍 穴位", "💊 症狀", "🔗 對針"]
NAV_MODE = {
    "acupoint": "📍 穴位",
    "symptom": "💊 症狀",
    "pair": "🔗 對針",
}

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
@import url('https://fonts.googleapis.com/css2?family=Allura&family=Noto+Serif+TC:wght@300;400;500;600;700&family=Noto+Sans+TC:wght@300;400;500&display=swap');

:root {
  --parchment:    #F7EDD8;
  --parchment-dk: #EDD9A3;
  --surface:      rgba(255,255,255,.62);
  --surface-hover:rgba(196,147,58,.14);
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
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
  background: var(--parchment) !important;
}

#MainMenu, footer, [data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"] {
  position: fixed !important; top: 0 !important; left: 0 !important; right: 0 !important;
  height: 120px !important;
  background-color: var(--vermillion) !important;
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180' viewBox='0 0 180 180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.72' numOctaves='4' seed='17' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.22'/%3E%3C/svg%3E"),
    radial-gradient(circle at 48% 35%, #8C3825 0%, #7B2D1E 52%, #5F2116 100%) !important;
  background-blend-mode: soft-light, normal !important;
  box-shadow: 0 2px 14px rgba(69,20,16,.25) !important;
  z-index: 1002 !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] { display: none !important; }

.app-topbar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 1003;
  height: 120px; display: flex; align-items: center; justify-content: space-between;
  gap: 18px; padding: 16px 30px 16px 24px; pointer-events: none;
}
.app-brand { display: flex; align-items: center; gap: 12px; min-width: 0; }
.app-logo {
  width: 42px; height: 42px; border-radius: 6px; object-fit: cover; flex-shrink: 0;
  box-shadow: 0 1px 6px rgba(44,28,16,.22); transform: rotate(90deg);
}
.app-title-wrap { display: flex; flex-direction: column; justify-content: center; min-width: 0; }
.app-title-zh {
  font-family: BiauKai, DFKai-SB, STKaiti, KaiTi, serif;
  font-size: 1.72em; font-weight: 400;
  color: #F7EDD8; line-height: 1.02; white-space: nowrap;
}
.app-title-en {
  font-family: 'Allura', 'Brush Script MT', cursive;
  font-size: .92em; letter-spacing: .04em; color: rgba(247,237,216,.86);
  margin-top: 1px; white-space: nowrap;
}
.app-admin-link {
  pointer-events: auto;
  background: rgba(247,237,216,.14); border: 1px solid rgba(247,237,216,.3);
  border-radius: 999px; padding: 5px 14px; font-size: .82em; color: #F7EDD8;
  line-height: 1.4; flex-shrink: 0; text-decoration: none !important;
}
.app-admin-link:hover {
  background: rgba(247,237,216,.24); color: #fff;
}

[data-testid="stSidebar"] {
  background-color: var(--parchment-dk) !important;
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='360' height='720' viewBox='0 0 360 720'%3E%3Cfilter id='cloud'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.012 .045' numOctaves='4' seed='23' stitchTiles='stitch'/%3E%3CfeGaussianBlur stdDeviation='1.2'/%3E%3C/filter%3E%3Cfilter id='vein'%3E%3CfeTurbulence type='turbulence' baseFrequency='.008 .032' numOctaves='3' seed='41' result='noise'/%3E%3CfeDisplacementMap in='SourceGraphic' in2='noise' scale='54' xChannelSelector='R' yChannelSelector='B'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23cloud)' opacity='.16'/%3E%3Cg filter='url(%23vein)' fill='none' stroke-linecap='round'%3E%3Cpath d='M-40 120 C70 60 110 230 220 160 S350 90 410 150' stroke='%23A78A5D' stroke-width='2.2' opacity='.28'/%3E%3Cpath d='M-70 345 C45 285 125 430 245 355 S365 300 420 370' stroke='%23BDA67D' stroke-width='5' opacity='.16'/%3E%3Cpath d='M-30 565 C80 500 150 650 255 575 S365 525 410 590' stroke='%238D704B' stroke-width='1.5' opacity='.22'/%3E%3Cpath d='M35 -40 C5 120 150 185 105 340 S185 600 145 760' stroke='%23FFF8E8' stroke-width='8' opacity='.18'/%3E%3Cpath d='M-55 55 C50 20 135 115 230 72 S345 40 415 88' stroke='%23947A55' stroke-width='1.1' opacity='.19'/%3E%3Cpath d='M-35 205 C85 145 145 285 250 218 S355 180 405 225' stroke='%23C2AA80' stroke-width='2.8' opacity='.14'/%3E%3Cpath d='M-60 275 C40 245 130 335 225 292 S340 250 420 315' stroke='%238B704D' stroke-width='1.2' opacity='.18'/%3E%3Cpath d='M-45 435 C65 375 135 495 240 448 S350 405 415 455' stroke='%23B49A70' stroke-width='2' opacity='.16'/%3E%3Cpath d='M-70 500 C55 455 125 550 235 510 S350 470 425 525' stroke='%23977B54' stroke-width='.9' opacity='.2'/%3E%3Cpath d='M-40 650 C65 600 145 705 255 662 S360 625 415 680' stroke='%23C5AE86' stroke-width='3.5' opacity='.13'/%3E%3Cpath d='M250 -45 C205 90 330 180 275 315 S325 565 285 760' stroke='%23A68B63' stroke-width='1.3' opacity='.17'/%3E%3Cpath d='M165 -55 C120 85 230 155 180 290 S245 530 205 755' stroke='%23FFF8E8' stroke-width='4.5' opacity='.12'/%3E%3C/g%3E%3C/svg%3E") !important;
  background-size: 360px 720px !important;
  background-repeat: repeat !important;
  background-blend-mode: multiply !important;
  border-right: 1px solid var(--divider) !important;
  display: block !important;
  width: 200px !important; min-width: 200px !important; max-width: 200px !important;
  z-index: 1000 !important;
  transform: translateX(0) !important;
  visibility: visible !important;
  overflow: visible !important;
}
[data-testid="stSidebar"][aria-expanded="false"] {
  width: 200px !important;
  min-width: 200px !important;
  max-width: 200px !important;
  transform: translateX(0) !important;
  visibility: visible !important;
}
[data-testid="stSidebar"] > div:first-child {
  padding-top: 7.7rem !important;
  display: block !important;
  overflow: visible !important;
  background: transparent !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] summary {
  color: var(--ink) !important;
  text-align: center !important;
}
[data-testid="block-container"] {
  background-color: var(--parchment) !important;
  padding: 9.3rem 2rem 1.5rem !important; max-width: 900px !important;
}

.sidebar-layout-anchor { height: 22vh; min-height: 130px; }
.sidebar-nav-shell { margin: 42px 0 0; position: relative; }
.sidebar-nav { border: none; background: transparent; box-shadow: none; overflow: visible; }
.sidebar-nav-item { position: relative; }
.sidebar-nav-item + .sidebar-nav-item { border-top: none; margin-top: 34px; }
.sidebar-nav-main {
  display: flex; justify-content: center; align-items: center;
  padding: 0 8px; color: var(--ink) !important; text-decoration: none !important;
  font-family: 'Noto Serif TC', serif; font-size: 1.28em; font-weight: 700;
  letter-spacing: .04em; text-align: center;
}
.sidebar-nav-main span:first-child { border-bottom: 2px solid transparent; line-height: 1.35; }
.sidebar-nav-item:hover .sidebar-nav-main span:first-child,
.sidebar-nav-item.is-active .sidebar-nav-main span:first-child {
  border-bottom-color: var(--gold); color: var(--vermillion);
}
.sidebar-nav-caret { display: none; }
.sidebar-flyout {
  display: block; position: absolute; left: 168px; top: -8px; width: 260px;
  overflow: visible;
  visibility: hidden; opacity: 0; pointer-events: none;
  transition: opacity .12s ease, visibility 0s linear .12s;
  background: rgba(255,252,244,.98); border: 1px solid var(--divider);
  border-left: 3px solid var(--gold); border-radius: 0 8px 8px 0;
  box-shadow: 8px 10px 24px rgba(44,28,16,.16); padding: 6px 0; z-index: 1004;
}
.sidebar-flyout::before {
  content: ""; position: absolute; left: -42px; top: -16px; width: 42px; height: calc(100% + 32px);
}
.sidebar-nav-item.is-menu-open > .sidebar-flyout {
  visibility: visible; opacity: 1; pointer-events: auto;
}
.sidebar-flyout a,
.sidebar-flyout-main {
  display: block; padding: 10px 18px; color: var(--ink-lt); text-decoration: none !important;
  font-family: 'Noto Serif TC', serif; font-size: .96em;
  border-bottom: 1px solid rgba(212,184,135,.36); background: transparent;
}
.sidebar-flyout a:last-child,
.sidebar-flyout-row:last-child .sidebar-flyout-main { border-bottom: none; }
.sidebar-flyout a:hover,
.sidebar-flyout-row:hover > .sidebar-flyout-main {
  color: var(--vermillion); background: rgba(219,168,76,.14);
}
.sidebar-flyout-row { position: relative; }
.sidebar-flyout-main { display: flex; align-items: center; justify-content: space-between; }
.sidebar-flyout-main::after {
  content: "›"; color: var(--gold); font-family: 'Noto Sans TC', sans-serif;
}
.sidebar-subflyout {
  display: block; position: absolute; left: calc(100% - 1px); top: -7px; width: 270px;
  max-height: calc(100vh - 48px); overflow-y: auto;
  overscroll-behavior: contain; scrollbar-gutter: stable;
  visibility: hidden; opacity: 0; pointer-events: none;
  background: rgba(255,252,244,.98); border: 1px solid var(--divider);
  border-left: 3px solid var(--gold); border-radius: 0 8px 8px 0;
  box-shadow: 8px 10px 24px rgba(44,28,16,.14); padding: 6px 0;
  z-index: 1005;
}
.sidebar-subflyout::before {
  content: ""; position: absolute; left: -34px; top: -12px; width: 34px; height: calc(100% + 24px);
}
.sidebar-flyout-row.is-submenu-open > .sidebar-subflyout {
  visibility: visible; opacity: 1; pointer-events: auto;
}

.pair-result-list {
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 14px; margin: 30px 0 10px;
}
.pair-result-card {
  display: flex; flex-direction: column; justify-content: center; align-items: center;
  width: 100%; min-height: 76px; padding: 12px 18px; text-align: center;
  background: var(--surface); border: 1px solid var(--divider);
  border-radius: 7px; color: var(--vermillion); text-decoration: none !important;
  font-family: 'Noto Serif TC', serif; box-shadow: none;
}
.pair-result-card:hover {
  background: var(--surface-hover); border-color: var(--gold); color: var(--vermillion-dk);
}
.pair-result-title {
  font-size: clamp(.95rem, 1.15vw, 1.08rem); font-weight: 700; line-height: 1.35;
}
.pair-result-points {
  margin-top: 4px; font-size: clamp(.78rem, .95vw, .92rem); color: var(--ink-lt); line-height: 1.35;
}
.catalog-section-title {
  font-family: 'Noto Serif TC', serif; font-size: 1.28rem; font-weight: 700;
  color: var(--ink); margin: 24px 0 10px; padding-bottom: 6px;
  border-bottom: 1px solid var(--divider);
}
.catalog-grid {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px 14px; margin-bottom: 22px;
}
.catalog-grid.two-col { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.catalog-card {
  min-height: 48px; display: flex; align-items: center; justify-content: center;
  flex-direction: column; gap: 2px;
  padding: 10px 12px; text-align: center; background: var(--surface);
  border: 1px solid var(--divider); border-radius: 7px; color: var(--vermillion);
  text-decoration: none !important; font-family: 'Noto Serif TC', serif;
  font-size: clamp(.86rem, 1vw, .98rem); font-weight: 600; line-height: 1.35;
}
.catalog-card:hover {
  background: var(--surface-hover); border-color: var(--gold); color: var(--vermillion-dk);
}
.catalog-card small {
  display: block; color: var(--ink-mute); font-family: 'Noto Sans TC', sans-serif;
  font-size: .76em; font-weight: 400;
}
.result-top-space { height: 18px; }

[data-testid="stTextInput"] > div > div > input {
  background: rgba(255,255,255,.7) !important; border: 1px solid var(--divider) !important;
  border-radius: 20px !important; color: var(--ink) !important;
  font-family: 'Noto Sans TC', sans-serif !important; padding: 6px 14px !important;
}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
  background-color: rgba(255,255,255,.74) !important;
  border: 1px solid var(--divider) !important;
  box-shadow: none !important;
  color: var(--ink) !important;
  caret-color: var(--vermillion) !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
  color: var(--ink-mute) !important;
  opacity: .78 !important;
}
[data-testid="stSidebar"] [data-testid="stTextInput"] div[data-baseweb="input"] {
  background: #fff !important;
  border: 1px solid var(--divider) !important;
  border-radius: 22px !important;
  box-shadow: none !important;
}
[data-testid="stSidebar"] [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 2px rgba(196,147,58,.2) !important;
}
[data-testid="stSidebar"] [data-testid="stTextInput"] input {
  background: transparent !important;
  border: none !important;
  color: #000 !important;
  box-shadow: none !important;
}
[data-testid="stSidebar"] [data-testid="stTextInput"] input::placeholder {
  color: rgba(0,0,0,.58) !important;
}
[data-testid="stTextInput"] > div > div > input:focus {
  border-color: var(--gold) !important; box-shadow: 0 0 0 2px rgba(196,147,58,.2) !important;
}
[data-testid="stSelectbox"] > div > div {
  background: rgba(255,255,255,.5) !important; border: 1px solid var(--divider) !important;
  border-radius: 6px !important;
}
[data-baseweb="select"] > div,
[data-baseweb="popover"] ul {
  background-color: rgba(255,255,255,.96) !important;
  border-color: var(--divider) !important;
  color: var(--ink) !important;
}
[data-baseweb="select"] span,
[data-baseweb="popover"] li,
[data-baseweb="popover"] div {
  color: var(--ink) !important;
}
[data-baseweb="checkbox"] span {
  border-color: var(--divider) !important;
}
[data-baseweb="checkbox"] input:checked + div,
[data-baseweb="checkbox"] div[aria-checked="true"] {
  background-color: var(--vermillion) !important;
  border-color: var(--vermillion) !important;
}

[data-testid="stButton"] > button,
[data-testid="stFormSubmitButton"] > button,
[data-testid="baseButton-secondary"],
[data-testid="baseButton-primary"] {
  background-color: var(--surface) !important;
  border: 1px solid var(--divider) !important;
  border-radius: 6px !important;
  box-shadow: none !important;
  color: var(--ink-lt) !important;
  font-family: 'Noto Sans TC', sans-serif !important;
  font-size: clamp(.78rem, .95vw, .95rem) !important;
  font-weight: 500 !important;
  min-height: 3.05rem !important;
  white-space: normal !important;
  line-height: 1.35 !important;
  transition: background-color .15s ease, border-color .15s ease, color .15s ease !important;
}
[data-testid="stButton"] > button:hover,
[data-testid="stFormSubmitButton"] > button:hover,
[data-testid="baseButton-secondary"]:hover {
  background-color: var(--surface-hover) !important;
  border-color: var(--gold) !important;
  color: var(--vermillion) !important;
}
[data-testid="stButton"] > button:focus,
[data-testid="stFormSubmitButton"] > button:focus {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 2px rgba(196,147,58,.22) !important;
  color: var(--vermillion) !important;
}
[data-testid="baseButton-primary"],
[data-testid="stFormSubmitButton"] button[kind="primary"],
[data-testid="stButton"] button[kind="primary"] {
  background-color: var(--vermillion) !important;
  border-color: var(--vermillion-dk) !important;
  color: var(--parchment) !important;
}
[data-testid="baseButton-primary"]:hover,
[data-testid="stFormSubmitButton"] button[kind="primary"]:hover,
[data-testid="stButton"] button[kind="primary"]:hover {
  background-color: var(--vermillion-dk) !important;
  border-color: var(--vermillion-dk) !important;
  color: #fff8e8 !important;
}
[data-testid="stButton"] button:disabled,
[data-testid="stFormSubmitButton"] button:disabled {
  background-color: rgba(255,255,255,.34) !important;
  border-color: rgba(212,184,135,.55) !important;
  color: rgba(92,61,37,.55) !important;
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
  background: var(--surface); border: 1px solid var(--divider); border-radius: 8px;
  padding: 14px 18px; margin: 8px 0 14px;
}
.needle-row { display: flex; gap: 12px; padding: 4px 0; border-bottom: 1px solid rgba(212,184,135,.3); }
.needle-row:last-child { border-bottom: none; }
.needle-lbl { font-size: .8em; color: var(--gold); font-weight: 600; min-width: 44px; }
.needle-val { font-size: .92em; color: var(--ink); line-height: 1.7; }

.location-grid {
  display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 2rem; align-items: stretch;
}
.location-panel {
  display: flex; flex-direction: column; min-width: 0;
}
.location-panel > .section-label {
  margin-top: 26px;
}
.location-image-frame {
  position: relative; flex: 1 1 auto; min-height: 0; height: 0;
  display: flex; align-items: flex-start; justify-content: center;
  overflow: hidden; border-radius: 8px;
}
.location-image-frame img {
  display: block; width: auto; height: auto;
  max-width: 100%; max-height: 100%; object-fit: contain; object-position: center top;
  border-radius: 8px;
}
.location-image-empty {
  color: var(--ink-mute); font-size: .82em; padding-top: 8px;
}
.location-caution {
  width: calc(50% - 1rem);
}
@media (max-width: 760px) {
  .location-grid { grid-template-columns: 1fr; gap: 0; }
  .location-image-frame { height: auto; max-height: 52vh; min-height: 220px; }
  .location-caution { width: 100%; }
}

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
  color: var(--ink-lt) !important; text-align: center !important; padding: 8px !important;
  font-family: 'Noto Serif TC', serif !important; font-size: 1.05em !important;
  font-weight: 600 !important; width: 100% !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
  color: var(--vermillion) !important; background: rgba(247,237,216,.42) !important;
}
.sidebar-section-title {
  font-family: 'Noto Serif TC', serif; font-size: .92em; font-weight: 700;
  letter-spacing: .08em; color: var(--ink); margin: 4px 0 8px; text-align: center;
}
.sidebar-preview {
  font-size: .9em; color: var(--ink-lt); line-height: 1.7;
  padding: 0 4px 6px; text-align: center;
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


def _html_text(value: str) -> str:
    return _html.escape(str(value or "")).replace("\n", "<br>")


def _nav_href(nav: str, **params) -> str:
    pairs = [("nav", nav)]
    pairs.extend((k, v) for k, v in params.items() if v)
    return "?" + "&".join(f"{k}={quote(str(v), safe='')}" for k, v in pairs)


def _query_value(params, key: str) -> str:
    val = params.get(key, "")
    if isinstance(val, list):
        return val[0] if val else ""
    return val or ""


def _apply_nav_query():
    params = st.query_params
    nav = _query_value(params, "nav")
    if nav not in NAV_MODE:
        return

    mode = NAV_MODE[nav]
    st.session_state.mode_idx = MODES.index(mode)
    st.session_state.mode_select = mode
    st.session_state.selected_ap = None
    st.session_state.pop("_pending_pair_name", None)

    sub = _query_value(params, "sub")
    category = _query_value(params, "cat")
    if nav == "acupoint":
        st.session_state.search_kw = ""
        st.session_state.pop("_pending_symptom", None)
        ap_id = _query_value(params, "ap")
        if ap_id:
            try:
                st.session_state.selected_ap = int(ap_id)
            except ValueError:
                st.session_state.selected_ap = None
            st.session_state.selected_region_code = None
        elif sub:
            st.session_state.selected_region_code = sub
    elif nav == "symptom":
        st.session_state.selected_region_code = None
        if sub:
            st.session_state.search_kw = sub
            st.session_state._pending_symptom = sub
        else:
            st.session_state.search_kw = ""
            st.session_state.pop("_pending_symptom", None)
    elif nav == "pair":
        st.session_state.selected_region_code = None
        st.session_state.pop("_pending_symptom", None)
        pair_name = _query_value(params, "pair")
        if pair_name:
            st.session_state.search_kw = ""
            st.session_state._pending_pair_name = pair_name
        else:
            st.session_state.search_kw = sub or category or ""

    try:
        st.query_params.clear()
    except Exception:
        pass


def _apply_admin_query():
    params = st.query_params
    if not _query_value(params, "admin"):
        return
    st.session_state.admin_panel_open = True
    try:
        if not _query_value(params, "nav"):
            st.query_params.clear()
    except Exception:
        pass


def _render_sidebar_nav(active_mode: str):
    region_items = []
    for code, name, body_part in dl.list_regions():
        label = f"{name}【{body_part}】" if body_part else name
        region_items.append((label, _nav_href("acupoint", sub=code)))

    symptom_items = [
        (
            section,
            _nav_href("symptom", section=section),
            [(item, _nav_href("symptom", sub=item)) for item in items],
        )
        for section, items in dl.default_symptom_groups()
    ]
    pair_items = [
        ("總綱", _nav_href("pair", cat="總綱"),
         [(x, _nav_href("pair", cat="總綱", sub=x)) for x in
          ("前身", "側身", "後身", "腹", "下腹", "提神", "疑難雜症", "解毒")]),
        ("內科", _nav_href("pair", cat="內科"),
         [(x, _nav_href("pair", cat="內科", sub=x)) for x in
          ("肺系", "心系", "胃腸系", "肝膽系", "內分泌")]),
        ("婦男科", _nav_href("pair", cat="婦男科"),
         [(x, _nav_href("pair", cat="婦男科", sub=x)) for x in ("婦科", "男科")]),
        ("五官科", _nav_href("pair", cat="五官科"),
         [(x, _nav_href("pair", cat="五官科", sub=x)) for x in
          ("顏面", "眼", "耳", "鼻", "口", "咽")]),
        ("皮膚及外科", _nav_href("pair", cat="皮膚及外科"),
         [(x, _nav_href("pair", cat="皮膚及外科", sub=x)) for x in ("皮膚", "外科")]),
        ("痛症", _nav_href("pair", cat="痛症"),
         [(x, _nav_href("pair", cat="痛症", sub=x)) for x in
          ("頭面", "肩背腰臀", "手足", "胸腹脅", "五官")]),
    ]

    nav_items = [
        ("acupoint", "穴位詮解", "📍 穴位", "flat", region_items),
        ("symptom", "治療析要", "💊 症狀", "nested", symptom_items),
        ("pair", "區位對針", "🔗 對針", "nested", pair_items),
    ]

    blocks = []
    for nav, label, mode, menu_type, items in nav_items:
        active_class = " is-active" if mode == active_mode else ""
        if menu_type == "nested":
            links = "\n".join(
                "<div class='sidebar-flyout-row'>"
                f"<a class='sidebar-flyout-main' href='{href}' target='_self'>{_html.escape(text)}</a>"
                "<div class='sidebar-subflyout'>"
                + "\n".join(
                    f"<a href='{child_href}' target='_self'>{_html.escape(child_text)}</a>"
                    for child_text, child_href in children
                )
                + "</div></div>"
                for idx, (text, href, children) in enumerate(items)
            )
        else:
            links = "\n".join(
                f"<a href='{href}' target='_self'>{_html.escape(text)}</a>"
                for text, href in items
            )
        blocks.append(f"""
<div class="sidebar-nav-item nav-{nav}{active_class}">
  <a class="sidebar-nav-main" href="{_nav_href(nav)}" target="_self">
    <span>{_html.escape(label)}</span>
    <span class="sidebar-nav-caret">›</span>
  </a>
  <div class="sidebar-flyout">
    {links}
  </div>
</div>""")

    st.sidebar.markdown(f"""
<div class="sidebar-nav-shell">
  <div class="sidebar-nav">
    {''.join(blocks)}
  </div>
</div>
""", unsafe_allow_html=True)

    components.html(
        """
<script>
(() => {
  const host = window.parent;
  const doc = host.document;
  const KEY = "__tungsacuFlyoutPositioner";
  if (host[KEY]?.cleanup) host[KEY].cleanup();

  const TOP_GAP = 136;
  const BOTTOM_GAP = 24;
  const CLOSE_DELAY = 300;
  let activeNavItem = null;
  let activeRow = null;
  let closeTimer = null;

  function place(row) {
    const submenu = row?.querySelector(":scope > .sidebar-subflyout");
    const flyout = row?.closest(".sidebar-flyout");
    if (!submenu || !flyout) return;

    const rowRect = row.getBoundingClientRect();
    const flyoutRect = flyout.getBoundingClientRect();
    const maxHeight = Math.max(180, host.innerHeight - TOP_GAP - BOTTOM_GAP);

    submenu.style.position = "fixed";
    submenu.style.left = `${Math.round(flyoutRect.right - 1)}px`;
    submenu.style.right = "auto";
    submenu.style.bottom = "auto";
    submenu.style.maxHeight = `${Math.floor(maxHeight)}px`;

    const panelHeight = Math.min(submenu.scrollHeight, maxHeight);
    const desiredTop = rowRect.top - 7;
    const latestTop = host.innerHeight - BOTTOM_GAP - panelHeight;
    const top = Math.max(TOP_GAP, Math.min(desiredTop, latestTop));
    submenu.style.top = `${Math.round(top)}px`;
  }

  function cancelClose() {
    if (closeTimer !== null) {
      host.clearTimeout(closeTimer);
      closeTimer = null;
    }
  }

  function closeMenus() {
    cancelClose();
    activeRow?.classList.remove("is-submenu-open");
    activeNavItem?.classList.remove("is-menu-open");
    activeRow = null;
    activeNavItem = null;
  }

  function scheduleClose() {
    cancelClose();
    closeTimer = host.setTimeout(closeMenus, CLOSE_DELAY);
  }

  function activateNavItem(navItem) {
    cancelClose();
    if (activeNavItem && activeNavItem !== navItem) {
      activeRow?.classList.remove("is-submenu-open");
      activeNavItem.classList.remove("is-menu-open");
      activeRow = null;
    }
    activeNavItem = navItem;
    activeNavItem.classList.add("is-menu-open");
  }

  function activateRow(row) {
    const navItem = row.closest(".sidebar-nav-item");
    if (!navItem) return;
    activateNavItem(navItem);
    if (activeRow && activeRow !== row) {
      activeRow.classList.remove("is-submenu-open");
    }
    activeRow = row;
    place(row);
    row.classList.add("is-submenu-open");
  }

  function onPointerOver(event) {
    const target = event.target;
    if (!(target instanceof host.Element)) return;
    const row = target.closest(".sidebar-flyout-row");
    if (row) {
      activateRow(row);
      return;
    }
    const navItem = target.closest(".sidebar-nav-item");
    if (navItem) activateNavItem(navItem);
  }

  function onPointerOut(event) {
    const target = event.target;
    if (!(target instanceof host.Element)) return;
    const navItem = target.closest(".sidebar-nav-item");
    if (!navItem || navItem !== activeNavItem) return;

    const related = event.relatedTarget;
    if (related instanceof host.Node && navItem.contains(related)) return;
    scheduleClose();
  }

  function onFocusIn(event) {
    const target = event.target;
    if (!(target instanceof host.Element)) return;
    const row = target.closest(".sidebar-flyout-row");
    if (row) {
      activateRow(row);
      return;
    }
    const navItem = target.closest(".sidebar-nav-item");
    if (navItem) activateNavItem(navItem);
  }

  function onFocusOut(event) {
    const target = event.target;
    if (!(target instanceof host.Element)) return;
    const navItem = target.closest(".sidebar-nav-item");
    if (!navItem || navItem !== activeNavItem) return;

    const related = event.relatedTarget;
    if (related instanceof host.Node && navItem.contains(related)) return;
    scheduleClose();
  }

  function onResize() {
    if (activeRow?.isConnected) place(activeRow);
  }

  doc.addEventListener("pointerover", onPointerOver, true);
  doc.addEventListener("pointerout", onPointerOut, true);
  doc.addEventListener("focusin", onFocusIn, true);
  doc.addEventListener("focusout", onFocusOut, true);
  host.addEventListener("resize", onResize);

  host[KEY] = {
    cleanup() {
      closeMenus();
      doc.removeEventListener("pointerover", onPointerOver, true);
      doc.removeEventListener("pointerout", onPointerOut, true);
      doc.removeEventListener("focusin", onFocusIn, true);
      doc.removeEventListener("focusout", onFocusOut, true);
      host.removeEventListener("resize", onResize);
    }
  };
})();
</script>
""",
        height=0,
        width=0,
    )


def _render_symptom_grid(groups):
    for section, items in groups:
        st.markdown(f"<div class='catalog-section-title'>{section}</div>", unsafe_allow_html=True)
        for row_start in range(0, len(items), 4):
            chunk = items[row_start:row_start + 4]
            cols = st.columns(len(chunk))
            for idx, symptom in enumerate(chunk):
                with cols[idx]:
                    if st.button(
                        symptom,
                        key=f"sym_grid_{section}_{row_start}_{idx}",
                        use_container_width=True,
                    ):
                        st.session_state._pending_mode = "💊 症狀"
                        st.session_state._pending_symptom = symptom
                        st.session_state._set_search_kw = symptom
                        st.session_state.selected_ap = None
                        st.rerun()


def _render_catalog_grid(groups, nav: str, param: str = "sub"):
    for section, items in groups:
        cards = []
        for label, value in items:
            cards.append(
                f"<a class='catalog-card' href='{_nav_href(nav, **{param: value})}' target='_self'>"
                f"{_html.escape(label)}</a>"
            )
        st.markdown(
            f"<div class='catalog-section-title'>{_html.escape(section)}</div>"
            f"<div class='catalog-grid'>{''.join(cards)}</div>",
            unsafe_allow_html=True,
        )


def _render_acupoint_cards_grid(df):
    if df.empty:
        st.caption("目前沒有符合條件的穴位")
        return
    cards = []
    for _, row in df.iterrows():
        label = row.get("穴名", "")
        sub = row.get("部位", "") or row.get("身體分區", "")
        content = f"<span>{_html.escape(label)}</span>"
        if sub:
            content += f"<small>{_html.escape(sub)}</small>"
        cards.append(
            f"<a class='catalog-card' href='{_nav_href('acupoint', ap=row.get('id'))}' target='_self'>"
            f"{content}</a>"
        )
    st.markdown(
        f"<div class='catalog-grid'>{''.join(cards)}</div>",
        unsafe_allow_html=True,
    )


def _acupoint_catalog_groups():
    df = dl.load_acupoints_df()
    groups = []
    for code, name, body_part in dl.list_regions():
        section = f"{name}【{body_part.replace('穴位', '')}】" if body_part else name
        rows = df[df["部位代碼"] == code]
        items = [(row["穴名"], str(row["id"])) for _, row in rows.iterrows()]
        if items:
            groups.append((section, items))
    return groups


def _pair_catalog_groups():
    df = dl.pair_groups_df().sort_values(["目錄排序", "穴組名稱"])
    groups: list[tuple[str, list[tuple[str, str]]]] = []
    for category, cat_df in df.groupby("大類", sort=False):
        items = []
        for _, row in cat_df.iterrows():
            label = row["穴組名稱"]
            if row.get("穴位", ""):
                label = f"{label}｜{row['穴位']}"
            items.append((label, row["穴組名稱"]))
        if items:
            groups.append((category or "其他", items))
    return groups


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

    badge_region = f"<span class='detail-badge'>📍 {rname}{('　'+rbody) if rbody else ''}</span>"
    st.markdown(f"""
<div class="detail-header">
  <div class="detail-code-circle">
    <span class="detail-code-num">{fig}</span>
    <span class="detail-code-label">穴號</span>
  </div>
  <div>
    <div class="detail-title">{name}</div>
    <div class="detail-badges">{badge_region}</div>
  </div>
</div>""", unsafe_allow_html=True)

    loc = d.get("取穴定位", "")
    needle = d.get("針法", "")
    caution = d.get("備註", "")
    kw_raw = d.get("主治關鍵字", "")
    kws = dl.split_kw(kw_raw)
    standard_kws, supplemental_kws = dl.standardize_keywords(kws)
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
        location_html = (
            "<div class='location-grid'>"
            "<section class='location-panel'>"
            "<div class='section-label'>位置</div>"
            f"<div class='section-body'>{_html_text(loc) if loc else '此穴暫無位置資料'}</div>"
        )
        if needle:
            location_html += (
                "<div class='section-label'>針法</div>"
                "<div class='needle-card'>"
                "<div class='needle-row'><span class='needle-lbl'>針法</span>"
                f"<span class='needle-val'>{_html_text(needle)}</span></div></div>"
            )
        location_html += (
            "</section>"
            "<section class='location-panel'>"
            "<div class='section-label'>穴位圖</div>"
        )
        if img_abs:
            image_uri = _img_to_data_uri(img_abs)
            location_html += (
                "<div class='location-image-frame'>"
                f"<img src='{image_uri}' alt='{_html.escape(name)}穴位圖'>"
                + "</div>"
            )
        else:
            location_html += "<div class='location-image-empty'>此穴尚無圖</div>"
        location_html += "</section></div>"
        st.markdown(location_html, unsafe_allow_html=True)

        if caution:
            st.markdown(
                "<div class='location-caution'>"
                "<div class='section-label'>備註</div>"
                f"<div class='section-body'>{_html_text(caution)}</div></div>",
                unsafe_allow_html=True,
            )

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
        if standard_kws:
            st.markdown("<div class='section-label'>標準主治症狀</div>", unsafe_allow_html=True)
            n_cols = 4
            cols = st.columns(n_cols)
            for i, kw in enumerate(standard_kws):
                with cols[i % n_cols]:
                    if st.button(kw, key=f"std_kw_{ap_id}_{i}", use_container_width=True):
                        st.session_state._pending_mode = "💊 症狀"
                        st.session_state._pending_symptom = kw
                        st.session_state._set_search_kw = kw
                        st.session_state.selected_ap = None
                        st.rerun()
        else:
            st.caption("此穴暫無已對齊的標準主治症狀")

        if supplemental_kws:
            container = st.expander("相關關鍵字") if standard_kws else st.container()
            with container:
                st.markdown("<div class='section-label'>相關關鍵字</div>", unsafe_allow_html=True)
                if standard_kws:
                    st.caption("原始主治關鍵字中尚未對齊標準症狀詞的補充提示")
                n_cols = 4
                cols = st.columns(n_cols)
                for i, kw in enumerate(supplemental_kws):
                    with cols[i % n_cols]:
                        refs = dl.same_acupoint_refs(kw)
                        label = f"{kw} → {refs[0]['穴名']}" if refs else kw
                        if st.button(label, key=f"supp_kw_{ap_id}_{i}", use_container_width=True):
                            if refs:
                                st.session_state.selected_ap = int(refs[0]["id"])
                            else:
                                st.session_state._pending_mode = "💊 症狀"
                                st.session_state._pending_symptom = kw
                                st.session_state._set_search_kw = kw
                                st.session_state.selected_ap = None
                            st.rerun()

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
                title = p.get("穴組名稱", "")
                points = p.get("穴位", "")
                ind = p.get("主治關鍵字", "")
                std_ind = dl.standardize_text_keywords(ind)
                theory = p.get("理論與發揮", "")
                pg = p.get("頁碼", "")
                with st.expander(f"**{title}**　｜　{points}"):
                    if ind: st.markdown(f"**主治：** {ind}")
                    if std_ind: st.caption(f"標準症狀：{'、'.join(std_ind)}")
                    if theory: st.markdown(f"**理論與發揮：** {theory[:240]}{'…' if len(theory) > 240 else ''}")
                    if pg: st.caption(f"p.{pg}")
                    if st.button("查看這組對針", key=f"ap_pair_{p.get('目錄排序')}_{title}"):
                        st.session_state.mode_idx = MODES.index("🔗 對針")
                        st.session_state._pending_pair_name = title
                        st.session_state.selected_ap = None
                        st.rerun()

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


def render_pair_group_detail(pair_name: str):
    rows = dl.pair_rows_for_name(pair_name)
    if rows.empty:
        st.warning("找不到這組對針")
        return

    group = rows.iloc[0].to_dict()
    title = group.get("穴組名稱", pair_name)
    keywords = group.get("主治關鍵字", "")
    theory = group.get("理論與發揮", "")
    page = group.get("頁碼", "")

    st.markdown("<div class='section-label'>對針組合查詢</div>", unsafe_allow_html=True)
    st.markdown(
        f"<h3 style='font-family:Noto Serif TC,serif;color:var(--vermillion);margin-bottom:0'>"
        f"{title}</h3>",
        unsafe_allow_html=True,
    )
    meta = []
    if group.get("大類"):
        meta.append(group["大類"])
    if group.get("次分類"):
        meta.append(group["次分類"])
    if group.get("目錄排序"):
        meta.append(f"排序 {group['目錄排序']}")
    if page:
        meta.append(f"p.{page}")
    if meta:
        st.caption(" ｜ ".join(meta))
    if keywords:
        st.markdown(f"**主治關鍵字：** {keywords}")

    for idx, (_, row) in enumerate(rows.iterrows(), start=1):
        point_name = row.get("穴名", "")
        st.markdown(
            f"<div class='section-label'>第 {idx} 穴：{point_name}</div>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns([1.15, 0.85])
        with c1:
            if row.get("位置"):
                st.markdown(f"**位置**\n\n{row['位置']}")
            if row.get("針法"):
                st.markdown(f"**針法**\n\n{row['針法']}")
        with c2:
            img_rel = row.get("圖片") or ""
            img_path = dl.image_abs_path(img_rel)
            if img_path:
                st.image(str(img_path), use_container_width=True)
            else:
                st.caption("暫無圖片")

    st.markdown("<div class='section-label'>兩穴解析與理論與發揮</div>", unsafe_allow_html=True)
    for idx, (_, row) in enumerate(rows.iterrows(), start=1):
        if row.get("解析"):
            st.markdown(f"**{idx}. {row.get('穴名', '')} 解析**\n\n{row.get('解析', '')}")
    if theory:
        st.markdown("**理論與發揮**")
        st.markdown(theory)


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
    if "_set_pending_pair_name" in st.session_state:
        st.session_state._pending_pair_name = st.session_state.pop("_set_pending_pair_name")
    if "_set_pending_pair" in st.session_state:
        legacy = st.session_state.pop("_set_pending_pair")
        if isinstance(legacy, tuple) and len(legacy) == 2:
            legacy_row = dl.find_pair(*legacy)
            if legacy_row:
                st.session_state._pending_pair_name = legacy_row.get("穴組名稱", "")

    mode_idx = st.session_state.get("mode_idx", 0)
    sel = MODES[mode_idx]
    prev_mode_idx = st.session_state.get("_prev_mode_idx", mode_idx)
    if prev_mode_idx != mode_idx:
        for k in ("search_kw", "_pending_symptom", "_pending_pair", "_pending_pair_name", "_set_search_kw", "_set_pending_pair_name"):
            st.session_state.pop(k, None)
        st.session_state.selected_ap = None
        st.session_state.selected_region = None
    st.session_state.mode_idx = mode_idx
    st.session_state._prev_mode_idx = mode_idx
    mode = sel

    placeholder = {"📍 穴位": "輸入穴位名稱或編號…",
                   "💊 症狀": "輸入症狀關鍵字…",
                   "🔗 對針": "輸入症狀或穴位名稱…"}.get(mode, "")
    st.sidebar.markdown("<div class='sidebar-layout-anchor'></div>", unsafe_allow_html=True)
    st.sidebar.text_input("搜尋", placeholder=placeholder,
                          key="search_kw", label_visibility="collapsed")
    _render_sidebar_nav(sel)


def render_admin_panel():
    if not st.session_state.get("admin_panel_open") and not st.session_state.get("admin_mode"):
        return

    with st.container(border=True):
        if st.session_state.get("admin_mode"):
            c1, c2, c3, c4 = st.columns([1.4, 1, 1, 1])
            c1.markdown("**管理員模式已開啟**")
            if c2.button("新增穴位", key="admin_create_top", use_container_width=True):
                st.session_state.create_ap_open = True
                st.session_state.image_review_open = False
                st.rerun()
            if c3.button("圖片審核", key="admin_image_top", use_container_width=True):
                st.session_state.image_review_open = True
                st.session_state.create_ap_open = False
                st.rerun()
            if c4.button("關閉", key="admin_close_top", use_container_width=True):
                st.session_state.admin_mode = False
                st.session_state.admin_panel_open = False
                st.session_state.image_review_open = False
                st.session_state.create_ap_open = False
                st.rerun()
            return

        with st.form("admin_login_form"):
            pw = st.text_input("管理員密碼", type="password")
            c1, c2 = st.columns([1, 1])
            login = c1.form_submit_button("登入", use_container_width=True)
            close = c2.form_submit_button("取消", use_container_width=True)
            if login:
                if pw == st.secrets.get("admin_password", "admin123"):
                    st.session_state.admin_mode = True
                    st.session_state.admin_panel_open = True
                    st.rerun()
                else:
                    st.error("密碼錯誤")
            if close:
                st.session_state.admin_panel_open = False
                st.rerun()


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
            resolved_terms = dl.resolve_symptom_query(kw)
            results = dl.search_symptoms_in_acupoints(kw)
            st.markdown(f"**「{kw}」— 找到 {len(results)} 個穴位**")
            if resolved_terms[1:]:
                st.caption(f"對應標準詞／別名：{'、'.join(resolved_terms[1:8])}")
            else:
                st.caption("此詞目前尚未對齊標準症狀，先以原始關鍵字搜尋。")
            if st.button("← 返回症狀清單", key="symptom_back"):
                st.session_state._set_search_kw = ""
                st.session_state.pop("_pending_symptom", None)
                st.rerun()
            _render_acupoint_cards_grid(results)
        else:
            groups = dl.default_symptom_groups()
            _render_symptom_grid(groups)
        return

    if mode == "🔗 對針":
        pending_pair_name = st.session_state.get("_pending_pair_name")
        if search:
            resolved_terms = dl.resolve_symptom_query(search)
            results = dl.search_pairs_df(search)
            st.markdown("<div class='result-top-space'></div>", unsafe_allow_html=True)
            st.markdown(f"**「{search}」— 找到 {len(results)} 組對針**")
            if resolved_terms[1:]:
                st.caption(f"對應標準詞／別名：{'、'.join(resolved_terms[1:8])}")
            cards = []
            for _, p in results.iterrows():
                title = p.get("穴組名稱", "")
                points = p.get("穴位", "")
                cards.append(
                    f"<a class='pair-result-card' href='{_nav_href('pair', pair=title)}' target='_self'>"
                    f"<span class='pair-result-title'>{_html.escape(title)}</span>"
                    f"<span class='pair-result-points'>{_html.escape(points)}</span>"
                    "</a>"
                )
            st.markdown(
                f"<div class='pair-result-list'>{''.join(cards)}</div>",
                unsafe_allow_html=True,
            )
        elif pending_pair_name:
            render_pair_group_detail(pending_pair_name)
            if st.button("← 返回對針清單", key="pair_back"):
                st.session_state.pop("_pending_pair_name", None)
                st.rerun()
        else:
            _render_catalog_grid(_pair_catalog_groups(), "pair", param="pair")
        return

    # 穴位模式
    if search:
        results = dl.search_acupoints_df(search)
        st.markdown(f"**搜尋「{search}」— 找到 {len(results)} 個穴位**")
        _render_acupoint_cards_grid(results)
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
        _render_acupoint_cards_grid(rdf)
        return

    # 穴位首頁
    _render_catalog_grid(_acupoint_catalog_groups(), "acupoint", param="ap")


# ── 主程式 ────────────────────────────────────────────────────────────────
def main():
    _inject_css()
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
  <a class="app-admin-link" href="?admin=1" target="_self">管理員</a>
</div>
""", unsafe_allow_html=True)

    for k, v in [("selected_ap", None), ("selected_region_code", None),
                 ("mode_idx", 0), ("admin_mode", False),
                 ("image_review_open", False), ("create_ap_open", False),
                 ("admin_panel_open", False)]:
        st.session_state.setdefault(k, v)

    _apply_admin_query()
    _apply_nav_query()

    if "_pending_mode" in st.session_state:
        pending = st.session_state.pop("_pending_mode")
        st.session_state.mode_idx = MODES.index(pending)
        st.session_state.mode_select = pending

    render_sidebar()
    render_admin_panel()
    render_main()

    if "_pending_symptom" in st.session_state and not st.session_state.get("selected_ap"):
        if st.session_state.get("search_kw"):
            st.session_state.pop("_pending_symptom", None)
    if st.session_state.get("search_kw"):
        st.session_state.pop("_pending_pair", None)
        st.session_state.pop("_pending_pair_name", None)


if __name__ == "__main__":
    main()
