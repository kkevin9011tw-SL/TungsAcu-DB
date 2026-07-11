#!/usr/bin/env python3
"""Build the formal evaluation plate for Xinchang point (11.19)."""

import json
import math
import subprocess
import tempfile
from pathlib import Path


HERE = Path(__file__).parent
BASE_SVG = HERE.parent / "poc-muxue-20260612" / "who_palm_pc8_clean.svg"

OUTPUT_SVG = HERE / "心常穴_正式評估版_v1_WHO左手掌面.svg"
OUTPUT_PNG = HERE / "心常穴_正式評估版_v1_WHO左手掌面.png"
OUTPUT_JSON = HERE / "心常穴_定位資料_v1.json"

CANVAS_W = 1400
CANVAS_H = 1200

# Middle-finger proximal segment in the WHO source SVG coordinate system.
# A/E follow the local skin margins; C is the centre line. D is generated as
# the midpoint between C and E, then used as the bone-adjacent point line.
A_TOP = (383.5, 478.0)
A_BOTTOM = (389.0, 517.0)
E_TOP = (410.0, 478.0)
E_BOTTOM = (414.0, 517.0)
C_TOP = ((A_TOP[0] + E_TOP[0]) / 2, (A_TOP[1] + E_TOP[1]) / 2)
C_BOTTOM = (
    (A_BOTTOM[0] + E_BOTTOM[0]) / 2,
    (A_BOTTOM[1] + E_BOTTOM[1]) / 2,
)
D_TOP = ((C_TOP[0] + E_TOP[0]) / 2, (C_TOP[1] + E_TOP[1]) / 2)
D_BOTTOM = (
    (C_BOTTOM[0] + E_BOTTOM[0]) / 2,
    (C_BOTTOM[1] + E_BOTTOM[1]) / 2,
)

MAIN_SCALE = 3.65
MAIN_ORIGIN = (62.0, 162.0)

INSET_SCALE = 10.5
INSET_CX = 1035.0
INSET_CY = 515.0
INSET_R = 285.0
INSET_FOCUS = (
    (D_TOP[0] + D_BOTTOM[0]) / 2,
    (D_TOP[1] + D_BOTTOM[1]) / 2,
)

INK = "#2C1C10"
MUTED = "#75695F"
GOLD = "#C4933A"
VERMILLION = "#7B2D1E"
RED = "#B3261E"
BLUE = "#008CB4"
PAPER = "#FBF6EA"


