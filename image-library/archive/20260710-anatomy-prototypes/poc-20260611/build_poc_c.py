#!/usr/bin/env python3
"""指駟馬穴 PoC C 版：WHO 標準線稿底圖（手背＋骨骼透視）＋ 標註層 ＋ 放大圈。

底圖 who_hand_dorsum_clean.svg 由 prepare_who_base.py 產生（座標系 = PDF pt）。
錨點由格線量測：食指 DIP 關節 (364.5, 204.5)、PIP 關節 (370.0, 243.0)，
指寬約 25 單位（一寸 = 十分），外開二分 ≈ 5（尺側）。

v2 修正：
- 文字全部轉外框路徑（text2path.py），不依賴檢視端字型與編碼判讀。
- 開頭補 XML 編碼宣告。
- 放大圈標註改用指軸座標系 loc(u,v)：橫紋、尺寸線、括線全部垂直於指軸，
  不再是水平/垂直線貼在斜的手指上。
"""
import math
from pathlib import Path

from text2path import SANS, SANS_BOLD, SERIF_BOLD

HERE = Path(__file__).parent

# ── 底圖錨點（base SVG 座標）──
DIPc = (364.5, 204.5)
PIPc = (370.0, 243.0)
ULNAR = 5.0          # 外開二分（朝尺側）

_L = math.hypot(PIPc[0] - DIPc[0], PIPc[1] - DIPc[1])
_ev = ((PIPc[0] - DIPc[0]) / _L, (PIPc[1] - DIPc[1]) / _L)   # 沿指軸（DIP→PIP）
_eu = (_ev[1], -_ev[0])                                       # 垂直指軸，+u = 尺側（畫面右）


def loc(u, v):
    """指軸座標 → base 座標。u 垂直指軸（+尺側），v 沿指軸（0=DIP, _L=PIP）"""
    return (DIPc[0] + u * _eu[0] + v * _ev[0], DIPc[1] + u * _eu[1] + v * _ev[1])


def ann(t):
    return loc(ULNAR, t * _L)


POINTS = [ann(0.25), ann(0.5), ann(0.75)]

# ── 畫布與兩個視圖的座標映射 ──
CANVAS_W, CANVAS_H = 1120, 1100
S, TX, TY = 3.0, 60, 110            # 全手：canvas = (X-300)*S+TX, (Y-96)*S+TY
SI = 7.0                            # 放大圈倍率
ICX, ICY, IR = 810, 430, 235        # 放大圈圓心與半徑
IFX, IFY = 367.25, 223.75           # 放大圈對準的底圖座標（中節中心）

INK = "#2C1C10"
GOLD = "#C4933A"
VERMILLION = "#7B2D1E"
RED = "#B3261E"
HALO = "#FBF6EA"


def mp(p):
    return ((p[0] - 300) * S + TX, (p[1] - 96) * S + TY)


def mi(p):
    return ((p[0] - IFX) * SI + ICX, (p[1] - IFY) * SI + ICY)


def line(p1, p2, **attrs):
    a = " ".join(f"{k.replace('_','-')}='{v}'" for k, v in attrs.items())
    return (
        f"<line x1='{p1[0]:.1f}' y1='{p1[1]:.1f}' x2='{p2[0]:.1f}' y2='{p2[1]:.1f}' {a}/>"
    )


def otext(x, y, size, fill, text, anchor="start", face=SANS, opacity=1, halo=False):
    """文字外框路徑。halo=True 時先鋪一層淡色描邊，疊在線稿上仍可讀。"""
    d, w = face.path_d(text, size)
    dx = -w / 2 if anchor == "middle" else (-w if anchor == "end" else 0)
    tf = f"translate({x + dx:.1f},{y:.1f}) scale(1,-1)"
    s = ""
    if halo:
        s += (
            f"<path d='{d}' transform='{tf}' fill='none' stroke='{HALO}' "
            f"stroke-width='4' stroke-linejoin='round' opacity='.9'/>"
        )
    op = f" fill-opacity='{opacity}'" if opacity != 1 else ""
    s += f"<path d='{d}' transform='{tf}' fill='{fill}'{op}/>"
    return s


