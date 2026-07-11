#!/usr/bin/env python3
"""Build the anterior-forearm 12-cun calibration overlay."""

import json
import math
import re
from pathlib import Path

import fitz
import numpy as np
from PIL import Image


HERE = Path(__file__).parent
CALIBRATION_DIR = HERE / "calibration" / "forearm-anterior"
MARKUP_PATH = CALIBRATION_DIR / "user-markup-reference.png"
BASE_SVG_PATH = HERE / "muscle-bone-bases" / "03_forearm-anterior.svg"
BASE_PNG_PATH = HERE / "muscle-bone-bases" / "03_forearm-anterior.png"
OUTPUT_STEM = CALIBRATION_DIR / "forearm-anterior-12cun-calibration"
DATA_PATH = CALIBRATION_DIR / "calibration.json"

SOURCE_VIEWBOX = (326.0, 100.0, 174.0, 257.0)
AXIS_INWARD_SHIFT_SCREEN_PX = -180.0
BOUNDARY_LEFT_AXIS_SHIFT_SCREEN_PX = -400.0
BOUNDARY_RIGHT_AXIS_SHIFT_SCREEN_PX = 0.0
OUTPUT_VIEWBOX = (
    SOURCE_VIEWBOX[0],
    SOURCE_VIEWBOX[1],
    SOURCE_VIEWBOX[2],
    SOURCE_VIEWBOX[3] + 14.0,
)
RENDER_SCALE = 6


def fit_markup_lines() -> dict[str, tuple[float, float]]:
    pixels = np.asarray(Image.open(MARKUP_PATH).convert("RGB")).astype(np.int16)
    red, green, blue = [pixels[:, :, index] for index in range(3)]

    red_mask = (
        (red > 220)
        & (green < 110)
        & (blue < 90)
        & (red - green > 100)
    )
    blue_mask = (
        (blue > 110)
        & (green > 80)
        & (red < 80)
        & (blue > red + 70)
        & (green > red + 50)
    )

    lines = {}
    for name, y0, y1 in (
        ("elbow_boundary", 200, 400),
        ("wrist_boundary", 900, 1150),
    ):
        y_coordinates, x_coordinates = np.where(red_mask[y0:y1])
        y_coordinates = y_coordinates + y0
        slope, intercept = np.polyfit(x_coordinates, y_coordinates, 1)
        lines[name] = (float(slope), float(intercept))

    y_coordinates, x_coordinates = np.where(blue_mask)
    slope, intercept = np.polyfit(y_coordinates, x_coordinates, 1)
    lines["dimension_axis"] = (float(slope), float(intercept))
    return lines


def line_intersection(
    boundary: tuple[float, float],
    axis: tuple[float, float],
    axis_shift_x: float,
) -> tuple[float, float]:
    boundary_slope, boundary_intercept = boundary
    axis_slope, axis_intercept = axis
    shifted_intercept = axis_intercept + axis_shift_x
    y = (
        boundary_slope * shifted_intercept + boundary_intercept
    ) / (1 - boundary_slope * axis_slope)
    x = axis_slope * y + shifted_intercept
    return float(x), float(y)


def screen_to_base_pixel(
    point: tuple[float, float],
    screen_size: tuple[int, int],
    base_size: tuple[int, int],
) -> tuple[float, float]:
    return (
        point[0] * base_size[0] / screen_size[0],
        point[1] * base_size[1] / screen_size[1],
    )


def base_pixel_to_svg(point: tuple[float, float]) -> tuple[float, float]:
    x0, y0, _, _ = SOURCE_VIEWBOX
    return x0 + point[0] / RENDER_SCALE, y0 + point[1] / RENDER_SCALE


