#!/usr/bin/env python3
"""把 marker JSON 的紅點疊到套皮後的底圖上，驗證「點不飄」。

用法:
    python3 overlay_points.py <marked.json> <skin_image.png> <output.png>

座標換算:
    marker JSON 的座標是底圖 SVG viewBox 單位。
    clean-bases 的 PNG 以 scale=6 輸出(viewBox 170x240 -> 1020x1440)。
    只要套皮圖與 clean-bases PNG 同尺寸,像素座標 = (座標 - viewBox 原點) * 6。
"""
import json
import sys
from PIL import Image, ImageDraw

# clean-bases 各底圖的 viewBox 原點與輸出 scale
BASE_GEOMETRY = {
    "01_hand-palmar.svg": {"origin": (322, 112), "scale": 6},
    "02_hand-dorsal.svg": {"origin": (322, 112), "scale": 6},
    "14_lower-leg-posterior.svg": {"origin": (337, 107), "scale": 6},
}


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    marked_json, skin_png, out_png = sys.argv[1:4]

    with open(marked_json) as f:
        data = json.load(f)

    base_file = data["base_file"]
    geo = BASE_GEOMETRY.get(base_file)
    if geo is None:
        sys.exit(f"未登錄的底圖: {base_file},請把它的 viewBox 原點加進 BASE_GEOMETRY")
    ox, oy = geo["origin"]
    s = geo["scale"]

    img = Image.open(skin_png).convert("RGB")
    draw = ImageDraw.Draw(img)

    n = 0
    for ann in data["annotations"]:
        if ann["type"] != "point":
            continue
        x, y = ann["xy"]
        px, py = (x - ox) * s, (y - oy) * s
        r = ann.get("r", 8) * s * 0.15  # 紅點半徑(2026-07-03 顥軒定案 0.15)
        draw.ellipse([px - r - 3, py - r - 3, px + r + 3, py + r + 3], fill="white")
        draw.ellipse([px - r, py - r, px + r, py + r], fill=(196, 30, 30))
        n += 1

    img.save(out_png)
    print(f"疊了 {n} 個點 -> {out_png} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
