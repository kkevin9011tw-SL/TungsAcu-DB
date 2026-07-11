#!/usr/bin/env python3
"""Build the geometry-locked competitor-style layers for WHO bases 01-19."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

HERE = Path(__file__).resolve().parent
ANATOMY = HERE.parents[1]
OUT = HERE / "all"
sys.path.insert(0, str(ANATOMY / "skin-pipeline"))
import pipeline  # noqa: E402


BASES = tuple(pipeline.CFG["bases"])
SKELETON_ONLY = {"18_upper-back-skeleton", "19_lower-back-skeleton"}
SKIN = np.array((246, 211, 184), dtype=np.float64)
OUTLINE_ALPHA = 0.62
BONE_ALPHA = 0.31

# Several WHO plates intentionally leave the skin contour open at the crop edge.
# A row-span fill is unstable on those plates (it can choose an internal bone line
# as one of the borders), so keep a conservative, geometry-locked silhouette for
# the affected views.  Points are normalized to each base image.
CUSTOM_POLYGONS = {
    "03_upper-arm-anterior": [
        (.30, .18), (.37, .16), (.45, .16), (.53, .18), (.52, .30),
        (.51, .45), (.51, .60), (.53, .75), (.54, .90), (.53, 1.00),
        (.21, 1.00), (.22, .94), (.25, .84), (.28, .70), (.29, .55),
        (.30, .40),
    ],
    "05_upper-arm-posterior": [
        (.18, .23), (.28, .20), (.43, .20), (.56, .23), (.65, .32),
        (.68, .45), (.69, .62), (.72, .80), (.72, 1.00), (.43, 1.00),
        (.40, .80), (.38, .60), (.35, .45), (.26, .35),
    ],
    "15_thigh-anterior": [
        (.22, .18), (.34, .16), (.47, .16), (.58, .23), (.66, .36),
        (.70, .53), (.69, .73), (.66, 1.00), (.36, 1.00), (.32, .84),
        (.28, .66), (.24, .46),
    ],
    "16_thigh-posterior": [
        (.55, .16), (.68, .16), (.82, .20), (.90, .29), (.94, .44),
        (.89, .62), (.83, .79), (.80, 1.00), (.55, 1.00), (.55, .80),
        (.58, .58), (.60, .36),
    ],
    "17_shoulder-joint-posterior": [
        (.27, .12), (.40, .12), (.55, .17), (.68, .25), (.79, .40),
        (.84, .57), (.84, .70), (.59, .70), (.57, .53), (.43, .37),
        (.32, .25),
    ],
}


def add_soft_ellipse(image, box, color, blur):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(box, fill=color)
    return Image.alpha_composite(image, layer.filter(ImageFilter.GaussianBlur(blur)))


def point(size, value):
    return round(value[0] * size[0]), round(value[1] * size[1])


def curve(image, values, color, width):
    ImageDraw.Draw(image).line([point(image.size, value) for value in values], fill=color, width=width, joint="curve")


def polygon_mask(size, values):
    mask = Image.new("1", size, 0)
    ImageDraw.Draw(mask).polygon([point(size, value) for value in values], fill=1)
    # Anti-alias the hand-authored closure so the simplified surface keeps a
    # smooth atlas contour instead of visibly angular polygon corners.
    softened = mask.convert("L").filter(ImageFilter.GaussianBlur(7))
    return np.array(softened) > 96


def interior_for(base, source, outline):
    if base in CUSTOM_POLYGONS:
        return polygon_mask(source.size, CUSTOM_POLYGONS[base])
    if base in SKELETON_ONLY or base in {"16_thigh-posterior", "17_shoulder-joint-posterior"}:
        mask = pipeline.span_interior(outline)
        if base == "18_upper-back-skeleton":
            # The WHO crop intentionally cuts the right shoulder at the frame edge.
            # Extend only existing body rows to that edge; do not invent lower rows.
            dark = np.array(outline) < 128
            for row in np.where(dark.any(axis=1))[0]:
                left = int(np.where(dark[row])[0].min())
                mask[row, left:] = True
        return mask
    return pipeline.interior_for(source, outline, pipeline.CFG["bases"][base])[0]


def add_back_bones(image, interior):
    """Restore a restrained posterior torso skeleton layer for WHO plate 10.

    The cleaned WHO raster keeps the skin outline but its gray skeleton pixels
    were removed during source cleanup.  These lines are deliberately low
    contrast and are clipped to the same surface mask as the skin.
    """
    h, w = interior.shape
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    bone = (92, 94, 96, 112)
    bone_light = (110, 111, 112, 82)
    cx = w * 0.50
    top, bottom = h * 0.17, h * 0.92
    draw.line((cx, top, cx, bottom), fill=bone, width=max(3, round(w * .004)))
    vertebra_h = max(12, round(h * .018))
    count = 14
    for i in range(count):
        y = top + (bottom - top) * i / (count - 1)
        half = w * (0.025 if i < 4 else 0.032)
        draw.rounded_rectangle(
            (cx - half, y - vertebra_h, cx + half, y + vertebra_h),
            radius=max(4, round(vertebra_h * .45)), fill=bone_light, outline=bone,
            width=max(2, round(w * .0025)),
        )
    # Posterior rib arcs, kept shorter than the body outline so the layer reads
    # as透視 rather than a second silhouette.
    for i in range(7):
        y = h * (0.27 + i * 0.045)
        rise = h * .10
        span = w * (0.24 - i * .012)
        draw.arc((cx - span, y - rise, cx + span, y + rise), 205, 335, fill=bone_light, width=max(2, round(w * .0025)))
    # Scapulae.
    left = [(cx - w*.07, h*.25), (cx - w*.24, h*.29), (cx - w*.20, h*.43), (cx - w*.08, h*.38), (cx - w*.07, h*.25)]
    right = [(cx + w*.07, h*.25), (cx + w*.24, h*.29), (cx + w*.20, h*.43), (cx + w*.08, h*.38), (cx + w*.07, h*.25)]
    draw.line(left, fill=bone, width=max(2, round(w * .0025)), joint="curve")
    draw.line(right, fill=bone, width=max(2, round(w * .0025)), joint="curve")
    # Clip every stroke to the skin geometry; no lines may leak into the white.
    clipped = np.array(overlay)
    clipped[~interior] = 0
    return Image.alpha_composite(image.convert("RGBA"), Image.fromarray(clipped, "RGBA").convert("RGBA"))


def body_surface(base):
    config = pipeline.CFG["bases"][base]
    source = pipeline.load_base(base)
    outline, bones = pipeline.outline_and_bones(source, config)
    interior = interior_for(base, source, outline)
    height, width = interior.shape
    y, x = np.mgrid[:height, :width]
    rows = np.where(interior.any(axis=1))[0]
    if len(rows) < 2:
        raise RuntimeError(f"{base}: 無法從 WHO 外輪廓建立表面遮罩")
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

    if "hand" in base:
        base_color = np.array((247, 211, 183), dtype=np.float64)
        edge_strength, highlight = 13, 15
    elif "head" in base:
        base_color = np.array((239, 193, 158), dtype=np.float64)
        edge_strength, highlight = 12, 12
    elif "foot" in base:
        base_color = np.array((243, 202, 169), dtype=np.float64)
        edge_strength, highlight = 14, 15
    elif "torso" in base or base in {"09_chest-abdomen", "10_back", *SKELETON_ONLY}:
        base_color = np.array((239, 191, 153), dtype=np.float64)
        edge_strength, highlight = 16, 14
    else:
        base_color = SKIN
        edge_strength, highlight = 16, 16

    shade = -edge_strength * np.abs(u) ** 1.7
    shade += highlight * np.exp(-((u - 0.06) / 0.34) ** 2)
    shade -= 6 * np.exp(-((u + 0.58) / 0.28) ** 2)
    shade += 4 * np.exp(-((v - 0.12) / 0.10) ** 2)
    if base == "14_lower-leg-posterior":
        shade += 10 * np.exp(-((u + 0.22) / 0.23) ** 2 - ((v - 0.45) / 0.25) ** 2)
        shade += 9 * np.exp(-((u - 0.20) / 0.23) ** 2 - ((v - 0.44) / 0.25) ** 2)
    elif base == "13_lower-leg-anterior":
        shade += 8 * np.exp(-((u - 0.20) / 0.19) ** 2 - ((v - 0.50) / 0.34) ** 2)
    elif base in SKELETON_ONLY:
        shade += 6 * np.exp(-((u - 0.05) / 0.52) ** 2)

    pixels = np.full((height, width, 3), 255.0)
    tint = np.array((1.0, -0.15, -0.55))
    pixels[interior] = np.clip(base_color + shade[interior, None] * tint, 0, 255)
    surface = Image.fromarray(pixels.astype(np.uint8)).convert("RGBA")

    if base == "13_lower-leg-anterior":
        surface = add_soft_ellipse(surface, (width * .39, height * .25, width * .62, height * .77), (255, 236, 218, 44), 34)
        curve(surface, [(.51, .23), (.54, .43), (.55, .65), (.55, .82)], (166, 112, 81, 80), 3)
        curve(surface, [(.41, .87), (.50, .89), (.60, .88)], (173, 117, 84, 56), 2)
    elif base == "14_lower-leg-posterior":
        surface = add_soft_ellipse(surface, (width * .28, height * .25, width * .51, height * .62), (255, 235, 216, 45), 30)
        surface = add_soft_ellipse(surface, (width * .49, height * .25, width * .74, height * .62), (255, 235, 216, 42), 30)
        curve(surface, [(.42, .29), (.38, .46), (.42, .61), (.48, .72)], (168, 112, 80, 55), 2)
        curve(surface, [(.62, .29), (.67, .45), (.62, .61), (.53, .76)], (168, 112, 80, 55), 2)
        curve(surface, [(.51, .63), (.51, .79), (.50, .91)], (151, 101, 74, 72), 3)

    clipped = np.array(surface.convert("RGB"))
    clipped[~interior] = 255
    surface = Image.fromarray(clipped).convert("RGBA")
    outline_for_render = outline
    if base in CUSTOM_POLYGONS:
        # The source plate has open crop-edge contour strokes outside the
        # hand-closed surface.  Do not let those orphan lines survive as
        # apparent skin leaks in the simplified surface layer.
        outline_arr = np.array(outline_for_render)
        outline_arr[~interior] = 255
        outline_for_render = Image.fromarray(outline_arr.astype("uint8"))
    soft_outline = outline_for_render.point(lambda value: int(255 - (255 - value) * OUTLINE_ALPHA) if value < 128 else 255).convert("RGB")
    surface = ImageChops.multiply(surface.convert("RGB"), soft_outline).convert("RGBA")
    bone_arr = np.array(bones)
    if base in CUSTOM_POLYGONS:
        bone_arr[~interior] = 255
    faint_bones = Image.fromarray(bone_arr.astype("uint8")).point(lambda value: int(255 - (255 - value) * BONE_ALPHA)).convert("RGB")
    anatomy = ImageChops.multiply(surface.convert("RGB"), faint_bones)
    if base == "10_back":
        anatomy = add_back_bones(anatomy, interior)
    return surface.convert("RGB"), anatomy.convert("RGB"), int(interior.sum())


def contact_sheet(files, output, title):
    columns, tile_w, image_h, label_h = 5, 270, 320, 28
    rows = (len(files) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_w, rows * (image_h + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(files):
        image = ImageOps.contain(Image.open(path).convert("RGB"), (tile_w - 18, image_h - 12), Image.Resampling.LANCZOS)
        x = (index % columns) * tile_w + (tile_w - image.width) // 2
        y = (index // columns) * (image_h + label_h) + 5
        sheet.paste(image, (x, y))
        draw.text(((index % columns) * tile_w + 6, y + image_h), path.stem.replace("_表面圖", "").replace("_骨骼透視圖", ""), fill=(55, 43, 35))
    sheet.save(output)
    print(f"wrote {title}: {output}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    surface_files, anatomy_files = [], []
    for base in BASES:
        surface, anatomy, area = body_surface(base)
        surface_path = OUT / f"{base}_表面圖.png"
        anatomy_path = OUT / f"{base}_骨骼透視圖.png"
        surface.save(surface_path)
        anatomy.save(anatomy_path)
        surface_files.append(surface_path)
        anatomy_files.append(anatomy_path)
        print(f"{base}: surface={surface_path} anatomy={anatomy_path} interior_px={area}")
    contact_sheet(surface_files, OUT / "01-19_表面圖總覽.png", "surface overview")
    contact_sheet(anatomy_files, OUT / "01-19_骨骼透視圖總覽.png", "anatomy overview")


if __name__ == "__main__":
    main()
