#!/usr/bin/env python3
"""Build configured palmar-finger acupuncture diagrams from WHO p.168."""

import base64
import json
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


HERE = Path(__file__).parent
BASE_PNG = (
    HERE.parent
    / "who-standard-bases-20260612"
    / "who_palmar_from_dorsal_evaluation.png"
)

SPEC = {
    "point": "木炎穴",
    "code": "11.20",
    "finger": "無名指",
    "finger_id": "ring",
    "segment": "第二節",
    "segment_id": "middle",
    "target_line": "D",
    "division_name": "三分點法",
    "point_fractions": (1 / 3, 2 / 3),
    "point_count": "二穴",
    "reference": "原書木炎穴圖",
}

OUTPUT_PNG = HERE / "木炎穴_正式評估版_v1_WHO-p168左手掌面.png"
OUTPUT_SVG = HERE / "木炎穴_正式評估版_v1_WHO-p168左手掌面.svg"
OUTPUT_JSON = HERE / "木炎穴_定位資料_v1.json"

LOGICAL_W = 1400
LOGICAL_H = 1200
RENDER_SCALE = 2
WIDTH = LOGICAL_W * RENDER_SCALE
HEIGHT = LOGICAL_H * RENDER_SCALE

SOURCE_X = 322.0
SOURCE_Y = 112.0
SOURCE_W = 170.0
SOURCE_H = 240.0

MAIN_X = 55.0
MAIN_Y = 205.0
MAIN_W = 520.0
MAIN_H = MAIN_W * SOURCE_H / SOURCE_W

INSET_CX = 1040.0
INSET_CY = 515.0
INSET_R = 272.0
INSET_CROP = (395.0, 134.0, 457.0, 196.0)

# Ring-finger DIP/PIP centres come from the WHO p.168 finger manifest.
# The axes continue the reviewed proximal-segment direction across the middle
# phalanx; this first middle-segment output is awaiting crease review.
A_TOP = (409.14, 153.45)
A_BOTTOM = (414.97, 178.22)
C_TOP = (416.51, 151.93)
C_BOTTOM = (423.27, 176.50)
E_TOP = (423.93, 150.40)
E_BOTTOM = (430.29, 175.05)
B_TOP = ((A_TOP[0] + C_TOP[0]) / 2, (A_TOP[1] + C_TOP[1]) / 2)
B_BOTTOM = (
    (A_BOTTOM[0] + C_BOTTOM[0]) / 2,
    (A_BOTTOM[1] + C_BOTTOM[1]) / 2,
)
D_TOP = ((C_TOP[0] + E_TOP[0]) / 2, (C_TOP[1] + E_TOP[1]) / 2)
D_BOTTOM = (
    (C_BOTTOM[0] + E_BOTTOM[0]) / 2,
    (C_BOTTOM[1] + E_BOTTOM[1]) / 2,
)

MIDDLE_FINGER_POLYGON = (
    (404.0, 118.0),
    (383.0, 120.0),
    (380.0, 139.0),
    (384.0, 160.0),
    (391.0, 181.0),
    (396.0, 199.0),
    (397.0, 209.0),
    (407.0, 216.0),
    (420.0, 210.0),
    (416.0, 187.0),
    (411.0, 166.0),
    (406.0, 145.0),
)
TARGET_FINGER_POLYGON = tuple(
    (x + 19.4, y) for x, y in MIDDLE_FINGER_POLYGON
)

PAPER = (251, 246, 234)
WHITE = (255, 255, 255)
INK = (44, 28, 16)
MUTED = (117, 105, 95)
GOLD = (196, 147, 58)
VERMILLION = (123, 45, 30)
RED = (179, 38, 30)
BLUE = (0, 129, 165)