def add(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return a[0] + b[0], a[1] + b[1]


def sub(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return a[0] - b[0], a[1] - b[1]


def mul(v: tuple[float, float], scalar: float) -> tuple[float, float]:
    return v[0] * scalar, v[1] * scalar


def point_at_fraction(
    start: tuple[float, float],
    end: tuple[float, float],
    fraction: float,
) -> tuple[float, float]:
    return (
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction,
    )


POINTS = (
    point_at_fraction(D_TOP, D_BOTTOM, 1 / 3),
    point_at_fraction(D_TOP, D_BOTTOM, 2 / 3),
)


def main_map(point: tuple[float, float]) -> tuple[float, float]:
    return (
        (point[0] - 318.0) * MAIN_SCALE + MAIN_ORIGIN[0],
        (point[1] - 421.0) * MAIN_SCALE + MAIN_ORIGIN[1],
    )


def inset_map(point: tuple[float, float]) -> tuple[float, float]:
    return (
        (point[0] - INSET_FOCUS[0]) * INSET_SCALE + INSET_CX,
        (point[1] - INSET_FOCUS[1]) * INSET_SCALE + INSET_CY,
    )


def base_body() -> str:
    svg = BASE_SVG.read_text()
    return svg.split("</defs>", 1)[1].rsplit("</svg>", 1)[0]


def embed(
    body: str,
    focus: tuple[float, float],
    scale: float,
    anchor: tuple[float, float],
    clip_id: str,
) -> str:
    tx = anchor[0] - focus[0] * scale
    ty = anchor[1] - focus[1] * scale
    return (
        f"<g clip-path='url(#{clip_id})'>"
        f"<g transform='translate({tx:.3f},{ty:.3f}) scale({scale})'>"
        f"{body}</g></g>"
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
        f"<text {common} fill='none' stroke='{PAPER}' stroke-width='5' "
        f"stroke-linejoin='round'>{text}</text>"
        f"<text {common} fill='{colour}'>{text}</text>"
    )


def mapped_line(
    mapper,
    start: tuple[float, float],
    end: tuple[float, float],
    colour: str,
    width: float,
    opacity: float = 1.0,
    dash: str | None = None,
) -> str:
    x1, y1 = mapper(start)
    x2, y2 = mapper(end)
    dash_attr = f" stroke-dasharray='{dash}'" if dash else ""
    return (
        f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
        f"stroke='{colour}' stroke-width='{width}' stroke-opacity='{opacity}'"
        f"{dash_attr}/>"
    )


def main_annotations() -> str:
    parts = ["<g id='main-annotations'>"]
    for point in POINTS:
        x, y = main_map(point)
        parts.append(
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='7.5' fill='{RED}' "
            "stroke='#FFFFFF' stroke-width='2.2'/>"
        )

    segment_mid = point_at_fraction(D_TOP, D_BOTTOM, 0.5)
    cx, cy = main_map(segment_mid)
    d_vector = sub(D_BOTTOM, D_TOP)
    angle = math.degrees(math.atan2(d_vector[1], d_vector[0])) - 90
    parts.append(
        f"<ellipse cx='{cx:.1f}' cy='{cy:.1f}' rx='62' ry='82' "
        f"transform='rotate({angle:.2f} {cx:.1f} {cy:.1f})' "
        f"fill='none' stroke='{GOLD}' stroke-width='2' stroke-dasharray='8 6'/>"
    )
    parts.append(
        f"<line x1='{cx + 52:.1f}' y1='{cy - 58:.1f}' "
        f"x2='{INSET_CX - 250:.1f}' y2='{INSET_CY - 142:.1f}' "
        f"stroke='{GOLD}' stroke-width='1.5' stroke-opacity='.72'/>"
    )
    parts.append(
        f"<line x1='{cx + 52:.1f}' y1='{cy + 58:.1f}' "
        f"x2='{INSET_CX - 250:.1f}' y2='{INSET_CY + 142:.1f}' "
        f"stroke='{GOLD}' stroke-width='1.5' stroke-opacity='.72'/>"
    )
    parts.append("</g>")
    return "".join(parts)


def inset_annotations() -> str:
    parts = ["<g id='inset-annotations'>"]

    # PIP and MCP boundaries span the complete proximal segment.
    for start, end in ((A_TOP, E_TOP), (A_BOTTOM, E_BOTTOM)):
        vector = sub(end, start)
        extension = mul(vector, 0.16)
        parts.append(
            mapped_line(
                inset_map,
                sub(start, extension),
                add(end, extension),
                INK,
                1.8,
                0.72,
                "7 5",
            )
        )

    # Show the centre, calculated D line, and ulnar skin margin.
    for name, top, bottom, colour, width in (
        ("C", C_TOP, C_BOTTOM, BLUE, 1.6),
        ("D", D_TOP, D_BOTTOM, RED, 2.2),
        ("E", E_TOP, E_BOTTOM, BLUE, 1.6),
    ):
        vector = sub(bottom, top)
        start = add(top, mul(vector, -0.12))
        end = add(bottom, mul(vector, 0.12))
        parts.append(
            mapped_line(inset_map, start, end, colour, width, 0.78)
        )
        label_point = add(top, mul(vector, -0.17))
        lx, ly = inset_map(label_point)
        parts.append(
            halo_text(
                lx,
                ly - 8,
                16,
                VERMILLION if name == "D" else "#006F90",
                f"{name} 線",
                "middle",
            )
        )

    d_vector = sub(D_BOTTOM, D_TOP)
    d_length = math.hypot(*d_vector)
    axis = (d_vector[0] / d_length, d_vector[1] / d_length)
    cross = (axis[1], -axis[0])
    bracket_offset = 8.0
    bracket_start = add(D_TOP, mul(cross, bracket_offset))
    bracket_end = add(D_BOTTOM, mul(cross, bracket_offset))
    parts.append(
        mapped_line(inset_map, bracket_start, bracket_end, INK, 1.6)
    )
    for fraction in (0, 1 / 3, 2 / 3, 1):
        centre = add(
            point_at_fraction(D_TOP, D_BOTTOM, fraction),
            mul(cross, bracket_offset),
        )
        parts.append(
            mapped_line(
                inset_map,
                add(centre, mul(cross, -0.7)),
                add(centre, mul(cross, 0.7)),
                INK,
                1.6,
            )
        )

    label_point = add(
        point_at_fraction(D_TOP, D_BOTTOM, 0.5),
        mul(cross, 10.5),
    )
    lx, ly = inset_map(label_point)
    parts.append(halo_text(lx + 10, ly + 4, 17, INK, "三分點法"))

    for point in POINTS:
        x, y = inset_map(point)
        parts.append(
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='10.5' fill='{RED}' "
            "stroke='#FFFFFF' stroke-width='3'/>"
        )

    parts.append("</g>")
    return "".join(parts)


def labels() -> str:
    return f"""
    <g id='labels'>
      <rect x='30' y='26' width='76' height='36' fill='{VERMILLION}'/>
      <text x='68' y='51' font-size='18' fill='#F7EDD8' text-anchor='middle'
        font-family='Noto Sans TC, sans-serif'>11.19</text>
      <text x='124' y='55' font-size='31' font-weight='700' fill='{INK}'
        font-family='Noto Serif TC, serif'>心常穴</text>
      <text x='30' y='91' font-size='14' fill='{MUTED}'
        font-family='Noto Sans TC, sans-serif'>正式評估版｜左手掌面・骨骼透視</text>

      <rect x='45' y='128' width='330' height='82' rx='7' fill='#FFFDF6'
        stroke='{GOLD}' stroke-width='1.7'/>
      <text x='210' y='161' font-size='24' font-weight='700' fill='{VERMILLION}'
        text-anchor='middle' font-family='Noto Serif TC, serif'>心常穴（二穴）</text>
      <text x='210' y='188' font-size='14.5' fill='{INK}' fill-opacity='.82'
        text-anchor='middle' font-family='Noto Sans TC, sans-serif'>中指第一節 D 線・三分點法</text>

      <text x='{INSET_CX}' y='188' font-size='19' font-weight='700' fill='{INK}'
        text-anchor='middle' font-family='Noto Sans TC, sans-serif'>中指第一節放大</text>

      <rect x='805' y='850' width='520' height='145' rx='9'
        fill='#FFFDF6' stroke='{GOLD}' stroke-width='1.7'/>
      <text x='840' y='892' font-size='19' font-weight='700' fill='{VERMILLION}'
        font-family='Noto Sans TC, sans-serif'>定位規則</text>
      <text x='840' y='928' font-size='16' fill='{INK}'
        font-family='Noto Sans TC, sans-serif'>D 線＝C 線與尺側 E 線的中點線</text>
      <text x='840' y='962' font-size='16' fill='{INK}'
        font-family='Noto Sans TC, sans-serif'>穴點依 D 線定位，實際取穴貼近指骨旁</text>

      <text x='30' y='1176' font-size='12' fill='{INK}' fill-opacity='.55'
        font-family='Noto Sans TC, sans-serif'>底圖｜WHO Standard Acupuncture Point Locations
        in the Western Pacific Region (2008), p.164　定位參考｜原書心常穴圖　標註｜TungsAcu-DB</text>
    </g>
    """


def build() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    body = base_body()
    x0, y0 = main_map((318, 421))
    x1, y1 = main_map((474, 660))
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg'
      xmlns:xlink='http://www.w3.org/1999/xlink'
      viewBox='0 0 {CANVAS_W} {CANVAS_H}'>
      <defs>
        <clipPath id='main-clip'>
          <rect x='{x0:.1f}' y='{y0:.1f}' width='{x1 - x0:.1f}' height='{y1 - y0:.1f}'/>
        </clipPath>
        <clipPath id='inset-clip'>
          <circle cx='{INSET_CX}' cy='{INSET_CY}' r='{INSET_R}'/>
        </clipPath>
      </defs>
      <rect width='{CANVAS_W}' height='{CANVAS_H}' fill='{PAPER}'/>
      {embed(body, (318, 421), MAIN_SCALE, MAIN_ORIGIN, "main-clip")}
      {main_annotations()}
      <circle cx='{INSET_CX}' cy='{INSET_CY}' r='{INSET_R}'
        fill='#FFFFFF' stroke='{GOLD}' stroke-width='2.5'/>
      {embed(body, INSET_FOCUS, INSET_SCALE, (INSET_CX, INSET_CY), "inset-clip")}
      <circle cx='{INSET_CX}' cy='{INSET_CY}' r='{INSET_R}'
        fill='none' stroke='{GOLD}' stroke-width='2.5'/>
      {inset_annotations()}
      {labels()}
    </svg>"""

    OUTPUT_SVG.write_text(svg)
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(
            [
                "qlmanage",
                "-t",
                "-s",
                str(CANVAS_W * 2),
                "-o",
                temp_dir,
                str(OUTPUT_SVG),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        thumbnail = Path(temp_dir) / f"{OUTPUT_SVG.name}.png"
        subprocess.run(
            [
                "sips",
                "-c",
                str(CANVAS_H * 2),
                str(CANVAS_W * 2),
                str(thumbnail),
                "--out",
                str(OUTPUT_PNG),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )

    OUTPUT_JSON.write_text(
        json.dumps(
            {
                "version": 1,
                "status": "awaiting_user_review",
                "point": "心常穴",
                "code": "11.19",
                "view": "left_palm",
                "segment": "middle_finger_proximal_segment",
                "lines_svg": {
                    "A": {"top": A_TOP, "bottom": A_BOTTOM},
                    "C": {"top": C_TOP, "bottom": C_BOTTOM},
                    "D": {"top": D_TOP, "bottom": D_BOTTOM},
                    "E": {"top": E_TOP, "bottom": E_BOTTOM},
                },
                "construction": {
                    "C": "local centre line between A and E",
                    "D": "midpoint line between C and E",
                    "point_placement": (
                        "Use D-line geometry; clinical point remains "
                        "bone-adjacent on the ulnar side."
                    ),
                    "longitudinal_method": "three-part method",
                },
                "points_svg": [
                    [round(value, 4) for value in point] for point in POINTS
                ],
                "future_edge_point_policy": {
                    "yin_palm": ["A", "E"],
                    "yang_palm": ["A", "C"],
                    "inset_view": "lateral",
                    "point_position": "inferior bone margin",
                },
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
    print(f"Points: {POINTS}")


if __name__ == "__main__":
    build()
