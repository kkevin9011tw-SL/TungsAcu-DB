#!/usr/bin/env python3
"""從 WHO 標準經穴定位書抽出乾淨的手背線稿底圖（向量）。

來源：WHO Standard Acupuncture Point Locations in the Western Pacific Region (2008)
      https://iris.who.int/handle/10665/353407
      PDF bitstream: https://iris.who.int/server/api/core/bitstreams/d98c1c98-3fbf-4e4e-8c9a-1bbe72ccd00e/content
版權：© WHO 2008，傳統版權（非 CC）。內部評估用；公開上線前需向 WHO 西太平洋辦公室申請重製授權。

流程：p.168（TE3 圖，手背＋全骨架）→ SVG 匯出 → 刪文字/紅灰標記/引導線 → 裁圖框 → 轉 180°（指尖朝上）。
產出 who_hand_dorsum_clean.svg：右手背線稿，viewBox 296 94.5 206.4 290.9（PDF pt 座標）。
"""
import re
from pathlib import Path

import fitz

HERE = Path(__file__).parent

doc = fitz.open(HERE / "who_acupoints.pdf")
svg = doc[167].get_svg_image()

m = re.match(r"(.*?<defs>.*?</defs>)(.*)(</svg>)", svg, re.S)
head, body, tail = m.groups()

body = re.sub(r"<use[^>]*/>", "", body)                          # 文字 glyph
body = re.sub(r'<path[^>]*fill="#ed1d24"[^>]*/>', "", body)      # 紅色點與標籤底
body = re.sub(r'<path[^>]*fill="#808285"[^>]*/>', "", body)      # 灰色點與灰字


def filt(mt):
    tag = mt.group(0)
    dm = re.search(r'd="([^"]+)"', tag)
    d = dm.group(1) if dm else ""
    if 'fill="#ffffff"' in tag and "H" in d:
        return ""           # 軸對齊白色遮罩矩形（H/V 指令）
    if 'stroke="#ffffff"' in tag:
        nums = [float(v) for v in re.findall(r"-?[\d.]+", d)]
        if nums and max(nums) - min(nums) < 15:
            return ""       # 小字（5th/4th）的白色描邊光暈
        return tag
    if "stroke" not in tag:
        return tag          # 純填色（骨骼、指甲）保留
    if any(c in d for c in "CQA"):
        return tag          # 含曲線 = 輪廓，保留
    coords = re.findall(r"[\d.]+ [\d.]+", d)
    return "" if len(coords) <= 3 else tag   # 短直線 = 引導線，刪


body = re.sub(r"<path[^>]*/>", filt, body)

x0, y0, x1, y1 = 296.0, 94.5, 502.4, 385.4
cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
w, h = x1 - x0, y1 - y0
head = re.sub(
    r'width="\d+" height="\d+" viewBox="[^"]+"',
    f'width="{w:.0f}" height="{h:.0f}" viewBox="{x0} {y0} {w:.1f} {h:.1f}"',
    head,
)
body = f'<g transform="rotate(180 {cx:.2f} {cy:.2f})">' + body + "</g>"

(HERE / "who_hand_dorsum_clean.svg").write_text(head + body + tail)
print("產出: who_hand_dorsum_clean.svg")
