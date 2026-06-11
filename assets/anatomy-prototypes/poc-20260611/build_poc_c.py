#!/usr/bin/env python3
"""指駟馬穴 PoC C 版：WHO 標準線稿底圖（手背＋骨骼透視）＋ 標註層 ＋ 放大圈。

底圖 who_hand_dorsum_clean.svg 由 prepare_who_base.py 產生（座標系 = PDF pt）。
錨點由格線量測：食指 DIP 關節 (364.5, 204.5)、PIP 關節 (370.0, 243.0)，
指寬約 25 單位（一寸 = 十分），外開二分 ≈ +5（尺側，畫面右）。
"""
import re
from pathlib import Path

HERE = Path(__file__).parent

# ── 底圖錨點（base SVG 座標）──
DIPc = (364.5, 204.5)
PIPc = (370.0, 243.0)
ULNAR = 5.0          # 外開二分（+x = 尺側）
SKIN_L, SKIN_R = 352.0, 379.0   # 食指中節兩側皮緣（約略）


def cl(t):
    """中央線上的點，t=0 在 DIP、t=1 在 PIP"""
    return (DIPc[0] + t * (PIPc[0] - DIPc[0]), DIPc[1] + t * (PIPc[1] - DIPc[1]))


def ann(t):
    x, y = cl(t)
    return (x + ULNAR, y)


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


def halo_text(x, y, size, fill, text, anchor="start", weight=None, opacity=1):
    w = f" font-weight='{weight}'" if weight else ""
    common = (
        f"x='{x:.1f}' y='{y:.1f}' font-size='{size}' text-anchor='{anchor}'"
        f"{w} font-family='Noto Sans TC, sans-serif'"
    )
    return (
        f"<text {common} fill='none' stroke='{HALO}' stroke-width='4' "
        f"stroke-linejoin='round' opacity='.9'>{text}</text>"
        f"<text {common} fill='{fill}' fill-opacity='{opacity}'>{text}</text>"
    )


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
    # 中節範圍小圈（連到放大圈）
    ccx, ccy = mp((IFX, IFY))
    s += (
        f"<circle cx='{ccx:.1f}' cy='{ccy:.1f}' r='70' fill='none' "
        f"stroke='{GOLD}' stroke-width='1.6' stroke-dasharray='6 4'/>"
    )
    # 連接線（小圈 → 放大圈）
    s += (
        f"<line x1='{ccx+49.5:.0f}' y1='{ccy-49.5:.0f}' x2='{ICX-203}' y2='{ICY-117}' "
        f"stroke='{GOLD}' stroke-width='1.2' stroke-opacity='.75'/>"
        f"<line x1='{ccx+49.5:.0f}' y1='{ccy+49.5:.0f}' x2='{ICX-203}' y2='{ICY+117}' "
        f"stroke='{GOLD}' stroke-width='1.2' stroke-opacity='.75'/>"
    )
    return s + "</g>"


def inset_annotations():
    s = "<g id='inset-ann'>"
    # DIP / PIP 橫紋（虛線）＋標籤（放圈內左側空白區）
    for (jx, jy), label in ((DIPc, "遠端指節橫紋"), (PIPc, "近端指節橫紋")):
        (x1, y), (x2, _) = mi((SKIN_L - 1.5, jy)), mi((SKIN_R + 1.5, jy))
        s += (
            f"<line x1='{x1:.0f}' y1='{y:.0f}' x2='{x2:.0f}' y2='{y:.0f}' "
            f"stroke='{INK}' stroke-opacity='.7' stroke-width='1.8' stroke-dasharray='6 4'/>"
            + halo_text(x1 - 10, y + 5, 16, INK, label, anchor="end", opacity=.85)
        )
    # 中央線（金色虛線，向上下各延伸一點）
    (cx0, cy0), (cx1, cy1) = mi(cl(-0.18)), mi(cl(1.12))
    s += (
        f"<line x1='{cx0:.0f}' y1='{cy0:.0f}' x2='{cx1:.0f}' y2='{cy1:.0f}' "
        f"stroke='{GOLD}' stroke-width='1.8' stroke-dasharray='8 5'/>"
        + halo_text(cx0 - 6, cy0 - 8, 16, "#8A6420", "中央線", anchor="end", weight=700)
    )
    # 標註線（外開二分）
    (ax0, ay0), (ax1, ay1) = mi(ann(0.0)), mi(ann(1.0))
    s += (
        f"<line x1='{ax0:.0f}' y1='{ay0:.0f}' x2='{ax1:.0f}' y2='{ay1:.0f}' "
        f"stroke='{RED}' stroke-width='1.4' stroke-opacity='.5'/>"
    )
    # 二分 尺寸標註（DIP 上方）
    t2 = -0.12
    (bx0, by), (bx1, _) = mi(cl(t2)), mi(ann(t2))
    s += (
        f"<line x1='{bx0:.0f}' y1='{by:.0f}' x2='{bx1:.0f}' y2='{by:.0f}' stroke='{INK}' stroke-width='1.4'/>"
        f"<line x1='{bx0:.0f}' y1='{by-5:.0f}' x2='{bx0:.0f}' y2='{by+5:.0f}' stroke='{INK}' stroke-width='1.4'/>"
        f"<line x1='{bx1:.0f}' y1='{by-5:.0f}' x2='{bx1:.0f}' y2='{by+5:.0f}' stroke='{INK}' stroke-width='1.4'/>"
        + halo_text((bx0 + bx1) / 2, by - 10, 15, INK, "二分", anchor="middle")
    )
    # 四分點刻度括線（右側）
    brx = mi((SKIN_R + 4.5, 0))[0]
    ytop, ybot = mi((0, DIPc[1]))[1], mi((0, PIPc[1]))[1]
    s += f"<line x1='{brx:.0f}' y1='{ytop:.0f}' x2='{brx:.0f}' y2='{ybot:.0f}' stroke='{INK}' stroke-width='1.4'/>"
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        yt = ytop + t * (ybot - ytop)
        w = 9 if t in (0, 1.0) else 6
        s += f"<line x1='{brx-w:.0f}' y1='{yt:.0f}' x2='{brx+w:.0f}' y2='{yt:.0f}' stroke='{INK}' stroke-width='1.4'/>"
    s += (
        halo_text(brx + 16, (ytop + ybot) / 2 - 10, 16, INK, "四分點法", weight=700)
        + halo_text(brx + 16, (ytop + ybot) / 2 + 12, 14, INK, "均分四等份取三穴", opacity=.8)
    )
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
        f"<text x='{bx+bw/2}' y='{by+27}' font-size='21' font-weight='700' fill='{VERMILLION}' "
        f"text-anchor='middle' font-family='Noto Serif TC, serif'>指駟馬穴（三穴）</text>"
        f"<text x='{bx+bw/2}' y='{by+50}' font-size='13.5' fill='{INK}' fill-opacity='.8' "
        f"text-anchor='middle' font-family='Noto Sans TC, sans-serif'>食指背第二節．中央線外開二分</text>"
        f"<line x1='{bx+bw/2}' y1='{by+bh}' x2='{ccx-42:.0f}' y2='{ccy-56:.0f}' "
        f"stroke='{INK}' stroke-opacity='.5' stroke-width='1.1'/>"
    )
    return s + "</g>"