def base_body():
    svg = (HERE / "who_hand_dorsum_clean.svg").read_text()
    return svg.split("</defs>")[1].rsplit("</svg>", 1)[0]


def embed(body, fx, fy, scale, anchor_xy, clip_id):
    """把底圖 body 以 scale 嵌入，使底圖座標 (fx,fy) 對到畫布 anchor_xy"""
    tx = anchor_xy[0] - fx * scale
    ty = anchor_xy[1] - fy * scale
    return (
        f"<g clip-path='url(#{clip_id})'>"
        f"<g transform='translate({tx:.2f},{ty:.2f}) scale({scale})'>{body}</g></g>"
    )


def main_annotations():
    s = "<g id='main-ann'>"
    for p in POINTS:
        x, y = mp(p)
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='4.6' fill='{RED}' stroke='#FFFFFF' stroke-width='1.4'/>"
    ccx, ccy = mp((IFX, IFY))
    s += (
        f"<circle cx='{ccx:.1f}' cy='{ccy:.1f}' r='70' fill='none' "
        f"stroke='{GOLD}' stroke-width='1.6' stroke-dasharray='6 4'/>"
    )
    s += line((ccx + 49.5, ccy - 49.5), (ICX - 203, ICY - 117),
              stroke=GOLD, stroke_width=1.2, stroke_opacity=.75)
    s += line((ccx + 49.5, ccy + 49.5), (ICX - 203, ICY + 117),
              stroke=GOLD, stroke_width=1.2, stroke_opacity=.75)
    return s + "</g>"


def inset_annotations():
    """放大圈標註：全部以指軸座標 loc(u,v) 定義，自然跟著手指傾斜。"""
    s = "<g id='inset-ann'>"
    # DIP / PIP 橫紋（垂直於指軸的虛線）＋標籤（圈內左側，文字保持水平）
    for v, hw, label in ((0, 14.5, "遠端指節橫紋"), (_L, 15.5, "近端指節橫紋")):
        s += line(mi(loc(-hw, v)), mi(loc(hw, v)),
                  stroke=INK, stroke_opacity=.7, stroke_width=1.8, stroke_dasharray="6 4")
        lx, ly = mi(loc(-hw - 2, v))
        s += otext(lx, ly + 5, 16, INK, label, anchor="end", opacity=.85, halo=True)
    # 中央線（金色虛線，沿指軸向上下延伸）
    s += line(mi(loc(0, -7)), mi(loc(0, _L + 4.5)),
              stroke=GOLD, stroke_width=1.8, stroke_dasharray="8 5")
    cx0, cy0 = mi(loc(-1.5, -9))
    s += otext(cx0, cy0, 16, "#8A6420", "中央線", anchor="end", face=SANS_BOLD, halo=True)
    # 標註線（外開二分，與中央線平行）
    s += line(mi(ann(0.0)), mi(ann(1.0)), stroke=RED, stroke_width=1.4, stroke_opacity=.5)
    # 二分 尺寸標註（DIP 上方，沿垂直指軸方向）
    vd = -4
    s += line(mi(loc(0, vd)), mi(loc(ULNAR, vd)), stroke=INK, stroke_width=1.4)
    for u in (0, ULNAR):
        s += line(mi(loc(u, vd - 1.5)), mi(loc(u, vd + 1.5)), stroke=INK, stroke_width=1.4)
    tx, ty = mi(loc(ULNAR / 2, vd - 3))
    s += otext(tx + 6, ty, 15, INK, "二分", halo=True)
    # 四分點刻度括線（指尺側外，沿指軸）
    s += line(mi(loc(17, 0)), mi(loc(17, _L)), stroke=INK, stroke_width=1.4)
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        w = 1.9 if t in (0, 1.0) else 1.2
        s += line(mi(loc(17 - w, t * _L)), mi(loc(17 + w, t * _L)), stroke=INK, stroke_width=1.4)
    bx, by = mi(loc(19.5, _L * 0.5))
    s += otext(bx, by - 6, 16, INK, "四分點法", face=SANS_BOLD, halo=True)
    s += otext(bx, by + 16, 14, INK, "均分四等份取三穴", opacity=.8, halo=True)
    # 穴位紅點
    for p in POINTS:
        x, y = mi(p)
        s += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='9' fill='{RED}' stroke='#FFFFFF' stroke-width='2.6'/>"
    return s + "</g>"


