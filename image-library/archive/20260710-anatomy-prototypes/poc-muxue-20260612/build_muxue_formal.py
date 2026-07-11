#!/usr/bin/env python3
"""Build the user-calibrated evaluation plate for Mu point (11.17).

The longitudinal C/D/E lines and both finger-segment boundaries are measured
directly from the user's annotations on the 2800 x 2400 v2 PNG. Coordinates
below are converted back into the WHO vector coordinate system.
"""

import math
from pathlib import Path


HERE = Path(__file__).parent

CANVAS_W = 1400
CANVAS_H = 1200

# Intersections of the annotated C/D/E lines with the annotated upper and
# lower finger-segment boundaries.
C_TOP = (366.5711, 476.2240)
C_BOTTOM = (376.1057, 506.7052)
D_TOP = (371.2858, 474.4552)
D_BOTTOM = (380.7905, 504.8628)
E_TOP = (375.3101, 472.9454)
E_BOTTOM = (384.8011, 503.2855)

DX = D_BOTTOM[0] - D_TOP[0]
DY = D_BOTTOM[1] - D_TOP[1]
SEGMENT_LENGTH = math.hypot(DX, DY)
AXIS = (DX / SEGMENT_LENGTH, DY / SEGMENT_LENGTH)
CROSS = (AXIS[1], -AXIS[0])

MAIN_SCALE = 3.65
MAIN_ORIGIN = (62.0, 162.0)

INSET_SCALE = 11.8
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
PAPER = "#FBF6EA"


def add(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return a[0] + b[0], a[1] + b[1]


def mul(v: tuple[float, float], scalar: float) -> tuple[float, float]:
    return v[0] * scalar, v[1] * scalar


def axis_point(t: float) -> tuple[float, float]:
    return D_TOP[0] + DX * t, D_TOP[1] + DY * t


def d_point(t: float) -> tuple[float, float]:
    return axis_point(t)


POINTS = (d_point(1 / 3), d_point(2 / 3))


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
    svg = (HERE / "who_palm_pc8_clean.svg").read_text()
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
    size: int,
    colour: str,
    text: str,
    anchor: str = "start",
    weight: int | None = None,
) -> str:
    weight_attr = f" font-weight='{weight}'" if weight else ""
    common = (
        f"x='{x:.1f}' y='{y:.1f}' font-size='{size}' text-anchor='{anchor}'"
        f"{weight_attr} font-family='Noto Sans TC, sans-serif'"
    )
    return (
        f"<text {common} fill='none' stroke='{PAPER}' stroke-width='5' "
        f"stroke-linejoin='round'>{text}</text>"
        f"<text {common} fill='{colour}'>{text}</text>"
    )


def mapped_segment(
    mapper,
    start: tuple[float, float],
    end: tuple[float, float],
    **attrs,
) -> str:
    x1, y1 = mapper(start)
    x2, y2 = mapper(end)
    attributes = " ".join(f"{key.replace('_', '-')}='{value}'" for key, value in attrs.items())
    return f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' {attributes}/>"


def main_annotations() -> str:
    parts = ["<g id='main-annotations'>"]
    for point in POINTS:
        x, y = main_map(point)
        parts.append(
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='7.5' fill='{RED}' "
            "stroke='#FFFFFF' stroke-width='2.2'/>"
        )

    segment_mid = axis_point(0.5)
    cx, cy = main_map(segment_mid)
    parts.append(
        f"<ellipse cx='{cx:.1f}' cy='{cy:.1f}' rx='58' ry='72' "
        f"transform='rotate({math.degrees(math.atan2(DY, DX)) - 90:.2f} {cx:.1f} {cy:.1f})' "
        f"fill='none' stroke='{GOLD}' stroke-width='2' stroke-dasharray='8 6'/>"
    )
    parts.append(
        f"<line x1='{cx + 48:.1f}' y1='{cy - 48:.1f}' "
        f"x2='{INSET_CX - 248:.1f}' y2='{INSET_CY - 132:.1f}' "
        f"stroke='{GOLD}' stroke-width='1.5' stroke-opacity='.72'/>"
    )
    parts.append(
        f"<line x1='{cx + 48:.1f}' y1='{cy + 48:.1f}' "
        f"x2='{INSET_CX - 248:.1f}' y2='{INSET_CY + 132:.1f}' "
        f"stroke='{GOLD}' stroke-width='1.5' stroke-opacity='.72'/>"
    )
    parts.append("</g>")
    return "".join(parts)


