#!/usr/bin/env python3
"""指駟馬穴 PoC 產圖：
A 版 = 向量插畫（描自書圖輪廓）+ 骨骼/肌腱示意 + 標註
B 版 = 書圖增強照片底 + 骨骼/肌腱示意 + 標註
兩版共用同一套幾何錨點（由 detect 程式量測自原圖）。
"""
import base64
import json
from pathlib import Path

HERE = Path(__file__).parent

# ── 幾何錨點（原圖 791×1044 座標系，程式偵測）──
DIP = {"y": 208, "x0": 488, "x1": 588}     # 遠端指節橫紋（上）
PIP = {"y": 349, "x0": 473, "x1": 585}     # 近端指節橫紋（下）
CL_TOP = (536.5, 200)                       # 中央線上端
CL_BOT = (527.0, 355)                       # 中央線下端
SLOPE = (CL_BOT[0] - CL_TOP[0]) / (CL_BOT[1] - CL_TOP[1])  # dx/dy ≈ -0.061
ULNAR_OFFSET = -20                          # 外開二分（向尺側 = 圖中左側）

def cl_x(y):
    return CL_TOP[0] + SLOPE * (y - CL_TOP[1])

def ann_pt(t):
    """標註線上的點，t=0 在 DIP、t=1 在 PIP"""
    y = DIP["y"] + t * (PIP["y"] - DIP["y"])
    return (cl_x(y) + ULNAR_OFFSET, y)

POINTS = [ann_pt(0.25), ann_pt(0.5), ann_pt(0.75)]

# ── 畫布配置 ──
CANVAS_W, CANVAS_H = 1120, 1100
IMG_W, IMG_H = 791, 1044
OX, OY = 300, 28                            # 照片群組位移

INK = "#2C1C10"
GOLD = "#C4933A"
VERMILLION = "#7B2D1E"
RED = "#B3261E"
BONE_FILL = "#F2EBD8"
BONE_STROKE = "#B9A37E"
TENDON = "#C25B5B"
HALO = "#FBF6EA"


def halo_text(x, y, size, fill, text, anchor="start", weight=None, opacity=1):
    """文字加淡色描邊光暈，疊在照片上仍可讀。畫兩次：先粗描邊再實字。"""
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


def bone_path(y0, y1, w_end, w_mid):
    """簡化指骨：兩端膨大（骨骺）、骨幹明顯收窄的長骨形。沿中央線傾斜。

    側緣用兩段三次曲線強制通過腰部最窄點，避免畫成直條。"""
    cx0, cx1 = cl_x(y0), cl_x(y1)
    ym = (y0 + y1) / 2
    cxm = cl_x(ym)
    he = w_end / 2
    he1 = he * 1.12                 # 近端（下端）骨骺略寬
    hm = w_mid / 2
    cap = min(16, (y1 - y0) * 0.18)
    dh = (y1 - y0) * 0.22
    return (
        f"M {cx0-he:.1f},{y0+cap:.1f} "
        f"Q {cx0-he:.1f},{y0:.1f} {cx0-he*0.5:.1f},{y0:.1f} "
        f"L {cx0+he*0.5:.1f},{y0:.1f} "
        f"Q {cx0+he:.1f},{y0:.1f} {cx0+he:.1f},{y0+cap:.1f} "
        f"C {cx0+he:.1f},{y0+cap+dh:.1f} {cxm+hm:.1f},{ym-dh:.1f} {cxm+hm:.1f},{ym:.1f} "
        f"C {cxm+hm:.1f},{ym+dh:.1f} {cx1+he1:.1f},{y1-cap-dh:.1f} {cx1+he1:.1f},{y1-cap:.1f} "
        f"Q {cx1+he1:.1f},{y1:.1f} {cx1+he1*0.5:.1f},{y1:.1f} "
        f"L {cx1-he1*0.5:.1f},{y1:.1f} "
        f"Q {cx1-he1:.1f},{y1:.1f} {cx1-he1:.1f},{y1-cap:.1f} "
        f"C {cx1-he1:.1f},{y1-cap-dh:.1f} {cxm-hm:.1f},{ym+dh:.1f} {cxm-hm:.1f},{ym:.1f} "
        f"C {cxm-hm:.1f},{ym-dh:.1f} {cx0-he:.1f},{y0+cap+dh:.1f} {cx0-he:.1f},{y0+cap:.1f} Z"
    )


