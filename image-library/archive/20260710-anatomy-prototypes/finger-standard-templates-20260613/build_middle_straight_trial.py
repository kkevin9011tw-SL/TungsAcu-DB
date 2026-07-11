#!/usr/bin/env python3
"""Build the final straight-axis trial for the middle-finger inset."""

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


HERE = Path(__file__).parent
SOURCE = HERE / "who_p168_dorsal_bones_only.png"
OUTPUT = HERE / "中指單指直軸_最後評估版.png"

SOURCE_X = 322.0
SOURCE_Y = 112.0
SOURCE_W = 170.0
SOURCE_H = 240.0

# One interior point for each WHO middle-finger phalanx.
SEEDS = (
    (420.0, 140.0),
    (414.0, 162.0),
    (407.0, 195.0),
)

PAPER = (250, 247, 239)
INK = (44, 28, 16)
MUTED = (117, 105, 95)
GOLD = (196, 147, 58)


def font(size: int, bold: bool = False):
    path = Path("/System/Library/Fonts/STHeiti Medium.ttc")
    if path.exists():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def source_pixel(point, size):
    return (
        round((point[0] - SOURCE_X) / SOURCE_W * size[0]),
        round((point[1] - SOURCE_Y) / SOURCE_H * size[1]),
    )


def component(mask, seed):
    height, width = mask.shape
    seed_y, seed_x = seed
    queue = deque([(seed_y, seed_x)])
    selected = {(seed_y, seed_x)}
    while queue:
        y, x = queue.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            point = y + dy, x + dx
            if (
                0 <= point[0] < height
                and 0 <= point[1] < width
                and mask[point]
                and point not in selected
            ):
                selected.add(point)
                queue.append(point)
    return selected


def extract_phalanges():
    source = Image.open(SOURCE).convert("RGB")
    pixels = np.asarray(source)
    fill_mask = (
        (pixels[:, :, 0] > 218)
        & (pixels[:, :, 0] < 240)
        & (pixels[:, :, 1] > 218)
        & (pixels[:, :, 1] < 242)
        & (pixels[:, :, 2] > 220)
        & (pixels[:, :, 2] < 244)
    )
    pieces = []
    for seed in SEEDS:
        pixel_x, pixel_y = source_pixel(seed, source.size)
        selected = component(fill_mask, (pixel_y, pixel_x))
        points = np.array([(y, x) for y, x in selected])

        # PCA gives the original long axis of this individual phalanx.
        xy = points[:, ::-1].astype(float)
        centred = xy - xy.mean(axis=0)
        covariance = np.cov(centred, rowvar=False)
        values, vectors = np.linalg.eigh(covariance)
        axis = vectors[:, np.argmax(values)]
        angle = np.degrees(np.arctan2(axis[1], axis[0]))
        rotation = angle - 90.0
        if rotation > 90:
            rotation -= 180
        if rotation < -90:
            rotation += 180

        selection = np.zeros(fill_mask.shape, dtype=np.uint8)
        selection[points[:, 0], points[:, 1]] = 255
        # Recover the WHO grey outline around the selected fill.
        expanded = Image.fromarray(selection).filter(
            ImageFilter.MaxFilter(9)
        )
        transparent = Image.new("RGBA", source.size, (255, 255, 255, 0))
        rgba = source.convert("RGBA")
        transparent.paste(rgba, mask=expanded)
        bbox = expanded.getbbox()
        piece = transparent.crop(bbox)
        piece = piece.rotate(
            rotation,
            resample=Image.Resampling.BICUBIC,
            expand=True,
            fillcolor=(255, 255, 255, 0),
        )
        alpha_bbox = piece.getchannel("A").getbbox()
        pieces.append(piece.crop(alpha_bbox))
    return pieces


def standard_finger(pieces, dorsal):
    canvas = Image.new("RGBA", (420, 850), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    centre = canvas.width // 2
    top = 72
    target_scale = 1.22
    resized = []
    for piece in pieces:
        resized.append(
            piece.resize(
                (
                    round(piece.width * target_scale),
                    round(piece.height * target_scale),
                ),
                Image.Resampling.LANCZOS,
            )
        )

    gap = 16
    y_positions = [top]
    y_positions.append(y_positions[-1] + resized[0].height + gap)
    y_positions.append(y_positions[-1] + resized[1].height + gap)
    bottom = y_positions[-1] + resized[2].height

    dip_y = y_positions[1] - gap // 2
    pip_y = y_positions[2] - gap // 2
    distal_half = max(68, resized[0].width // 2 + 16)
    proximal_half = max(82, resized[2].width // 2 + 16)
    arc_box = (
        centre - distal_half,
        top - 8,
        centre + distal_half,
        top + distal_half * 2 - 8,
    )
    draw.arc(arc_box, 180, 360, fill=INK, width=4)
    side_start_y = top + distal_half - 8
    draw.line(
        (
            centre - distal_half,
            side_start_y,
            centre - proximal_half,
            bottom + 20,
        ),
        fill=INK,
        width=4,
    )
    draw.line(
        (
            centre + distal_half,
            side_start_y,
            centre + proximal_half,
            bottom + 20,
        ),
        fill=INK,
        width=4,
    )

    for piece, y in zip(resized, y_positions):
        canvas.alpha_composite(piece, (centre - piece.width // 2, y))

    for y in (dip_y, pip_y, bottom + 4):
        draw.line(
            (38, y, canvas.width - 38, y),
            fill=GOLD,
            width=2,
        )

    if dorsal:
        nail_width = 102
        nail_height = max(92, resized[0].height - 28)
        draw.rounded_rectangle(
            (
                centre - nail_width // 2,
                top + 18,
                centre + nail_width // 2,
                top + 18 + nail_height,
            ),
            radius=28,
            fill="white",
            outline=INK,
            width=4,
        )
    return canvas


def main():
    pieces = extract_phalanges()
    dorsal = standard_finger(pieces, True)
    palmar = standard_finger(pieces, False)

    sheet = Image.new("RGB", (1100, 1020), PAPER)
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (54, 34),
        "中指單指直軸｜最後評估版",
        fill=INK,
        font=font(34, True),
    )
    draw.text(
        (54, 84),
        "三節 WHO 指骨各自校直，保持原尺寸比例並沿同一中軸排列。",
        fill=MUTED,
        font=font(20),
    )
    for title, image, x in (
        ("手背", dorsal, 104),
        ("掌面", palmar, 576),
    ):
        draw.text(
            (x + image.width // 2, 142),
            title,
            anchor="ma",
            fill=INK,
            font=font(25, True),
        )
        sheet.paste(image.convert("RGB"), (x, 178))
    sheet.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
