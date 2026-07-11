#!/usr/bin/env python3
"""Build first-pass proportional bone calibrations for the eight limb bases."""

import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont

from build_standard_bases import FONT_PATH, HERE


BASE_DIR = HERE / "muscle-bone-bases"
CALIBRATION_DIR = HERE / "calibration"
MANIFEST_PATH = CALIBRATION_DIR / "limb-calibration-manifest.json"
REVIEW_SHEET_PATH = HERE / "WHO_四肢骨度校準_8張檢查總覽.png"
RENDER_SCALE = 6


Point = tuple[float, float]
Line = tuple[Point, Point]


@dataclass(frozen=True)
class CalibrationSpec:
    number: int
    slug: str
    title: str
    base_stem: str
    total_cun: int
    proximal_name: str
    distal_name: str
    proximal_line: Line
    distal_line: Line
    axis_proximal: Point
    axis_distal: Point
    ruler_offset: float
    guide_offset: float
    major_interval: int
    evidence: str
    review_note: str
    boundary_trim: float = 0.0


# Coordinates are normalized to each source SVG viewBox. These are first-pass
# anatomical landmark estimates for human review, not approved point locations.
SPECS = [
    CalibrationSpec(
        1,
        "upper-arm-anterior",
        "上臂／前面",
        "01_upper-arm-anterior",
        9,
        "腋橫紋",
        "肘橫紋",
        ((0.0538, 0.3381), (0.8587, 0.3766)),
        ((0.18, 0.70), (0.67, 0.72)),
        (0.43, 0.26),
        (0.42, 0.71),
        0.38,
        -0.43,
        3,
        "WHO p.12: anterior axillary fold to cubital crease = 9 B-cun",
        "已依使用者紅線重建；確認腋橫紋與肘橫紋。",
        boundary_trim=0.18,
    ),
    CalibrationSpec(
        2,
        "upper-arm-posterior",
        "上臂／後面",
        "02_upper-arm-posterior",
        9,
        "腋橫紋",
        "肘橫紋",
        ((0.1631, 0.4279), (0.7485, 0.3482)),
        ((0.2742, 0.8271), (0.8596, 0.7475)),
        (0.56, 0.38),
        (0.58, 0.78),
        0.34,
        -0.48,
        3,
        "WHO p.12: posterior axillary fold to cubital crease = 9 B-cun",
        "已依使用者紅線重建；確認腋橫紋與肘橫紋。",
        boundary_trim=0.18,
    ),
    CalibrationSpec(
        4,
        "forearm-posterior",
        "前臂／後面",
        "04_forearm-posterior",
        12,
        "肘橫紋",
        "腕橫紋",
        ((0.0123, 0.2199), (0.5164, 0.1361)),
        ((0.1831, 0.6769), (0.6248, 0.5943)),
        (0.43, 0.19),
        (0.48, 0.66),
        0.34,
        -0.46,
        3,
        "WHO p.12: cubital crease to wrist crease = 12 B-cun",
        "已依使用者紅線重建；確認肘橫紋與腕橫紋。",
        boundary_trim=0.18,
    ),
    CalibrationSpec(
        5,
        "thigh-anterior",
        "大腿／前面",
        "05_thigh-anterior",
        19,
        "大轉子",
        "膝中",
        ((0.23, 0.29), (0.86, 0.30)),
        ((0.0728, 0.8408), (0.8872, 0.8371)),
        (0.64, 0.30),
        (0.51, 0.81),
        0.43,
        -0.52,
        3,
        "使用者校正：大轉子至膝中 = 19 寸",
        "已依使用者紅線重建；確認大轉子與膝中。",
    ),
    CalibrationSpec(
        6,
        "thigh-posterior",
        "大腿／後面",
        "06_thigh-posterior",
        14,
        "臀橫紋",
        "膝中",
        ((0.24, 0.22), (0.86, 0.23)),
        ((0.23, 0.78), (0.88, 0.79)),
        (0.62, 0.23),
        (0.65, 0.79),
        0.43,
        -0.50,
        3,
        "使用者校正：臀橫紋至膝中 = 14 寸",
        "確認臀橫紋與膝中。",
    ),
    CalibrationSpec(
        7,
        "lower-leg-anterior",
        "小腿／前面",
        "07_lower-leg-anterior",
        16,
        "膝中",
        "外踝尖",
        ((0.1191, 0.1470), (0.7407, 0.1508)),
        ((0.0137, 0.8726), (0.8456, 0.8821)),
        (0.43, 0.22),
        (0.56, 0.89),
        0.39,
        -0.49,
        4,
        "使用者校正：膝中至外踝尖 = 16 寸",
        "已依使用者紅線重建；確認膝中與外踝尖。",
        boundary_trim=0.18,
    ),
    CalibrationSpec(
        8,
        "lower-leg-posterior",
        "小腿／後面",
        "08_lower-leg-posterior",
        13,
        "脛骨內髁下緣",
        "內踝尖",
        ((0.2252, 0.2581), (0.7832, 0.2672)),
        ((0.1820, 0.7857), (0.7400, 0.7950)),
        (0.52, 0.21),
        (0.58, 0.84),
        0.40,
        -0.49,
        3,
        "使用者校正：脛骨內髁下緣至內踝尖 = 13 寸",
        "已依使用者紅線重建；確認脛骨內髁下緣與內踝尖。",
        boundary_trim=0.18,
    ),
]