def inset_annotations() -> str:
    parts = ["<g id='inset-annotations'>"]

    # User-annotated upper and lower segment boundaries.
    for start, end in (
        (add(C_TOP, mul(CROSS, -3.5)), add(E_TOP, mul(CROSS, 3.5))),
        (
            add(C_BOTTOM, mul(CROSS, -3.5)),
            add(E_BOTTOM, mul(CROSS, 3.5)),
        ),
    ):
        parts.append(
            mapped_segment(
                inset_map,
                start,
                end,
                stroke=INK,
                stroke_width="1.8",
                stroke_dasharray="7 5",
                stroke_opacity=".72",
            )
        )

    # C/D/E lines copied from the user's annotations; D is highlighted.
    for name, top, bottom, colour, width in (
        ("C", C_TOP, C_BOTTOM, "#008CB4", "1.6"),
        ("D", D_TOP, D_BOTTOM, RED, "2.1"),
        ("E", E_TOP, E_BOTTOM, "#008CB4", "1.6"),
    ):
        vector = (bottom[0] - top[0], bottom[1] - top[1])
        start = add(top, mul(vector, -0.12))
        end = add(bottom, mul(vector, 0.12))
        parts.append(
            mapped_segment(
                inset_map,
                start,
                end,
                stroke=colour,
                stroke_width=width,
                stroke_opacity=".72",
            )
        )
        label_point = add(top, mul(vector, -0.16))
        lx, ly = inset_map(label_point)
        parts.append(
            halo_text(
                lx,
                ly - 10,
                16,
                VERMILLION if name == "D" else "#006F90",
                f"{name} 線",
                "middle",
                700,
            )
        )

    # Three-part bracket parallel to D and outside E.
    bracket_offset = 7.0
    bracket_start = add(D_TOP, mul(CROSS, bracket_offset))
    bracket_end = add(D_BOTTOM, mul(CROSS, bracket_offset))
    parts.append(
        mapped_segment(
            inset_map,
            bracket_start,
            bracket_end,
            stroke=INK,
            stroke_width="1.6",
        )
    )
    for t in (0, 1 / 3, 2 / 3, 1):
        centre = add(axis_point(t), mul(CROSS, bracket_offset))
        tick_start = add(centre, mul(CROSS, -0.7))
        tick_end = add(centre, mul(CROSS, 0.7))
        parts.append(
            mapped_segment(
                inset_map,
                tick_start,
                tick_end,
                stroke=INK,
                stroke_width="1.6",
            )
        )

    bracket_label = add(axis_point(0.50), mul(CROSS, 9.5))
    bx, by = inset_map(bracket_label)
    parts.append(halo_text(bx + 10, by + 4, 17, INK, "三分點法", "start", 700))

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
        font-family='Noto Sans TC, sans-serif'>11.17</text>
      <text x='124' y='55' font-size='31' font-weight='700' fill='{INK}'
        font-family='Noto Serif TC, serif'>木穴</text>
      <text x='30' y='91' font-size='14' fill='{MUTED}'
        font-family='Noto Sans TC, sans-serif'>WHO 掌面線稿重製｜左手掌面・骨骼透視</text>

      <rect x='45' y='128' width='310' height='82' rx='7' fill='#FFFDF6'
        stroke='{GOLD}' stroke-width='1.7'/>
      <text x='200' y='161' font-size='24' font-weight='700' fill='{VERMILLION}'
        text-anchor='middle' font-family='Noto Serif TC, serif'>木穴（二穴）</text>
      <text x='200' y='188' font-size='14.5' fill='{INK}' fill-opacity='.82'
        text-anchor='middle' font-family='Noto Sans TC, sans-serif'>食指第一節 D 線・三分點法</text>

      <text x='{INSET_CX}' y='188' font-size='19' font-weight='700' fill='{INK}'
        text-anchor='middle' font-family='Noto Sans TC, sans-serif'>食指第一節放大</text>

      <text x='30' y='1176' font-size='12' fill='{INK}' fill-opacity='.55'
        font-family='Noto Sans TC, sans-serif'>底圖｜WHO Standard Acupuncture Point Locations
        in the Western Pacific Region (2008), p.164　定位參考｜原書木穴圖　標註｜TungsAcu-DB</text>
    </g>
    """


def build() -> None:
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

    output = HERE / "木穴_精簡評估版_v4_WHO左手掌面線稿.svg"
    output.write_text(svg)
    print(f"Produced: {output}")


if __name__ == "__main__":
    build()