def header_legend_attrib():
    s = "<g id='header'>"
    s += (
        f"<rect x='24' y='22' width='62' height='30' fill='{VERMILLION}'/>"
        f"<text x='55' y='43' font-size='16' fill='#F7EDD8' text-anchor='middle' "
        f"font-family='Noto Sans TC, sans-serif'>11.07</text>"
        f"<text x='98' y='45' font-size='26' font-weight='700' fill='{INK}' "
        f"font-family='Noto Serif TC, serif'>指駟馬穴</text>"
        f"<text x='24' y='76' font-size='14' fill='{INK}' fill-opacity='.65' "
        f"font-family='Noto Sans TC, sans-serif'>底圖：WHO 標準經穴定位線稿（手背觀・骨骼透視）｜C 版</text>"
        f"<text x='{ICX}' y='172' font-size='17' font-weight='700' fill='{INK}' text-anchor='middle' "
        f"font-family='Noto Sans TC, sans-serif'>食指背第二節（放大）</text>"
    )
    # 圖例（右下）
    lx, ly = 880, CANVAS_H - 92
    s += (
        f"<rect x='{lx}' y='{ly}' width='22' height='14' fill='#e6e7e8' stroke='#6d6e71' stroke-width='1.2'/>"
        f"<text x='{lx+30}' y='{ly+12}' font-size='14' fill='{INK}' font-family='Noto Sans TC, sans-serif'>骨骼透視</text>"
        f"<circle cx='{lx+11}' cy='{ly+31}' r='6.5' fill='{RED}' stroke='#FFFFFF' stroke-width='2'/>"
        f"<text x='{lx+30}' y='{ly+36}' font-size='14' fill='{INK}' font-family='Noto Sans TC, sans-serif'>穴位點</text>"
        f"<line x1='{lx}' y1='{ly+52}' x2='{lx+22}' y2='{ly+52}' stroke='{GOLD}' stroke-width='1.8' stroke-dasharray='8 5'/>"
        f"<text x='{lx+30}' y='{ly+57}' font-size='14' fill='{INK}' font-family='Noto Sans TC, sans-serif'>中央線</text>"
    )
    # 來源標示（左下）
    s += (
        f"<text x='24' y='{CANVAS_H-18}' font-size='12' fill='{INK}' fill-opacity='.55' "
        f"font-family='Noto Sans TC, sans-serif'>底圖｜WHO Standard Acupuncture Point Locations "
        f"in the Western Pacific Region (2008)　標註｜TungsAcu-DB</text>"
    )
    return s + "</g>"


def build():
    body = base_body()
    hand_clip_rect = (*mp((296.5, 95)), *mp((502, 385.4)))
    x0, y0, x1, y1 = hand_clip_rect
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {CANVAS_W} {CANVAS_H}'
     font-family='Noto Sans TC, sans-serif'>
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
    out.write_text(svg)
    print("產出:", out.name, f"({len(svg)//1024} KB)")


if __name__ == "__main__":
    build()