def label_layer():
    bx, by, bw, bh = 36, 130, 200, 64
    ccx, ccy = mp((IFX, IFY))
    s = "<g id='labels'>"
    s += (
        f"<rect x='{bx}' y='{by}' width='{bw}' height='{bh}' rx='6' fill='#FFFDF6' "
        f"stroke='{GOLD}' stroke-width='1.6'/>"
        + otext(bx + bw / 2, by + 28, 21, VERMILLION, "指駟馬穴（三穴）",
                anchor="middle", face=SERIF_BOLD)
        + otext(bx + bw / 2, by + 50, 13.5, INK, "食指背第二節．中央線外開二分",
                anchor="middle", opacity=.8)
        + line((bx + bw / 2, by + bh), (ccx - 42, ccy - 56),
               stroke=INK, stroke_opacity=.5, stroke_width=1.1)
    )
    return s + "</g>"


def header_legend_attrib():
    s = "<g id='header'>"
    s += (
        f"<rect x='24' y='22' width='62' height='30' fill='{VERMILLION}'/>"
        + otext(55, 43, 16, "#F7EDD8", "11.07", anchor="middle")
        + otext(98, 45, 26, INK, "指駟馬穴", face=SERIF_BOLD)
        + otext(24, 76, 14, INK, "底圖：WHO 標準經穴定位線稿（手背觀．骨骼透視）｜C 版", opacity=.65)
        + otext(ICX, 172, 17, INK, "食指背第二節（放大）", anchor="middle", face=SANS_BOLD)
    )
    # 圖例（右下）
    lx, ly = 880, CANVAS_H - 92
    s += (
        f"<rect x='{lx}' y='{ly}' width='22' height='14' fill='#e6e7e8' stroke='#6d6e71' stroke-width='1.2'/>"
        + otext(lx + 30, ly + 12, 14, INK, "骨骼透視")
        + f"<circle cx='{lx+11}' cy='{ly+31}' r='6.5' fill='{RED}' stroke='#FFFFFF' stroke-width='2'/>"
        + otext(lx + 30, ly + 36, 14, INK, "穴位點")
        + line((lx, ly + 52), (lx + 22, ly + 52), stroke=GOLD, stroke_width=1.8, stroke_dasharray="8 5")
        + otext(lx + 30, ly + 57, 14, INK, "中央線")
    )
    # 來源標示（左下）
    s += otext(24, CANVAS_H - 18, 12, INK,
               "底圖｜WHO Standard Acupuncture Point Locations in the Western Pacific Region (2008)　標註｜TungsAcu-DB",
               opacity=.55)
    return s + "</g>"


def build():
    body = base_body()
    x0, y0 = mp((296.5, 95))
    x1, y1 = mp((502, 385.4))
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {CANVAS_W} {CANVAS_H}'>
  <defs>
    <clipPath id='clip-main'><rect x='{x0:.0f}' y='{y0:.0f}' width='{x1-x0:.0f}' height='{y1-y0:.0f}'/></clipPath>
    <clipPath id='clip-inset'><circle cx='{ICX}' cy='{ICY}' r='{IR}'/></clipPath>
  </defs>
  <rect width='{CANVAS_W}' height='{CANVAS_H}' fill='#FBF6EA'/>
  {embed(body, 300, 96, S, (TX, TY), 'clip-main')}
  {main_annotations()}
  <circle cx='{ICX}' cy='{ICY}' r='{IR}' fill='#FFFFFF' stroke='{GOLD}' stroke-width='2.2'/>
  {embed(body, IFX, IFY, SI, (ICX, ICY), 'clip-inset')}
  <circle cx='{ICX}' cy='{ICY}' r='{IR}' fill='none' stroke='{GOLD}' stroke-width='2.2'/>
  {inset_annotations()}
  {label_layer()}
  {header_legend_attrib()}
</svg>"""
    out = HERE / "指駟馬_C版_WHO線稿.svg"
    out.write_text(svg, encoding="utf-8")
    print("產出:", out.name, f"({len(svg)//1024} KB)")


if __name__ == "__main__":
    build()