def anatomy_layer():
    """骨骼 + 伸指肌腱示意（食指）"""
    bones = [
        bone_path(96, 196, 34, 17),    # 遠節指骨
        bone_path(218, 340, 42, 21),   # 中節指骨（指駟馬所在）
        bone_path(360, 505, 50, 25),   # 近節指骨
    ]
    bone_svg = "".join(
        f"<path d='{p}' fill='{BONE_FILL}' fill-opacity='.62' "
        f"stroke='{BONE_STROKE}' stroke-opacity='.85' stroke-width='1.6'/>"
        for p in bones
    )
    # 關節間隙提示（細橫弧）
    joints = ""
    for yj in (207, 350):
        xj = cl_x(yj)
        joints += (
            f"<path d='M {xj-16:.1f},{yj:.1f} Q {xj:.1f},{yj+5:.1f} {xj+16:.1f},{yj:.1f}' "
            f"fill='none' stroke='{BONE_STROKE}' stroke-opacity='.7' stroke-width='1.3'/>"
        )
    # 伸指肌腱：沿中央線的半透明帶，PIP 處分中央束與側束
    t_top, t_bot = 100, 520
    band = (
        f"M {cl_x(t_top)-6.5:.1f},{t_top} "
        f"L {cl_x(t_bot)-7.5:.1f},{t_bot} L {cl_x(t_bot)+7.5:.1f},{t_bot} "
        f"L {cl_x(t_top)+6.5:.1f},{t_top} Z"
    )
    lateral = ""
    for sgn in (-1, 1):
        x_pip = cl_x(345)
        lateral += (
            f"<path d='M {x_pip+sgn*7:.1f},345 Q {x_pip+sgn*15:.1f},300 {cl_x(245)+sgn*9:.1f},245 "
            f"L {cl_x(215)+sgn*5:.1f},215' fill='none' "
            f"stroke='{TENDON}' stroke-opacity='.42' stroke-width='4.5' stroke-linecap='round'/>"
        )
    tendon_svg = (
        f"<path d='{band}' fill='{TENDON}' fill-opacity='.32' "
        f"stroke='{TENDON}' stroke-opacity='.5' stroke-width='1'/>"
        + lateral
    )
    return f"<g id='anatomy'>{bone_svg}{joints}{tendon_svg}</g>"


