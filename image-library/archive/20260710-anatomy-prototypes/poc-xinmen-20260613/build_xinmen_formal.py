#!/usr/bin/env python3
"""Build the formal evaluation plate for Xinmen point (33.12)."""

import base64
import io
import json
import math
from pathlib import Path

import fitz
from PIL import Image, ImageChops, ImageDraw, ImageOps


HERE = Path(__file__).parent
BASE_DIR = HERE.parent / "who-standard-bases-20260612"
BASE_SVG = BASE_DIR / "muscle-bone-bases" / "04_forearm-posterior.svg"
BASE_PNG = BASE_DIR / "muscle-bone-bases" / "04_forearm-posterior.png"
CALIBRATION_JSON = (
    BASE_DIR / "calibration" / "forearm-posterior" / "calibration.json"
)

OUTPUT_SVG = HERE / "心門穴_正式評估版_v1_WHO左前臂後側.svg"
OUTPUT_PNG = HERE / "心門穴_正式評估版_v1_WHO左前臂後側.png"
OUTPUT_JSON = HERE / "心門穴_定位資料_v1.json"

CANVAS_W = 1400
CANVAS_H = 1200
SOURCE_VIEWBOX = (326.0, 100.0, 174.0, 257.0)

MAIN_X = 42.0
MAIN_Y = 156.0
MAIN_SCALE = 3.48

INSET_CX = 1030.0
INSET_CY = 510.0
INSET_R = 292.0
INSET_VIEWBOX = (341.5, 112.0, 58.4, 58.4)

INK = "#2C1C10"
MUTED = "#75695F"
GOLD = "#C4933A"
VERMILLION = "#7B2D1E"
RED = "#B3261E"
BLUE = "#008CB4"
PAPER = "#FBF6EA"

# Anatomical review anchors in the WHO source SVG coordinate system.
# The point follows the ulnar border distally from the olecranon tip.
OLECRANON_TIP = (365.2, 145.2)
ULNAR_DIRECTION_REFERENCE = (388.0, 258.2)