def parse_viewbox(svg: str) -> tuple[float, float, float, float]:
    match = re.search(r'viewBox="([^"]+)"', svg)
    if not match:
        raise RuntimeError("SVG has no viewBox")
    values = tuple(float(value) for value in match.group(1).split())
    if len(values) != 4:
        raise RuntimeError(f"Unexpected viewBox: {values}")
    return values


def normalized_point(point: Point, viewbox: tuple[float, float, float, float]) -> Point:
    x0, y0, width, height = viewbox
    return x0 + point[0] * width, y0 + point[1] * height


def vector(start: Point, end: Point) -> Point:
    return end[0] - start[0], end[1] - start[1]


def add(point: Point, delta: Point) -> Point:
    return point[0] + delta[0], point[1] + delta[1]


def scale(delta: Point, amount: float) -> Point:
    return delta[0] * amount, delta[1] * amount


def dot(first: Point, second: Point) -> float:
    return first[0] * second[0] + first[1] * second[1]


def unit(delta: Point) -> Point:
    length = math.hypot(*delta)
    return delta[0] / length, delta[1] / length


def cross(first: Point, second: Point) -> float:
    return first[0] * second[1] - first[1] * second[0]


def line_intersection(first: Line, second: Line) -> Point:
    first_direction = vector(*first)
    second_direction = vector(*second)
    denominator = cross(first_direction, second_direction)
    if abs(denominator) < 1e-9:
        raise RuntimeError("Calibration lines are parallel")
    displacement = vector(first[0], second[0])
    amount = cross(displacement, second_direction) / denominator
    return add(first[0], scale(first_direction, amount))


def shifted_axis(axis: Line, perpendicular: Point, offset: float) -> Line:
    delta = scale(perpendicular, offset)
    return add(axis[0], delta), add(axis[1], delta)


def point_at_fraction(start: Point, end: Point, fraction: float) -> Point:
    return (
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction,
    )


def dashed_line(start: Point, end: Point) -> str:
    direction = vector(start, end)
    length = math.hypot(*direction)
    direction = unit(direction)
    segments = []
    position = 0.0
    while position < length:
        segment_end = min(position + 4.0, length)
        first = add(start, scale(direction, position))
        second = add(start, scale(direction, segment_end))
        segments.append(
            f'<line x1="{first[0]:.3f}" y1="{first[1]:.3f}" '
            f'x2="{second[0]:.3f}" y2="{second[1]:.3f}" '
            'stroke="#ef3b24" stroke-width="0.9"/>'
        )
        position += 7.0
    return "".join(segments)