def boundary_segment(
    line: tuple[float, float],
    axis: tuple[float, float],
    screen_size: tuple[int, int],
    base_size: tuple[int, int],
) -> tuple[tuple[float, float], tuple[float, float]]:
    screen_points = (
        line_intersection(
            line,
            axis,
            BOUNDARY_LEFT_AXIS_SHIFT_SCREEN_PX,
        ),
        line_intersection(
            line,
            axis,
            BOUNDARY_RIGHT_AXIS_SHIFT_SCREEN_PX,
        ),
    )
    return tuple(
        base_pixel_to_svg(
            screen_to_base_pixel(point, screen_size, base_size)
        )
        for point in screen_points
    )


def point_at_cun(
    wrist: tuple[float, float],
    elbow: tuple[float, float],
    cun: float,
) -> tuple[float, float]:
    ratio = cun / 12.0
    return (
        wrist[0] + (elbow[0] - wrist[0]) * ratio,
        wrist[1] + (elbow[1] - wrist[1]) * ratio,
    )


def svg_point(point: tuple[float, float]) -> str:
    return f"{point[0]:.3f},{point[1]:.3f}"


def dashed_line(
    start: tuple[float, float],
    end: tuple[float, float],
    dash_length: float = 4.0,
    gap_length: float = 3.0,
) -> str:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    unit_x = dx / length
    unit_y = dy / length
    segments = []
    position = 0.0
    while position < length:
        segment_end = min(position + dash_length, length)
        x1 = start[0] + unit_x * position
        y1 = start[1] + unit_y * position
        x2 = start[0] + unit_x * segment_end
        y2 = start[1] + unit_y * segment_end
        segments.append(
            f'<line x1="{x1:.3f}" y1="{y1:.3f}" '
            f'x2="{x2:.3f}" y2="{y2:.3f}" '
            'stroke="#ef3b24" stroke-width="0.9"/>'
        )
        position += dash_length + gap_length
    return "".join(segments)