def annotation_layer():
    """摺線、中央線、標註線、四分點、紅點"""
    s = "<g id='annotation'>"
    # 指節橫紋（沿偵測到的紅鋸齒位置畫細虛線）
    for cr, label in ((DIP, "遠端指節橫紋"), (PIP, "近端指節橫紋")):
        s += (
            f"<line x1='{cr['x0']}' y1='{cr['y']}' x2='{cr['x1']}' y2='{cr['y']}' "
            f"stroke='{INK}' stroke-opacity='.65' stroke-width='1.6' stroke-dasharray='5 3'/>"
            + halo_text(cr["x1"] + 10, cr["y"] + 4, 15, INK, label, opacity=.85)
        )
    # 中央線
    s += (
        f"<line x1='{cl_x(178):.1f}' y1='178' x2='{cl_x(382):.1f}' y2='382' "
        f"stroke='{GOLD}' stroke-width='1.4' stroke-dasharray='7 4' stroke-opacity='.9'/>"
        + halo_text(cl_x(178) + 6, 170, 15, "#8A6420", "中央線", weight=700)
    )
    # 標註線（中央線外開二分，尺側）
    p0, p1 = ann_pt(0.0), ann_pt(1.0)
    s += (
        f"<line x1='{p0[0]:.1f}' y1='{p0[1]:.1f}' x2='{p1[0]:.1f}' y2='{p1[1]:.1f}' "
        f"stroke='{RED}' stroke-width='1.2' stroke-opacity='.55'/>"
    )
    # 外開二分 尺寸標註（DIP 橫紋上方拉小雙箭頭）
    yd = DIP["y"] - 13
    xa, xb = cl_x(yd), cl_x(yd) + ULNAR_OFFSET
    s += (
        f"<line x1='{xa:.1f}' y1='{yd}' x2='{xb:.1f}' y2='{yd}' stroke='{INK}' stroke-width='1.2'/>"
        f"<line x1='{xa:.1f}' y1='{yd-4}' x2='{xa:.1f}' y2='{yd+4}' stroke='{INK}' stroke-width='1.2'/>"
        f"<line x1='{xb:.1f}' y1='{yd-4}' x2='{xb:.1f}' y2='{yd+4}' stroke='{INK}' stroke-width='1.2'/>"
        + halo_text((xa + xb) / 2, yd - 8, 14, INK, "二分", anchor="middle")
    )
    # 四分點刻度（右側括線）
    bx = PIP["x1"] + 26
    s += (
        f"<line x1='{bx}' y1='{DIP['y']}' x2='{bx}' y2='{PIP['y']}' stroke='{INK}' stroke-width='1.2'/>"
    )
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        yt = DIP["y"] + t * (PIP["y"] - DIP["y"])
        w = 8 if t in (0, 1.0) else 5
        s += f"<line x1='{bx-w}' y1='{yt:.1f}' x2='{bx+w}' y2='{yt:.1f}' stroke='{INK}' stroke-width='1.2'/>"
    s += (
        halo_text(bx + 14, (DIP["y"] + PIP["y"]) / 2 - 10, 15, INK, "四分點法", weight=700)
        + halo_text(bx + 14, (DIP["y"] + PIP["y"]) / 2 + 10, 13, INK, "均分四等份取三穴", opacity=.8)
    )
    # 穴位紅點
    for x, y in POINTS:
        s += (
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='7' fill='{RED}' "
            f"stroke='#FFF8E8' stroke-width='2.2'/>"
        )
    return s + "</g>"


def label_layer():
    """左側穴名框 + 引導線（畫布座標）"""
    bx, by, bw, bh = 36, 236, 196, 64
    s = "<g id='labels'>"
    s += (
        f"<rect x='{bx}' y='{by}' width='{bw}' height='{bh}' rx='6' fill='#FFFDF6' "
        f"stroke='{GOLD}' stroke-width='1.6'/>"
        f"<text x='{bx+bw/2}' y='{by+27}' font-size='21' font-weight='700' fill='{VERMILLION}' "
        f"text-anchor='middle' font-family='Noto Serif TC, serif'>指駟馬穴（三穴）</text>"
        f"<text x='{bx+bw/2}' y='{by+50}' font-size='13.5' fill='{INK}' fill-opacity='.8' "
        f"text-anchor='middle' font-family='Noto Sans TC, sans-serif'>食指背第二節．中央線外開二分</text>"
    )
    # 引導線（錨點沿框右緣分散，對應三個穴位點，水平段＋斜段折線）
    anchors_y = (by + 12, by + bh / 2, by + bh - 12)
    for (x, y), ay in zip(POINTS, anchors_y):
        tx, ty = x + OX - 9, y + OY
        mx = bx + bw + 40
        s += (
            f"<path d='M {bx+bw},{ay:.1f} L {mx},{ay:.1f} L {tx:.1f},{ty:.1f}' "
            f"fill='none' stroke='{INK}' stroke-opacity='.55' stroke-width='1.1'/>"
        )
    return s + "</g>"