def build_overlay(
    spec: CalibrationSpec,
    proximal_boundary: Line,
    distal_boundary: Line,
    anatomical_proximal: Point,
    anatomical_distal: Point,
    ruler_proximal: Point,
    ruler_distal: Point,
    caption_x: float,
    caption_y: float,
) -> str:
    ruler_direction = unit(vector(ruler_distal, ruler_proximal))
    perpendicular = (-ruler_direction[1], ruler_direction[0])
    tick_elements = []
    for cun in range(spec.total_cun + 1):
        point = point_at_fraction(
            ruler_distal,
            ruler_proximal,
            cun / spec.total_cun,
        )
        major = cun in {0, spec.total_cun} or cun % spec.major_interval == 0
        half_length = 3.2 if major else 1.8
        start = add(point, scale(perpendicular, -half_length))
        end = add(point, scale(perpendicular, half_length))
        tick_elements.append(
            f'<line x1="{start[0]:.3f}" y1="{start[1]:.3f}" '
            f'x2="{end[0]:.3f}" y2="{end[1]:.3f}" '
            f'stroke="#008fb3" stroke-width="{0.85 if major else 0.55}"/>'
        )
        if major and cun not in {0, spec.total_cun}:
            label = add(point, scale(perpendicular, -8.0))
            tick_elements.append(
                f'<text x="{label[0]:.3f}" y="{label[1] + 1.6:.3f}" '
                'font-family="Arial, sans-serif" font-size="4.5" '
                'font-weight="700" text-anchor="middle" fill="#006b86">'
                f"{cun}</text>"
            )

    proximal_label = add(proximal_boundary[0], (-2.0, -3.0))
    distal_label = add(distal_boundary[0], (-2.0, -3.0))
    ruler_label = add(
        point_at_fraction(ruler_distal, ruler_proximal, 0.52),
        scale(perpendicular, 10.0),
    )
    return f"""
<defs>
  <marker id="calibration-arrow" markerWidth="6" markerHeight="6"
      refX="5" refY="3" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L6,3 L0,6 Z" fill="#008fb3"/>
  </marker>
  <marker id="calibration-arrow-start" markerWidth="6" markerHeight="6"
      refX="1" refY="3" orient="auto" markerUnits="strokeWidth">
    <path d="M6,0 L0,3 L6,6 Z" fill="#008fb3"/>
  </marker>
</defs>
<g id="bone-proportional-calibration">
  {dashed_line(proximal_boundary[0], proximal_boundary[1])}
  {dashed_line(distal_boundary[0], distal_boundary[1])}
  <line x1="{ruler_distal[0]:.3f}" y1="{ruler_distal[1]:.3f}"
      x2="{ruler_proximal[0]:.3f}" y2="{ruler_proximal[1]:.3f}"
      stroke="#008fb3" stroke-width="1.15"
      marker-start="url(#calibration-arrow-start)"
      marker-end="url(#calibration-arrow)"/>
  {''.join(tick_elements)}
  <text x="{proximal_label[0]:.3f}" y="{proximal_label[1]:.3f}"
      font-family="STHeiti, PingFang TC, sans-serif" font-size="4.2"
      font-weight="700" text-anchor="end" fill="#9f2517">{spec.proximal_name}</text>
  <text x="{distal_label[0]:.3f}" y="{distal_label[1]:.3f}"
      font-family="STHeiti, PingFang TC, sans-serif" font-size="4.2"
      font-weight="700" text-anchor="end" fill="#9f2517">{spec.distal_name}</text>
  <text x="{ruler_label[0]:.3f}" y="{ruler_label[1]:.3f}"
      font-family="STHeiti, PingFang TC, sans-serif" font-size="5"
      font-weight="700" fill="#006b86">{spec.total_cun} 寸</text>
  <text x="{caption_x:.3f}" y="{caption_y:.3f}"
      font-family="STHeiti, PingFang TC, sans-serif" font-size="3.7"
      font-weight="500" text-anchor="middle" fill="#655b54">
      定位點｜{spec.proximal_name}--{spec.distal_name}，{spec.total_cun} 寸</text>
</g>
"""