def build_overlay(
    elbow: tuple[float, float],
    wrist: tuple[float, float],
    ruler_elbow: tuple[float, float],
    ruler_wrist: tuple[float, float],
    elbow_boundary: tuple[tuple[float, float], tuple[float, float]],
    wrist_boundary: tuple[tuple[float, float], tuple[float, float]],
) -> str:
    dx = ruler_elbow[0] - ruler_wrist[0]
    dy = ruler_elbow[1] - ruler_wrist[1]
    length = math.hypot(dx, dy)
    perpendicular = (-dy / length, dx / length)

    tick_elements = []
    for cun in range(13):
        point = point_at_cun(ruler_wrist, ruler_elbow, cun)
        major = cun in {0, 3, 6, 9, 12}
        half_length = 3.2 if major else 1.8
        start = (
            point[0] - perpendicular[0] * half_length,
            point[1] - perpendicular[1] * half_length,
        )
        end = (
            point[0] + perpendicular[0] * half_length,
            point[1] + perpendicular[1] * half_length,
        )
        tick_elements.append(
            f'<line x1="{start[0]:.3f}" y1="{start[1]:.3f}" '
            f'x2="{end[0]:.3f}" y2="{end[1]:.3f}" '
            f'stroke="#008fb3" stroke-width="{0.85 if major else 0.55}"/>'
        )
        if major and cun not in {0, 12}:
            label = (
                point[0] - perpendicular[0] * 8.0,
                point[1] - perpendicular[1] * 8.0,
            )
            tick_elements.append(
                f'<text x="{label[0]:.3f}" y="{label[1] + 1.6:.3f}" '
                'font-family="Arial, sans-serif" font-size="4.5" '
                'font-weight="700" text-anchor="middle" fill="#006b86">'
                f"{cun}</text>"
            )

    elbow_label = (
        elbow_boundary[0][0] + 3.0,
        elbow_boundary[0][1] - 3.0,
    )
    wrist_label = (
        wrist_boundary[0][0] - 3.0,
        wrist_boundary[0][1] - 3.0,
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
  {dashed_line(elbow_boundary[0], elbow_boundary[1])}
  {dashed_line(wrist_boundary[0], wrist_boundary[1])}
  <line x1="{ruler_wrist[0]:.3f}" y1="{ruler_wrist[1]:.3f}"
      x2="{ruler_elbow[0]:.3f}" y2="{ruler_elbow[1]:.3f}"
      stroke="#008fb3" stroke-width="1.15"
      marker-start="url(#calibration-arrow-start)"
      marker-end="url(#calibration-arrow)"/>
  {''.join(tick_elements)}
  <text x="{elbow_label[0]:.3f}" y="{elbow_label[1]:.3f}"
      font-family="STHeiti, PingFang TC, sans-serif" font-size="4.2"
      font-weight="700" fill="#9f2517">肘橫紋</text>
  <text x="{wrist_label[0]:.3f}" y="{wrist_label[1]:.3f}"
      font-family="STHeiti, PingFang TC, sans-serif" font-size="4.2"
      font-weight="700" text-anchor="end" fill="#9f2517">腕橫紋</text>
  <text x="{(ruler_wrist[0] + ruler_elbow[0]) / 2 + 10:.3f}"
      y="{(ruler_wrist[1] + ruler_elbow[1]) / 2:.3f}"
      font-family="STHeiti, PingFang TC, sans-serif" font-size="5"
      font-weight="700" fill="#006b86">12 寸</text>
  <text x="{SOURCE_VIEWBOX[0] + SOURCE_VIEWBOX[2] / 2:.3f}"
      y="{SOURCE_VIEWBOX[1] + SOURCE_VIEWBOX[3] + 9:.3f}"
      font-family="STHeiti, PingFang TC, sans-serif" font-size="3.7"
      font-weight="500" text-anchor="middle" fill="#655b54">
      定位點｜肘橫紋--腕橫紋，12 寸</text>
</g>
"""


def main() -> None:
    CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
    screen_size = Image.open(MARKUP_PATH).size
    base_size = Image.open(BASE_PNG_PATH).size
    lines = fit_markup_lines()

    elbow_screen = line_intersection(
        lines["elbow_boundary"],
        lines["dimension_axis"],
        AXIS_INWARD_SHIFT_SCREEN_PX,
    )
    wrist_screen = line_intersection(
        lines["wrist_boundary"],
        lines["dimension_axis"],
        AXIS_INWARD_SHIFT_SCREEN_PX,
    )
    elbow_pixel = screen_to_base_pixel(elbow_screen, screen_size, base_size)
    wrist_pixel = screen_to_base_pixel(wrist_screen, screen_size, base_size)
    elbow_svg = base_pixel_to_svg(elbow_pixel)
    wrist_svg = base_pixel_to_svg(wrist_pixel)

    ruler_elbow_screen = line_intersection(
        lines["elbow_boundary"],
        lines["dimension_axis"],
        0.0,
    )
    ruler_wrist_screen = line_intersection(
        lines["wrist_boundary"],
        lines["dimension_axis"],
        0.0,
    )
    ruler_elbow_svg = base_pixel_to_svg(
        screen_to_base_pixel(ruler_elbow_screen, screen_size, base_size)
    )
    ruler_wrist_svg = base_pixel_to_svg(
        screen_to_base_pixel(ruler_wrist_screen, screen_size, base_size)
    )

    elbow_boundary = boundary_segment(
        lines["elbow_boundary"],
        lines["dimension_axis"],
        screen_size,
        base_size,
    )
    wrist_boundary = boundary_segment(
        lines["wrist_boundary"],
        lines["dimension_axis"],
        screen_size,
        base_size,
    )

    base_svg = BASE_SVG_PATH.read_text()
    base_svg = re.sub(
        r'width="\d+" height="\d+" viewBox="[^"]+"',
        f'width="{OUTPUT_VIEWBOX[2]:.0f}" height="{OUTPUT_VIEWBOX[3]:.0f}" '
        f'viewBox="{OUTPUT_VIEWBOX[0]} {OUTPUT_VIEWBOX[1]} '
        f'{OUTPUT_VIEWBOX[2]} {OUTPUT_VIEWBOX[3]}"',
        base_svg,
        count=1,
    )
    overlay = build_overlay(
        elbow_svg,
        wrist_svg,
        ruler_elbow_svg,
        ruler_wrist_svg,
        elbow_boundary,
        wrist_boundary,
    )
    output_svg = re.sub(r"</svg>\s*$", overlay + "</svg>", base_svg)
    svg_path = OUTPUT_STEM.with_suffix(".svg")
    png_path = OUTPUT_STEM.with_suffix(".png")
    svg_path.write_text(output_svg)

    rendered = fitz.open(svg_path)
    rendered[0].get_pixmap(
        matrix=fitz.Matrix(RENDER_SCALE, RENDER_SCALE),
        alpha=False,
    ).save(png_path)

    points = {
        str(cun): {
            "pixel": [
                round(value, 3)
                for value in point_at_cun(wrist_pixel, elbow_pixel, cun)
            ],
            "svg": [
                round(value, 3)
                for value in point_at_cun(wrist_svg, elbow_svg, cun)
            ],
        }
        for cun in range(13)
    }
    DATA_PATH.write_text(
        json.dumps(
            {
                "version": 1,
                "status": "awaiting_anatomy_review",
                "base_image": str(BASE_PNG_PATH),
                "markup_reference": str(MARKUP_PATH),
                "coordinate_system": {
                    "pixel_size": list(base_size),
                    "svg_viewbox": list(SOURCE_VIEWBOX),
                    "output_svg_viewbox": list(OUTPUT_VIEWBOX),
                },
                "bone_proportion": {
                    "region": "anterior_forearm",
                    "origin": "palmar_wrist_crease",
                    "origin_display_name": "腕橫紋",
                    "origin_cun": 0,
                    "end": "cubital_crease",
                    "end_cun": 12,
                    "axis": {
                        "wrist_pixel": [round(value, 3) for value in wrist_pixel],
                        "elbow_pixel": [round(value, 3) for value in elbow_pixel],
                    },
                    "display_ruler": {
                        "placement": "outside_anatomy_right",
                        "wrist_svg": [
                            round(ruler_wrist_svg[0], 3),
                            round(ruler_wrist_svg[1], 3),
                        ],
                        "elbow_svg": [
                            round(ruler_elbow_svg[0], 3),
                            round(ruler_elbow_svg[1], 3),
                        ],
                        "extent_defined_by": [
                            "palmar_wrist_crease",
                            "cubital_crease"
                        ],
                        "endpoint_connector_lines": False,
                    },
                    "formula": "P(cun) = wrist + (cun / 12) * (elbow - wrist)",
                    "points": points,
                },
                "display_policy": {
                    "ruler_must_not_overlap_anatomy": True,
                    "ruler_default_placement": "outside_anatomy",
                    "point_to_ruler_connector": {
                        "style": "dashed",
                        "purpose": "show proportional correspondence only",
                    },
                    "anatomical_point_position_has_priority": True,
                    "boundary_endpoints": {
                        "alignment": "parallel_to_anatomical_axis",
                        "left_axis_shift_screen_px": BOUNDARY_LEFT_AXIS_SHIFT_SCREEN_PX,
                        "right_axis_shift_screen_px": BOUNDARY_RIGHT_AXIS_SHIFT_SCREEN_PX,
                        "alignment_guides_visible": False,
                    },
                },
                "detected_markup_lines": {
                    name: {
                        "equation": (
                            "y = m*x + b"
                            if name != "dimension_axis"
                            else "x = m*y + b"
                        ),
                        "m": round(values[0], 8),
                        "b": round(values[1], 8),
                    }
                    for name, values in lines.items()
                },
                "axis_inward_shift_screen_px": AXIS_INWARD_SHIFT_SCREEN_PX,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(f"Calibration SVG: {svg_path}")
    print(f"Calibration PNG: {png_path}")
    print(f"Calibration data: {DATA_PATH}")


if __name__ == "__main__":
    main()