def header_and_legend(subtitle):
    s = "<g id='header'>"
    s += (
        f"<rect x='24' y='22' width='62' height='30' fill='{VERMILLION}'/>"
        f"<text x='55' y='43' font-size='16' fill='#F7EDD8' text-anchor='middle' "
        f"font-family='Noto Sans TC, sans-serif'>11.07</text>"
        f"<text x='98' y='45' font-size='26' font-weight='700' fill='{INK}' "
        f"font-family='Noto Serif TC, serif'>指駟馬穴</text>"
        f"<text x='24' y='76' font-size='14' fill='{INK}' fill-opacity='.65' "
        f"font-family='Noto Sans TC, sans-serif'>{subtitle}</text>"
    )
    # 圖例
    ly = CANVAS_H - 96
    s += (
        f"<rect x='28' y='{ly}' width='22' height='14' fill='{BONE_FILL}' fill-opacity='.62' "
        f"stroke='{BONE_STROKE}' stroke-width='1.4'/>"
        f"<text x='58' y='{ly+12}' font-size='14' fill='{INK}' font-family='Noto Sans TC, sans-serif'>骨骼示意</text>"
        f"<rect x='28' y='{ly+24}' width='22' height='14' fill='{TENDON}' fill-opacity='.32'/>"
        f"<text x='58' y='{ly+36}' font-size='14' fill='{INK}' font-family='Noto Sans TC, sans-serif'>伸指肌腱示意</text>"
        f"<circle cx='39' cy='{ly+55}' r='6.5' fill='{RED}' stroke='#FFF8E8' stroke-width='2'/>"
        f"<text x='58' y='{ly+60}' font-size='14' fill='{INK}' font-family='Noto Sans TC, sans-serif'>穴位點</text>"
    )
    return s + "</g>"


def build(version):
    if version == "B":
        b64 = base64.b64encode((HERE / "base_enhanced_2x.jpg").read_bytes()).decode()
        base = (
            f"<image href='data:image/jpeg;base64,{b64}' x='0' y='0' "
            f"width='{IMG_W}' height='{IMG_H}'/>"
        )
        subtitle = "底圖：原書圖增強（去噪．銳化）｜骨骼與肌腱為示意疊層"
        out = "指駟馬_B版_書圖增強.svg"
    else:
        path = (HERE / "hand_path.txt").read_text()
        base = (
            f"<path d='{path}' fill='#F2C9A6' stroke='#D29B74' stroke-width='2.5'/>"
        )
        # 指甲：五指尖（由原圖目測，沿指向旋轉）
        nails = [
            (62, 305, 30, 22, -38),     # 小指
            (198, 132, 34, 25, -18),    # 無名指
            (352, 56, 36, 26, -5),      # 中指
            (533, 92, 35, 25, 6),       # 食指
            (706, 492, 36, 27, 55),     # 拇指
        ]
        for cx, cy, w, h, rot in nails:
            base += (
                f"<ellipse cx='{cx}' cy='{cy}' rx='{w/2}' ry='{h/2}' "
                f"transform='rotate({rot} {cx} {cy})' fill='#F8E2CE' "
                f"stroke='#D8A87F' stroke-width='1.6'/>"
            )
        # 指節摺痕提示（僅食指 DIP/PIP，其餘位置不可靠不畫）
        creases = [
            (cl_x(DIP["y"]), DIP["y"], 30), (cl_x(PIP["y"]), PIP["y"], 36),
        ]
        for cx, cy, w in creases:
            base += (
                f"<path d='M {cx-w/2:.0f},{cy:.0f} Q {cx:.0f},{cy+6:.0f} {cx+w/2:.0f},{cy:.0f}' "
                f"fill='none' stroke='#D29B74' stroke-width='1.8' stroke-opacity='.75'/>"
            )
        subtitle = "底圖：向量插畫（描自原書圖輪廓）｜骨骼與肌腱為示意疊層"
        out = "指駟馬_A版_向量插畫.svg"

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {CANVAS_W} {CANVAS_H}'
     font-family='Noto Sans TC, sans-serif'>
  <rect width='{CANVAS_W}' height='{CANVAS_H}' fill='#FBF6EA'/>
  <g transform='translate({OX},{OY})'>
    {base}
    {anatomy_layer()}
    {annotation_layer()}
  </g>
  {label_layer()}
  {header_and_legend(subtitle)}
</svg>"""
    (HERE / out).write_text(svg)
    print("產出:", out, f"({len(svg)//1024} KB)")


if __name__ == "__main__":
    build("B")
    build("A")