def build_spec(spec: CalibrationSpec) -> dict:
    base_svg_path = BASE_DIR / f"{spec.base_stem}.svg"
    base_png_path = BASE_DIR / f"{spec.base_stem}.png"
    base_svg = base_svg_path.read_text()
    viewbox = parse_viewbox(base_svg)
    _, _, width, _ = viewbox

    proximal_line = tuple(
        normalized_point(point, viewbox) for point in spec.proximal_line
    )
    distal_line = tuple(
        normalized_point(point, viewbox) for point in spec.distal_line
    )
    proximal_direction = unit(vector(*proximal_line))
    distal_direction = unit(vector(*distal_line))
    if dot(proximal_direction, distal_direction) < 0:
        distal_direction = scale(distal_direction, -1)

    boundary_tangent = unit(add(proximal_direction, distal_direction))
    if boundary_tangent[0] < 0:
        boundary_tangent = scale(boundary_tangent, -1)

    ruler_direction = (-boundary_tangent[1], boundary_tangent[0])
    axis_proximal_anchor = normalized_point(spec.axis_proximal, viewbox)
    axis_distal_anchor = normalized_point(spec.axis_distal, viewbox)
    desired_direction = unit(vector(axis_distal_anchor, axis_proximal_anchor))
    if dot(ruler_direction, desired_direction) < 0:
        ruler_direction = scale(ruler_direction, -1)

    axis_anchor = (
        (axis_proximal_anchor[0] + axis_distal_anchor[0]) / 2,
        (axis_proximal_anchor[1] + axis_distal_anchor[1]) / 2,
    )
    span = max(viewbox[2], viewbox[3]) * 2
    axis = (
        add(axis_anchor, scale(ruler_direction, -span)),
        add(axis_anchor, scale(ruler_direction, span)),
    )
    ruler_axis = shifted_axis(
        axis,
        boundary_tangent,
        spec.ruler_offset * width,
    )
    guide_axis = shifted_axis(
        axis,
        boundary_tangent,
        spec.guide_offset * width,
    )

    anatomical_distal = line_intersection(distal_line, axis)
    anatomical_proximal = line_intersection(proximal_line, axis)
    ruler_distal = line_intersection(distal_line, ruler_axis)
    ruler_proximal = line_intersection(proximal_line, ruler_axis)
    distal_boundary = (
        line_intersection(distal_line, guide_axis),
        ruler_distal,
    )
    proximal_boundary = (
        line_intersection(proximal_line, guide_axis),
        ruler_proximal,
    )
    proximal_display_boundary = (
        point_at_fraction(
            proximal_boundary[0],
            proximal_boundary[1],
            spec.boundary_trim,
        ),
        proximal_boundary[1],
    )
    distal_display_boundary = (
        point_at_fraction(
            distal_boundary[0],
            distal_boundary[1],
            spec.boundary_trim,
        ),
        distal_boundary[1],
    )

    all_points = [
        *proximal_display_boundary,
        *distal_display_boundary,
        ruler_distal,
        ruler_proximal,
    ]
    x0, y0, original_width, original_height = viewbox
    label_padding = max(
        20.0,
        5.0 * max(len(spec.proximal_name), len(spec.distal_name)),
    )
    min_x = min(
        x0,
        proximal_display_boundary[0][0] - label_padding,
        distal_display_boundary[0][0] - label_padding,
        *(point[0] - 20 for point in all_points),
    )
    max_x = max(x0 + original_width, *(point[0] + 24 for point in all_points))
    min_y = min(y0, *(point[1] - 10 for point in all_points))
    max_y = max(y0 + original_height, *(point[1] + 10 for point in all_points))
    caption_x = x0 + original_width / 2
    caption_y = max_y + 8
    output_viewbox = (
        min_x,
        min_y,
        max_x - min_x,
        caption_y + 5 - min_y,
    )

    base_svg = re.sub(
        r'width="\d+" height="\d+" viewBox="[^"]+"',
        f'width="{output_viewbox[2]:.0f}" height="{output_viewbox[3]:.0f}" '
        f'viewBox="{output_viewbox[0]:.3f} {output_viewbox[1]:.3f} '
        f'{output_viewbox[2]:.3f} {output_viewbox[3]:.3f}"',
        base_svg,
        count=1,
    )
    overlay = build_overlay(
        spec,
        proximal_display_boundary,
        distal_display_boundary,
        anatomical_proximal,
        anatomical_distal,
        ruler_proximal,
        ruler_distal,
        caption_x,
        caption_y,
    )
    output_svg = re.sub(r"</svg>\s*$", overlay + "</svg>", base_svg)

    output_dir = CALIBRATION_DIR / spec.slug
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = output_dir / f"{spec.slug}-{spec.total_cun}cun-calibration"
    svg_path = stem.with_suffix(".svg")
    png_path = stem.with_suffix(".png")
    data_path = output_dir / "calibration.json"
    svg_path.write_text(output_svg)
    rendered = fitz.open(svg_path)
    rendered[0].get_pixmap(
        matrix=fitz.Matrix(RENDER_SCALE, RENDER_SCALE),
        alpha=False,
    ).save(png_path)

    anatomical_points = {
        str(cun): [
            round(value, 3)
            for value in point_at_fraction(
                anatomical_distal,
                anatomical_proximal,
                cun / spec.total_cun,
            )
        ]
        for cun in range(spec.total_cun + 1)
    }
    record = {
        "version": 1,
        "status": "awaiting_anatomy_review",
        "spec": asdict(spec),
        "base_svg": str(base_svg_path),
        "base_png": str(base_png_path),
        "source_viewbox": list(viewbox),
        "output_viewbox": [round(value, 3) for value in output_viewbox],
        "anatomical_axis": {
            "distal": [round(value, 3) for value in anatomical_distal],
            "proximal": [round(value, 3) for value in anatomical_proximal],
            "formula": (
                "P(cun) = distal + (cun / total_cun) * (proximal - distal)"
            ),
            "points_svg": anatomical_points,
        },
        "display_ruler": {
            "distal": [round(value, 3) for value in ruler_distal],
            "proximal": [round(value, 3) for value in ruler_proximal],
            "method": "best_common_normal_to_user_boundaries",
            "boundary_left_trim_fraction": spec.boundary_trim,
            "extent_defined_by_anatomical_boundaries": True,
            "endpoint_values_visible": False,
        },
        "output_svg": str(svg_path),
        "output_png": str(png_path),
    }
    data_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    return record


