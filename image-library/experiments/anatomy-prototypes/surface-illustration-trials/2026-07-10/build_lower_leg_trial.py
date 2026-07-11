#!/usr/bin/env python3
"""Build deterministic lower-leg surface and anatomy-overlay comparison images."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


HERE = Path(__file__).resolve().parent
ANATOMY = HERE.parents[1]
sys.path.insert(0, str(ANATOMY / "skin-pipeline"))
import pipeline  # noqa: E402


BASES = ("13_lower-leg-anterior", "14_lower-leg-posterior")
SKIN = np.array((246, 211, 184), dtype=np.float64)
OUTLINE_ALPHA = 0.62
BONE_ALPHA = 0.31


def add_soft_ellipse(image, box, color, blur):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(box, fill=color)
    return Image.alpha_composite(image, layer.filter(ImageFilter.GaussianBlur(blur)))


def px(size, point):
    width, height = size
    return round(point[0] * width), round(point[1] * height)


def draw_curve(image, points, color, width):
    draw = ImageDraw.Draw(image)
    draw.line([px(image.size, point) for point in points], fill=color, width=width, joint="curve")


def skin_base(base):
    config = pipeline.CFG["bases"][base]
    source = pipeline.load_base(base)
    outline, bones = pipeline.outline_and_bones(source, config)
    interior, _ = pipeline.interior_for(source, outline, config)
    height, width = interior.shape
    y, x = np.mgrid[:height, :width]

    rows = np.where(interior.any(axis=1))[0]
    centers = np.zeros(height)
    halves = np.ones(height)
    for row in rows:
        xs = np.where(interior[row])[0]
        centers[row] = (xs.min() + xs.max()) / 2
        halves[row] = max((xs.max() - xs.min()) / 2, 1)
    centers = np.interp(np.arange(height), rows, centers[rows])
    halves = np.interp(np.arange(height), rows, halves[rows])
    u = (x - centers[:, None]) / halves[:, None]
    v = y / max(height - 1, 1)

    shade = -16 * np.abs(u) ** 1.7
    shade += 16 * np.exp(-((u - 0.08) / 0.30) ** 2)
    shade -= 7 * np.exp(-((u + 0.58) / 0.25) ** 2)
    shade += 4 * np.exp(-((v - 0.15) / 0.10) ** 2)
    if base.endswith("anterior"):
        shade += 9 * np.exp(-((u - 0.22) / 0.17) ** 2 - ((v - 0.52) / 0.34) ** 2)
        shade -= 6 * np.exp(-((u + 0.26) / 0.20) ** 2 - ((v - 0.54) / 0.33) ** 2)
    else:
        shade += 12 * np.exp(-((u + 0.23) / 0.22) ** 2 - ((v - 0.45) / 0.23) ** 2)
        shade += 10 * np.exp(-((u - 0.20) / 0.21) ** 2 - ((v - 0.43) / 0.24) ** 2)
        shade -= 8 * np.exp(-((u - 0.02) / 0.12) ** 2 - ((v - 0.64) / 0.24) ** 2)

    pixels = np.full((height, width, 3), 255.0)
    tint = np.array((1.0, -0.15, -0.55))
    pixels[interior] = np.clip(SKIN + shade[interior, None] * tint, 0, 255)
    surface = Image.fromarray(pixels.astype(np.uint8)).convert("RGBA")

    # Deliberately restrained surface landmarks, separate from the skeleton layer.
    if base.endswith("anterior"):
        surface = add_soft_ellipse(surface, (width * 0.39, height * 0.25, width * 0.62, height * 0.77), (255, 236, 218, 44), 34)
        draw_curve(surface, [(0.51, 0.23), (0.54, 0.43), (0.55, 0.65), (0.55, 0.82)], (166, 112, 81, 80), 3)
        draw_curve(surface, [(0.41, 0.87), (0.50, 0.89), (0.60, 0.88)], (173, 117, 84, 56), 2)
    else:
        surface = add_soft_ellipse(surface, (width * 0.28, height * 0.25, width * 0.51, height * 0.62), (255, 235, 216, 45), 30)
        surface = add_soft_ellipse(surface, (width * 0.49, height * 0.25, width * 0.74, height * 0.62), (255, 235, 216, 42), 30)
        draw_curve(surface, [(0.42, 0.29), (0.38, 0.46), (0.42, 0.61), (0.48, 0.72)], (168, 112, 80, 55), 2)
        draw_curve(surface, [(0.62, 0.29), (0.67, 0.45), (0.62, 0.61), (0.53, 0.76)], (168, 112, 80, 55), 2)
        draw_curve(surface, [(0.51, 0.63), (0.51, 0.79), (0.50, 0.91)], (151, 101, 74, 72), 3)

    # Blur and curve strokes are decorative surface detail: never let them escape the WHO silhouette.
    clipped = np.array(surface.convert("RGB"))
    clipped[~interior] = 255
    surface = Image.fromarray(clipped).convert("RGBA")
    soft_outline = outline.point(
        lambda value: int(255 - (255 - value) * OUTLINE_ALPHA) if value < 128 else 255
    ).convert("RGB")
    surface = ImageChops.multiply(surface.convert("RGB"), soft_outline).convert("RGBA")
    faint_bones = bones.point(lambda value: int(255 - (255 - value) * BONE_ALPHA)).convert("RGB")
    anatomy = ImageChops.multiply(surface.convert("RGB"), faint_bones)
    return surface.convert("RGB"), anatomy.convert("RGB")


def build_contact_sheet(images):
    tile_w, image_h, label_h, columns = 360, 520, 34, 2
    sheet = Image.new("RGB", (tile_w * columns, (image_h + label_h) * 2), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (label, image) in enumerate(images):
        thumb = ImageOps.contain(image, (tile_w - 24, image_h - 16), Image.Resampling.LANCZOS)
        x = (index % columns) * tile_w + (tile_w - thumb.width) // 2
        y = (index // columns) * (image_h + label_h) + 8
        sheet.paste(thumb, (x, y))
        draw.text(((index % columns) * tile_w + 10, y + image_h), label, fill=(58, 46, 38))
    return sheet


def main():
    review = []
    for base in BASES:
        surface, anatomy = skin_base(base)
        surface_path = HERE / f"{base}_表面圖.png"
        anatomy_path = HERE / f"{base}_骨骼透視圖.png"
        surface.save(surface_path)
        anatomy.save(anatomy_path)
        review.extend(((f"{base} | surface", surface), (f"{base} | anatomy", anatomy)))
        print(f"wrote {surface_path}")
        print(f"wrote {anatomy_path}")
    contact = HERE / "小腿_競品式表面與骨骼透視比較.png"
    build_contact_sheet(review).save(contact)
    print(f"wrote {contact}")


if __name__ == "__main__":
    main()