def font(size: int, serif: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(
                candidate,
                size * RENDER_SCALE,
                index=1 if "PingFang" in candidate and serif else 0,
            )
    return ImageFont.load_default()


def p(value: float) -> int:
    return round(value * RENDER_SCALE)


def point_at(start, end, fraction):
    return (
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction,
    )


LINES = {
    "A": (A_TOP, A_BOTTOM),
    "B": (B_TOP, B_BOTTOM),
    "C": (C_TOP, C_BOTTOM),
    "D": (D_TOP, D_BOTTOM),
    "E": (E_TOP, E_BOTTOM),
}
TARGET_TOP, TARGET_BOTTOM = LINES[SPEC["target_line"]]
POINTS = tuple(
    point_at(TARGET_TOP, TARGET_BOTTOM, fraction)
    for fraction in SPEC["point_fractions"]
)


def source_pixel(point, size):
    return (
        (point[0] - SOURCE_X) / SOURCE_W * size[0],
        (point[1] - SOURCE_Y) / SOURCE_H * size[1],
    )


def main_map(point):
    return (
        MAIN_X + (point[0] - SOURCE_X) / SOURCE_W * MAIN_W,
        MAIN_Y + (point[1] - SOURCE_Y) / SOURCE_H * MAIN_H,
    )


def inset_map(point):
    x0, y0, x1, y1 = INSET_CROP
    diameter = INSET_R * 2
    return (
        INSET_CX - INSET_R + (point[0] - x0) / (x1 - x0) * diameter,
        INSET_CY - INSET_R + (point[1] - y0) / (y1 - y0) * diameter,
    )


def recolour_white(image: Image.Image, colour) -> Image.Image:
    pixels = image.convert("RGB")
    data = pixels.load()
    for y in range(pixels.height):
        for x in range(pixels.width):
            red, green, blue = data[x, y]
            if red > 247 and green > 247 and blue > 247:
                data[x, y] = colour
    return pixels


def build_main_hand(base: Image.Image) -> Image.Image:
    normal = recolour_white(base, PAPER)
    dimmed = Image.blend(
        normal,
        Image.new("RGB", normal.size, PAPER),
        0.78,
    )
    mask = Image.new("L", normal.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.polygon(
        [source_pixel(point, normal.size) for point in TARGET_FINGER_POLYGON],
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(5))
    dimmed.paste(normal, mask=mask)
    return dimmed.resize(
        (p(MAIN_W), p(MAIN_H)),
        Image.Resampling.LANCZOS,
    )


def build_inset(base: Image.Image) -> Image.Image:
    x0, y0, x1, y1 = INSET_CROP
    pixel_0 = source_pixel((x0, y0), base.size)
    pixel_1 = source_pixel((x1, y1), base.size)
    crop = base.crop((*pixel_0, *pixel_1)).resize(
        (p(INSET_R * 2), p(INSET_R * 2)),
        Image.Resampling.LANCZOS,
    )
    mask = Image.new("L", crop.size, 0)
    ImageDraw.Draw(mask).ellipse(
        (0, 0, crop.width - 1, crop.height - 1),
        fill=255,
    )
    result = Image.new("RGB", crop.size, WHITE)
    result.paste(crop, mask=mask)
    return result


def line(draw, start, end, fill, width=2, dash=None):
    start = (p(start[0]), p(start[1]))
    end = (p(end[0]), p(end[1]))
    if not dash:
        draw.line((start, end), fill=fill, width=p(width))
        return
    total_x = end[0] - start[0]
    total_y = end[1] - start[1]
    length = (total_x**2 + total_y**2) ** 0.5
    if not length:
        return
    cursor = 0.0
    draw_length, gap_length = (p(dash[0]), p(dash[1]))
    while cursor < length:
        segment_end = min(length, cursor + draw_length)
        x1 = start[0] + total_x * cursor / length
        y1 = start[1] + total_y * cursor / length
        x2 = start[0] + total_x * segment_end / length
        y2 = start[1] + total_y * segment_end / length
        draw.line((x1, y1, x2, y2), fill=fill, width=p(width))
        cursor += draw_length + gap_length


def circle(draw, centre, radius, fill, outline=WHITE, outline_width=2):
    x, y = centre
    draw.ellipse(
        (
            p(x - radius),
            p(y - radius),
            p(x + radius),
            p(y + radius),
        ),
        fill=fill,
        outline=outline,
        width=p(outline_width),
    )


def centred_text(
    draw,
    xy,
    text,
    text_font,
    fill,
    stroke_width=0,
    stroke_fill=None,
):
    draw.text(
        (p(xy[0]), p(xy[1])),
        text,
        font=text_font,
        fill=fill,
        anchor="mm",
        stroke_width=p(stroke_width),
        stroke_fill=stroke_fill,
    )


def draw_main_annotations(draw):
    for point in POINTS:
        circle(draw, main_map(point), 7.0, RED, WHITE, 2)

    mapped_points = [main_map(point) for point in (A_TOP, E_TOP, E_BOTTOM, A_BOTTOM)]
    xs = [point[0] for point in mapped_points]
    ys = [point[1] for point in mapped_points]
    draw.rounded_rectangle(
        (
            p(min(xs) - 18),
            p(min(ys) - 18),
            p(max(xs) + 18),
            p(max(ys) + 18),
        ),
        radius=p(28),
        outline=GOLD,
        width=p(2),
    )
    line(
        draw,
        (max(xs) + 16, min(ys) + 4),
        (INSET_CX - INSET_R + 12, INSET_CY - 135),
        GOLD,
        1.4,
    )
    line(
        draw,
        (max(xs) + 16, max(ys) - 4),
        (INSET_CX - INSET_R + 12, INSET_CY + 135),
        GOLD,
        1.4,
    )


def draw_inset_annotations(draw):
    # DIP/PIP boundaries: no text labels.
    line(draw, inset_map(A_TOP), inset_map(E_TOP), MUTED, 2.8, (9, 5))
    line(draw, inset_map(A_BOTTOM), inset_map(E_BOTTOM), MUTED, 2.8, (9, 5))

    for name in ("A", "B", "C", "D", "E"):
        top, bottom = LINES[name]
        is_target = name == SPEC["target_line"]
        colour = RED if is_target else BLUE
        width = 4.0 if is_target else 3.2
        line(draw, inset_map(top), inset_map(bottom), colour, width, (8, 5))
        label = inset_map(top)
        label_offset_x = -14 if name == "A" else 0
        label_offset_y = -26 if name == "A" else -23
        label_colour = VERMILLION if is_target else BLUE
        centred_text(
            draw,
            (label[0] + label_offset_x, label[1] + label_offset_y),
            name,
            font(20),
            label_colour,
            1,
            label_colour,
        )

    # Division bracket offset to the side of the target line.
    target_start = inset_map(TARGET_TOP)
    target_end = inset_map(TARGET_BOTTOM)
    dx = target_end[0] - target_start[0]
    dy = target_end[1] - target_start[1]
    length = (dx**2 + dy**2) ** 0.5
    normal = (dy / length, -dx / length)
    offset = 72
    bracket_start = (
        target_start[0] + normal[0] * offset,
        target_start[1] + normal[1] * offset,
    )
    bracket_end = (
        target_end[0] + normal[0] * offset,
        target_end[1] + normal[1] * offset,
    )
    line(draw, bracket_start, bracket_end, INK, 2.8)
    for fraction in (0, 1 / 3, 2 / 3, 1):
        centre = point_at(bracket_start, bracket_end, fraction)
        cross = (normal[0] * 11, normal[1] * 11)
        line(
            draw,
            (centre[0] - cross[0], centre[1] - cross[1]),
            (centre[0] + cross[0], centre[1] + cross[1]),
            INK,
            2.8,
        )

    label_point = point_at(bracket_start, bracket_end, 0.5)
    centred_text(
        draw,
        (
            label_point[0] + normal[0] * 72,
            label_point[1] + normal[1] * 72,
        ),
        SPEC["division_name"],
        font(20),
        INK,
        1,
        INK,
    )

    for point in POINTS:
        circle(draw, inset_map(point), 10.0, RED, WHITE, 3)


def draw_labels(draw):
    draw.rectangle((p(30), p(26), p(106), p(62)), fill=VERMILLION)
    centred_text(draw, (68, 44), SPEC["code"], font(18), (247, 237, 216))
    draw.text(
        (p(124), p(27)),
        SPEC["point"],
        font=font(31, True),
        fill=INK,
    )
    draw.text(
        (p(30), p(72)),
        "正式評估版｜左手掌面｜骨骼透視",
        font=font(14),
        fill=MUTED,
    )

    draw.rounded_rectangle(
        (p(45), p(128), p(375), p(210)),
        radius=p(7),
        fill=(255, 253, 246),
        outline=GOLD,
        width=p(2),
    )
    centred_text(
        draw,
        (210, 161),
        f'{SPEC["point"]}（{SPEC["point_count"]}）',
        font(24, True),
        VERMILLION,
    )
    centred_text(
        draw,
        (210, 188),
        f'{SPEC["finger"]}{SPEC["segment"]} '
        f'{SPEC["target_line"]} 線｜{SPEC["division_name"]}',
        font(14),
        INK,
    )

    centred_text(
        draw,
        (INSET_CX, 188),
        f'{SPEC["finger"]}{SPEC["segment"]}原位放大',
        font(19),
        INK,
    )
    centred_text(
        draw,
        (1050, 850),
        f'{SPEC["target_line"]} 線＝C–E 中點線｜取指節 1/3、2/3',
        font(15),
        MUTED,
    )
    draw.text(
        (p(30), p(1164)),
        "底圖｜WHO Standard Acupuncture Point Locations in the Western Pacific Region "
        f'(2008), p.168　定位參考｜{SPEC["reference"]}　標註｜TungsAcu-DB',
        font=font(11),
        fill=MUTED,
    )


def build():
    base = Image.open(BASE_PNG).convert("RGB")
    canvas = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    canvas.paste(build_main_hand(base), (p(MAIN_X), p(MAIN_Y)))
    inset = build_inset(base)
    canvas.paste(inset, (p(INSET_CX - INSET_R), p(INSET_CY - INSET_R)))

    draw = ImageDraw.Draw(canvas)
    draw.ellipse(
        (
            p(INSET_CX - INSET_R),
            p(INSET_CY - INSET_R),
            p(INSET_CX + INSET_R),
            p(INSET_CY + INSET_R),
        ),
        outline=GOLD,
        width=p(3),
    )
    draw_main_annotations(draw)
    draw_inset_annotations(draw)
    draw_labels(draw)
    canvas.save(OUTPUT_PNG)

    buffer = BytesIO()
    canvas.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    OUTPUT_SVG.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 {LOGICAL_W} {LOGICAL_H}">
          <image href="data:image/png;base64,{encoded}"
            width="{LOGICAL_W}" height="{LOGICAL_H}"/>
        </svg>"""
    )

    OUTPUT_JSON.write_text(
        json.dumps(
            {
                "version": 1,
                "status": "awaiting_user_review",
                "point": SPEC["point"],
                "code": SPEC["code"],
                "source_page": 168,
                "view": "left_palm",
                "inset_method": "original_local_crop; no bone reconstruction",
                "finger": SPEC["finger_id"],
                "segment": SPEC["segment_id"],
                "lines_source_coordinates": {
                    "A": {"top": A_TOP, "bottom": A_BOTTOM},
                    "B": {"top": B_TOP, "bottom": B_BOTTOM},
                    "C": {"top": C_TOP, "bottom": C_BOTTOM},
                    "D": {"top": D_TOP, "bottom": D_BOTTOM},
                    "E": {"top": E_TOP, "bottom": E_BOTTOM},
                },
                "construction": {
                    "geometry": "ring-finger A line and DIP/PIP boundaries measured from user correction; C/E axes clipped to corrected boundaries",
                    "B": "midpoint line between A and C",
                    "D": "midpoint line between C and E",
                    "longitudinal_method": SPEC["division_name"],
                    "point_fractions_from_distal_boundary": SPEC["point_fractions"],
                    "point_placement": "palmar D line on ulnar side",
                },
                "points_source_coordinates": [
                    [round(value, 4) for value in point] for point in POINTS
                ],
                "outputs": {
                    "png": str(OUTPUT_PNG),
                    "svg": str(OUTPUT_SVG),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(OUTPUT_PNG)
    print(OUTPUT_SVG)
    print(OUTPUT_JSON)


if __name__ == "__main__":
    build()