def fit_on_card(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = image.copy()
    fitted.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    canvas.paste(
        fitted,
        ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2),
    )
    return canvas


def build_review_sheet(records: list[dict]) -> None:
    title_font = ImageFont.truetype(str(FONT_PATH), 26)
    meta_font = ImageFont.truetype(str(FONT_PATH), 17)
    heading_font = ImageFont.truetype(str(FONT_PATH), 38)
    cards = []

    approved_png = (
        CALIBRATION_DIR
        / "forearm-anterior"
        / "forearm-anterior-12cun-calibration.png"
    )
    approved = {
        "title": "前臂／前面",
        "total_cun": 12,
        "status": "approved",
        "output_png": str(approved_png),
        "review_note": "已由使用者校正腕橫紋、肘橫紋與版式。",
    }
    ordered = [records[0], records[1], approved, *records[2:]]
    for index, record in enumerate(ordered, 1):
        if record.get("status") == "approved":
            title = record["title"]
            total_cun = record["total_cun"]
            review_note = record["review_note"]
            png_path = Path(record["output_png"])
            status = "已校正"
        else:
            spec = record["spec"]
            title = spec["title"]
            total_cun = spec["total_cun"]
            review_note = spec["review_note"]
            png_path = Path(record["output_png"])
            status = "待確認"

        card = Image.new("RGB", (520, 720), "#f7f2e8")
        draw = ImageDraw.Draw(card)
        draw.rounded_rectangle(
            (8, 8, 512, 712),
            radius=18,
            fill="white",
            outline="#c89a45",
            width=2,
        )
        art = fit_on_card(Image.open(png_path).convert("RGB"), (470, 545))
        card.paste(art, (25, 68))
        draw.text(
            (26, 22),
            f"{index:02d}  {title}｜{total_cun} 寸",
            fill="#2a1b14",
            font=title_font,
        )
        status_colour = "#237a46" if status == "已校正" else "#a64a24"
        draw.text((26, 625), status, fill=status_colour, font=meta_font)
        draw.text((26, 656), review_note, fill="#655b54", font=meta_font)
        cards.append(card)

    sheet = Image.new("RGB", (4 * 520, 2 * 720 + 110), "#efe7d8")
    draw = ImageDraw.Draw(sheet)
    draw.text((26, 28), "WHO 四肢骨度校準｜8 張檢查總覽", fill="#2a1b14", font=heading_font)
    draw.text(
        (26, 74),
        "前臂前面已校正；其餘已依使用者紅線重建，比例尺取兩界線的共同法線",
        fill="#655b54",
        font=meta_font,
    )
    for index, card in enumerate(cards):
        sheet.paste(card, ((index % 4) * 520, 110 + (index // 4) * 720))
    sheet.save(REVIEW_SHEET_PATH)


def main() -> None:
    CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
    records = [build_spec(spec) for spec in SPECS]
    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "version": 1,
                "status": "awaiting_anatomy_review",
                "approved": ["forearm-anterior"],
                "generated": [record["spec"]["slug"] for record in records],
                "items": records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    build_review_sheet(records)
    print(f"Generated {len(records)} first-pass limb calibrations")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Review sheet: {REVIEW_SHEET_PATH}")


if __name__ == "__main__":
    main()