def add(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return a[0] + b[0], a[1] + b[1]


def sub(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return a[0] - b[0], a[1] - b[1]


def mul(v: tuple[float, float], scalar: float) -> tuple[float, float]:
    return v[0] * scalar, v[1] * scalar


def unit(v: tuple[float, float]) -> tuple[float, float]:
    length = math.hypot(*v)
    return v[0] / length, v[1] / length


def point_at_fraction(
    start: tuple[float, float],
    end: tuple[float, float],
    fraction: float,
) -> tuple[float, float]:
    return (
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction,
    )


def main_map(point: tuple[float, float]) -> tuple[float, float]:
    return (
        MAIN_X + (point[0] - SOURCE_VIEWBOX[0]) * MAIN_SCALE,
        MAIN_Y + (point[1] - SOURCE_VIEWBOX[1]) * MAIN_SCALE,
    )


def inset_map(point: tuple[float, float]) -> tuple[float, float]:
    x0, y0, width, height = INSET_VIEWBOX
    return (
        INSET_CX - INSET_R + (point[0] - x0) * (2 * INSET_R / width),
        INSET_CY - INSET_R + (point[1] - y0) * (2 * INSET_R / height),
    )


def embedded_base(
    x: float,
    y: float,
    width: float,
    height: float,
    clip_id: str | None = None,
) -> str:
    image = Image.open(BASE_PNG).convert("RGBA")
    alpha = ImageOps.grayscale(image.convert("RGB")).point(
        lambda value: 0 if value > 250 else 255
    )
    image.putalpha(alpha)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    element = (
        f"<image x='{x:.2f}' y='{y:.2f}' width='{width:.2f}' height='{height:.2f}' "
        f"href='data:image/png;base64,{encoded}' preserveAspectRatio='none'/>"
    )
    if clip_id:
        return f"<g clip-path='url(#{clip_id})'>{element}</g>"
    return element


def embedded_inset() -> str:
    image = Image.open(BASE_PNG).convert("RGBA")
    x0, y0, width, height = INSET_VIEWBOX
    source_x0, source_y0, _, _ = SOURCE_VIEWBOX
    crop_box = (
        round((x0 - source_x0) * 6),
        round((y0 - source_y0) * 6),
        round((x0 + width - source_x0) * 6),
        round((y0 + height - source_y0) * 6),
    )
    inset_size = round(INSET_R * 2)
    image = image.crop(crop_box).resize(
        (inset_size, inset_size),
        Image.Resampling.LANCZOS,
    )
    background_alpha = ImageOps.grayscale(image.convert("RGB")).point(
        lambda value: 0 if value > 250 else 255
    )
    circle_mask = Image.new("L", (inset_size, inset_size), 0)
    ImageDraw.Draw(circle_mask).ellipse(
        (0, 0, inset_size - 1, inset_size - 1),
        fill=255,
    )
    image.putalpha(ImageChops.multiply(background_alpha, circle_mask))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return (
        f"<image x='{INSET_CX - INSET_R:.2f}' y='{INSET_CY - INSET_R:.2f}' "
        f"width='{2 * INSET_R:.2f}' height='{2 * INSET_R:.2f}' "
        f"href='data:image/png;base64,{encoded}' preserveAspectRatio='none'/>"
    )


def halo_text(
    x: float,
    y: float,
    size: float,
    colour: str,
    text: str,
    anchor: str = "start",
    weight: int = 700,
) -> str:
    common = (
        f"x='{x:.1f}' y='{y:.1f}' font-size='{size}' text-anchor='{anchor}' "
        f"font-weight='{weight}' font-family='Noto Sans TC, sans-serif'"
    )
    return (
        f"<text {common} fill='none' stroke='{PAPER}' stroke-width='6' "
        f"stroke-linejoin='round'>{text}</text>"
        f"<text {common} fill='{colour}'>{text}</text>"
    )


def point_marker(
    mapper,
    point: tuple[float, float],
    radius: float,
) -> str:
    x, y = mapper(point)
    return (
        f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{radius}' fill='{RED}' "
        "stroke='#FFFFFF' stroke-width='4'/>"
    )


def dashed_segment(
    start: tuple[float, float],
    end: tuple[float, float],
    colour: str,
    width: float,
    dash: float = 10.0,
    gap: float = 8.0,
) -> str:
    direction = sub(end, start)
    length = math.hypot(*direction)
    direction = unit(direction)
    parts = []
    position = 0.0
    while position < length:
        segment_end = min(position + dash, length)
        first = add(start, mul(direction, position))
        second = add(start, mul(direction, segment_end))
        parts.append(
            f"<line x1='{first[0]:.1f}' y1='{first[1]:.1f}' "
            f"x2='{second[0]:.1f}' y2='{second[1]:.1f}' "
            f"stroke='{colour}' stroke-width='{width}'/>"
        )
        position += dash + gap
    return "".join(parts)


def build() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    calibration = json.loads(CALIBRATION_JSON.read_text())
    axis = calibration["anatomical_axis"]
    forearm_length = math.dist(axis["distal"], axis["proximal"])
    one_cun = forearm_length / 12.0
    local_distance = one_cun * 1.5
    ulnar_direction = unit(sub(ULNAR_DIRECTION_REFERENCE, OLECRANON_TIP))
    xinmen = add(OLECRANON_TIP, mul(ulnar_direction, local_distance))

    main_width = SOURCE_VIEWBOX[2] * MAIN_SCALE
    main_height = SOURCE_VIEWBOX[3] * MAIN_SCALE
    main_anatomy = embedded_base(
        MAIN_X,
        MAIN_Y,
        main_width,
        main_height,
    )
    inset_anatomy = embedded_inset()

    main_point = main_map(xinmen)
    main_tip = main_map(OLECRANON_TIP)
    inset_point = inset_map(xinmen)
    inset_tip = inset_map(OLECRANON_TIP)

    # Display the calibrated 12-cun ruler without endpoint numbers.
    ruler_distal = tuple(calibration["display_ruler"]["distal"])
    ruler_proximal = tuple(calibration["display_ruler"]["proximal"])
    ruler_start = main_map(ruler_distal)
    ruler_end = main_map(ruler_proximal)
    spec = calibration["spec"]
    source_x0, source_y0, source_width, source_height = SOURCE_VIEWBOX

    def normalized_source(point: list[float]) -> tuple[float, float]:
        return (
            source_x0 + point[0] * source_width,
            source_y0 + point[1] * source_height,
        )

    elbow_line_start = normalized_source(spec["proximal_line"][0])
    wrist_line_start = normalized_source(spec["distal_line"][0])
    trim = spec["boundary_trim"]
    elbow_display_start = point_at_fraction(
        elbow_line_start,
        ruler_proximal,
        trim,
    )
    wrist_display_start = point_at_fraction(
        wrist_line_start,
        ruler_distal,
        trim,
    )
    elbow_display_start = main_map(elbow_display_start)
    wrist_display_start = main_map(wrist_display_start)
    ruler_vector = sub(ruler_end, ruler_start)
    ruler_length = math.hypot(*ruler_vector)
    ruler_unit = unit(ruler_vector)
    ruler_cross = (-ruler_unit[1], ruler_unit[0])
    ruler_parts = [
        f"<line x1='{ruler_start[0]:.1f}' y1='{ruler_start[1]:.1f}' "
        f"x2='{ruler_end[0]:.1f}' y2='{ruler_end[1]:.1f}' "
        f"stroke='{BLUE}' stroke-width='4'/>"
    ]
    for cun in range(13):
        centre = add(ruler_start, mul(ruler_unit, ruler_length * cun / 12))
        major = cun in {0, 3, 6, 9, 12}
        half = 12 if major else 7
        start = add(centre, mul(ruler_cross, -half))
        end = add(centre, mul(ruler_cross, half))
        ruler_parts.append(
            f"<line x1='{start[0]:.1f}' y1='{start[1]:.1f}' "
            f"x2='{end[0]:.1f}' y2='{end[1]:.1f}' "
            f"stroke='{BLUE}' stroke-width='{4 if major else 2.4}'/>"
        )
        if major and cun not in {0, 12}:
            label = add(centre, mul(ruler_cross, -26))
            ruler_parts.append(
                halo_text(label[0], label[1] + 6, 19, "#006F90", str(cun), "middle")
            )
    ruler_mid = point_at_fraction(ruler_start, ruler_end, 0.5)
    ruler_label = add(ruler_mid, mul(ruler_cross, 38))
    ruler_parts.append(
        halo_text(ruler_label[0], ruler_label[1] + 7, 23, "#006F90", "12 寸", "middle")
    )

    local_vector = sub(inset_point, inset_tip)
    local_unit = unit(local_vector)
    local_cross = (-local_unit[1], local_unit[0])
    bracket_offset = -42.0
    bracket_tip = add(inset_tip, mul(local_cross, bracket_offset))
    bracket_point = add(inset_point, mul(local_cross, bracket_offset))
    bracket_parts = [
        f"<line x1='{bracket_tip[0]:.1f}' y1='{bracket_tip[1]:.1f}' "
        f"x2='{bracket_point[0]:.1f}' y2='{bracket_point[1]:.1f}' "
        f"stroke='{GOLD}' stroke-width='3'/>"
    ]
    for centre in (bracket_tip, bracket_point):
        start = add(centre, mul(local_cross, -14))
        end = add(centre, mul(local_cross, 14))
        bracket_parts.append(
            f"<line x1='{start[0]:.1f}' y1='{start[1]:.1f}' "
            f"x2='{end[0]:.1f}' y2='{end[1]:.1f}' "
            f"stroke='{GOLD}' stroke-width='3'/>"
        )
    bracket_label = add(
        point_at_fraction(bracket_tip, bracket_point, 0.5),
        mul(local_cross, -28),
    )
    bracket_parts.append(
        halo_text(
            bracket_label[0],
            bracket_label[1] + 7,
            22,
            VERMILLION,
            "1.5 寸",
            "middle",
        )
    )

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg'
      xmlns:xlink='http://www.w3.org/1999/xlink'
      viewBox='0 0 {CANVAS_W} {CANVAS_H}'>
      <defs>
        <clipPath id='inset-clip'>
          <circle cx='{INSET_CX}' cy='{INSET_CY}' r='{INSET_R}'/>
        </clipPath>
      </defs>
      <rect width='{CANVAS_W}' height='{CANVAS_H}' fill='{PAPER}'/>

      {main_anatomy}
      {dashed_segment(elbow_display_start, ruler_end, "#EF3B24", 3)}
      {dashed_segment(wrist_display_start, ruler_start, "#EF3B24", 3)}
      {''.join(ruler_parts)}
      {point_marker(main_map, xinmen, 10)}
      <line x1='{main_point[0] + 12:.1f}' y1='{main_point[1]:.1f}'
        x2='{point_at_fraction(ruler_start, ruler_end, 10.5 / 12)[0]:.1f}'
        y2='{point_at_fraction(ruler_start, ruler_end, 10.5 / 12)[1]:.1f}'
        stroke='{GOLD}' stroke-width='2.2' stroke-dasharray='8 6'
        stroke-opacity='.85'/>
      <line x1='{main_point[0] + 10:.1f}' y1='{main_point[1]:.1f}'
        x2='760' y2='400' stroke='{GOLD}' stroke-width='2'
        stroke-opacity='.72'/>
      <circle cx='{main_tip[0]:.1f}' cy='{main_tip[1]:.1f}' r='7'
        fill='#FFFFFF' stroke='{GOLD}' stroke-width='3'/>

      <circle cx='{INSET_CX}' cy='{INSET_CY}' r='{INSET_R}'
        fill='#FFFFFF' stroke='{GOLD}' stroke-width='3'/>
      {inset_anatomy}
      <circle cx='{INSET_CX}' cy='{INSET_CY}' r='{INSET_R}'
        fill='none' stroke='{GOLD}' stroke-width='3'/>
      <line x1='{inset_tip[0]:.1f}' y1='{inset_tip[1]:.1f}'
        x2='{inset_point[0]:.1f}' y2='{inset_point[1]:.1f}'
        stroke='{GOLD}' stroke-width='2.5' stroke-dasharray='8 6'/>
      <circle cx='{inset_tip[0]:.1f}' cy='{inset_tip[1]:.1f}' r='8'
        fill='#FFFFFF' stroke='{GOLD}' stroke-width='3'/>
      {point_marker(inset_map, xinmen, 13)}
      {''.join(bracket_parts)}
      {halo_text(inset_tip[0] - 22, inset_tip[1] - 18, 20, INK, "肘尖／尺骨鷹嘴", "end")}
      {halo_text(inset_point[0] + 24, inset_point[1] + 7, 23, VERMILLION, "心門穴", "start")}
      {halo_text(1030, 190, 22, INK, "肘部尺側放大", "middle")}

      <g id='labels'>
        <rect x='30' y='26' width='84' height='38' fill='{VERMILLION}'/>
        <text x='72' y='52' font-size='18' fill='#F7EDD8' text-anchor='middle'
          font-family='Noto Sans TC, sans-serif'>33.12</text>
        <text x='134' y='57' font-size='33' font-weight='700' fill='{INK}'
          font-family='Noto Serif TC, serif'>心門穴</text>
        <text x='30' y='94' font-size='14' fill='{MUTED}'
          font-family='Noto Sans TC, sans-serif'>正式評估版｜左前臂後側・骨骼透視</text>

        <rect x='765' y='835' width='555' height='190' rx='10'
          fill='#FFFDF6' stroke='{GOLD}' stroke-width='2'/>
        <text x='800' y='880' font-size='24' font-weight='700' fill='{VERMILLION}'
          font-family='Noto Serif TC, serif'>心門穴（董師原穴）</text>
        <text x='800' y='922' font-size='18' fill='{INK}'
          font-family='Noto Sans TC, sans-serif'>手撫胸取穴，肘尖向腕側 1.5 寸</text>
        <text x='800' y='958' font-size='18' fill='{INK}'
          font-family='Noto Sans TC, sans-serif'>尺骨內側凹陷、貼近尺骨取穴</text>
        <text x='800' y='994' font-size='15' fill='{MUTED}'
          font-family='Noto Sans TC, sans-serif'>本圖不顯示「楊維傑新心門」2 寸變體</text>

        <circle cx='795' cy='1068' r='9' fill='{RED}' stroke='#FFFFFF'
          stroke-width='3'/>
        <text x='820' y='1075' font-size='17' fill='{INK}'
          font-family='Noto Sans TC, sans-serif'>心門穴</text>
        <line x1='985' y1='1068' x2='1045' y2='1068'
          stroke='{GOLD}' stroke-width='3' stroke-dasharray='8 6'/>
        <text x='1060' y='1075' font-size='17' fill='{INK}'
          font-family='Noto Sans TC, sans-serif'>局部量距</text>

        <text x='30' y='1172' font-size='12' fill='{INK}' fill-opacity='.55'
          font-family='Noto Sans TC, sans-serif'>底圖｜WHO Standard Acupuncture Point Locations
          in the Western Pacific Region (2008)　定位參考｜董師原文、原書附圖　標註｜TungsAcu-DB</text>
      </g>
    </svg>"""

    OUTPUT_SVG.write_text(svg)
    rendered = fitz.open(OUTPUT_SVG)
    rendered[0].get_pixmap(
        matrix=fitz.Matrix(2, 2),
        alpha=False,
    ).save(OUTPUT_PNG)

    OUTPUT_JSON.write_text(
        json.dumps(
            {
                "version": 1,
                "status": "awaiting_user_review",
                "point": "心門穴",
                "code": "33.12",
                "variant": "董師原穴",
                "view": "left_forearm_posterior",
                "source_svg": str(BASE_SVG),
                "source_viewbox": list(SOURCE_VIEWBOX),
                "landmarks_svg": {
                    "olecranon_tip": list(OLECRANON_TIP),
                    "ulnar_direction_reference": list(ULNAR_DIRECTION_REFERENCE),
                    "xinmen": [round(value, 3) for value in xinmen],
                },
                "measurement": {
                    "forearm_total_cun": 12,
                    "forearm_axis_length_svg": round(forearm_length, 3),
                    "one_cun_svg": round(one_cun, 3),
                    "distance_from_olecranon_cun": 1.5,
                    "distance_from_olecranon_svg": round(local_distance, 3),
                    "method": (
                        "1.5 / 12 of calibrated forearm length, projected "
                        "distally along the ulnar border"
                    ),
                },
                "note": (
                    "This plate shows the original 1.5-cun Xinmen point. "
                    "The 2-cun Yang Weijie variant is intentionally omitted."
                ),
                "output_svg": str(OUTPUT_SVG),
                "output_png": str(OUTPUT_PNG),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(f"SVG: {OUTPUT_SVG}")
    print(f"PNG: {OUTPUT_PNG}")
    print(f"Data: {OUTPUT_JSON}")
    print(f"Xinmen SVG coordinate: {xinmen}")


if __name__ == "__main__":
    build()
