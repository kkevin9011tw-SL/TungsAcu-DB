#!/usr/bin/env python3
"""Build a Mu point (11.17) diagram from the cleaned WHO palmar hand."""

from pathlib import Path


HERE = Path(__file__).parent

CANVAS_W = 1200
CANVAS_H = 1200

# Clean WHO base coordinates after the vertical flip.
PIP = (355.0, 491.0)
MCP = (365.0, 541.0)
ULNAR_OFFSET = 5.0

MAIN_SCALE = 3.35
MAIN_TX = 80
MAIN_TY = 170

INSET_SCALE = 9.0
INSET_CX = 875
INSET_CY = 505
INSET_R = 250
INSET_FOCUS = (360.0, 516.0)

INK = "#2C1C10"
GOLD = "#C4933A"
VERMILLION = "#7B2D1E"
RED = "#B3261E"
PAPER = "#FBF6EA"


def point_on_axis(t: float) -> tuple[float, float]:
    return (
        PIP[0] + t * (MCP[0] - PIP[0]),
        PIP[1] + t * (MCP[1] - PIP[1]),
    )


def mu_point(t: float) -> tuple[float, float]:
    x, y = point_on_axis(t)
    return x + ULNAR_OFFSET, y


POINTS = (mu_point(1 / 3), mu_point(2 / 3))


def main_map(point: tuple[float, float]) -> tuple[float, float]:
    x, y = point
    return (
        (x - 318) * MAIN_SCALE + MAIN_TX,
        (y - 421) * MAIN_SCALE + MAIN_TY,
    )


def inset_map(point: tuple[float, float]) -> tuple[float, float]:
    x, y = point
    return (
        (x - INSET_FOCUS[0]) * INSET_SCALE + INSET_CX,
        (y - INSET_FOCUS[1]) * INSET_SCALE + INSET_CY,
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
        f"<g transform='translate({tx:.2f},{ty:.2f}) scale({scale})'>"
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


def main_annotations() -> str:
    parts = ["<g id='main-annotations'>"]
    for point in POINTS:
        x, y = main_map(point)
        parts.append(
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='7' fill='{RED}' "
            "stroke='#FFFFFF' stroke-width='2'/>"
        )

    cx, cy = main_map(INSET_FOCUS)
    parts.append(
        f"<ellipse cx='{cx:.1f}' cy='{cy:.1f}' rx='73' ry='105' fill='none' "
        f"stroke='{GOLD}' stroke-width='2' stroke-dasharray='8 6'/>"
    )
    parts.append(
        f"<line x1='{cx + 55:.1f}' y1='{cy - 70:.1f}' "
        f"x2='{INSET_CX - 218}' y2='{INSET_CY - 122}' "
        f"stroke='{GOLD}' stroke-width='1.5' stroke-opacity='.75'/>"
    )
    parts.append(
        f"<line x1='{cx + 55:.1f}' y1='{cy + 70:.1f}' "
        f"x2='{INSET_CX - 218}' y2='{INSET_CY + 122}' "
        f"stroke='{GOLD}' stroke-width='1.5' stroke-opacity='.75'/>"
    )
    parts.append("</g>")
    return "".join(parts)


def inset_annotations() -> str:
    parts = ["<g id='inset-annotations'>"]

    # Proximal interphalangeal and metacarpophalangeal creases.
    for joint, label in ((PIP, "近端指節橫紋"), (MCP, "掌指橫紋")):
        x1, y = inset_map((joint[0] - 14, joint[1]))
        x2, _ = inset_map((joint[0] + 15, joint[1]))
        parts.append(
            f"<line x1='{x1:.1f}' y1='{y:.1f}' x2='{x2:.1f}' y2='{y:.1f}' "
            f"stroke='{INK}' stroke-width='1.8' stroke-dasharray='7 5' "
            "stroke-opacity='.75'/>"
        )
        parts.append(halo_text(x1 - 10, y + 6, 16, INK, label, "end"))

    # Finger centre line and the D line, offset two fen toward the middle finger.
    c0 = inset_map(point_on_axis(-0.08))
    c1 = inset_map(point_on_axis(1.08))
    d0 = inset_map(mu_point(-0.08))
    d1 = inset_map(mu_point(1.08))
    parts.append(
        f"<line x1='{c0[0]:.1f}' y1='{c0[1]:.1f}' "
        f"x2='{c1[0]:.1f}' y2='{c1[1]:.1f}' stroke='{GOLD}' "
        "stroke-width='2' stroke-dasharray='9 6'/>"
    )
    parts.append(
        f"<line x1='{d0[0]:.1f}' y1='{d0[1]:.1f}' "
        f"x2='{d1[0]:.1f}' y2='{d1[1]:.1f}' stroke='{RED}' "
        "stroke-width='1.6' stroke-opacity='.5'/>"
    )
    parts.append(halo_text(c0[0] - 8, c0[1] - 8, 16, "#8A6420", "中央線", "end", 700))

    # Two-fen offset dimension.
    axis = inset_map(point_on_axis(-0.04))
    dline = inset_map(mu_point(-0.04))
    dim_y = axis[1] - 10
    parts.append(
        f"<line x1='{axis[0]:.1f}' y1='{dim_y:.1f}' "
        f"x2='{dline[0]:.1f}' y2='{dim_y:.1f}' stroke='{INK}' stroke-width='1.4'/>"
        f"<line x1='{axis[0]:.1f}' y1='{dim_y - 6:.1f}' "
        f"x2='{axis[0]:.1f}' y2='{dim_y + 6:.1f}' stroke='{INK}' stroke-width='1.4'/>"
        f"<line x1='{dline[0]:.1f}' y1='{dim_y - 6:.1f}' "
        f"x2='{dline[0]:.1f}' y2='{dim_y + 6:.1f}' stroke='{INK}' stroke-width='1.4'/>"
    )
    parts.append(
        halo_text((axis[0] + dline[0]) / 2, dim_y - 10, 15, INK, "二分", "middle")
    )

    # Three-part bracket.
    bracket_x = inset_map((MCP[0] + 19, MCP[1]))[0]
    top_y = inset_map(PIP)[1]
    bottom_y = inset_map(MCP)[1]
    parts.append(
        f"<line x1='{bracket_x:.1f}' y1='{top_y:.1f}' "
        f"x2='{bracket_x:.1f}' y2='{bottom_y:.1f}' "
        f"stroke='{INK}' stroke-width='1.5'/>"
    )
    for t in (0, 1 / 3, 2 / 3, 1):
        y = top_y + t * (bottom_y - top_y)
        tick = 10 if t in (0, 1) else 7
        parts.append(
            f"<line x1='{bracket_x - tick:.1f}' y1='{y:.1f}' "
            f"x2='{bracket_x + tick:.1f}' y2='{y:.1f}' "
            f"stroke='{INK}' stroke-width='1.5'/>"
        )
    parts.append(
        halo_text(bracket_x - 18, (top_y + bottom_y) / 2 - 7, 17, INK, "三分點法", "end", 700)
    )
    parts.append(
        halo_text(bracket_x - 18, (top_y + bottom_y) / 2 + 17, 14, INK, "取 1/3、2/3 兩點", "end")
    )

    for label, point in zip(("上穴", "下穴"), POINTS):
        x, y = inset_map(point)
        parts.append(
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='10' fill='{RED}' "
            "stroke='#FFFFFF' stroke-width='3'/>"
        )
        parts.append(
            halo_text(x - 18, y + 5, 15, VERMILLION, label, "end", 700)
        )

    parts.append("</g>")
    return "".join(parts)


def labels() -> str:
    return f"""
    <g id='labels'>
      <rect x='28' y='24' width='70' height='34' fill='{VERMILLION}'/>
      <text x='63' y='47' font-size='17' fill='#F7EDD8' text-anchor='middle'
        font-family='Noto Sans TC, sans-serif'>11.17</text>
      <text x='112' y='51' font-size='29' font-weight='700' fill='{INK}'
        font-family='Noto Serif TC, serif'>木穴</text>
      <text x='28' y='84' font-size='14' fill='{INK}' fill-opacity='.65'
        font-family='Noto Sans TC, sans-serif'>WHO 掌面線稿重製｜右手掌面・骨骼透視</text>

      <rect x='44' y='126' width='260' height='76' rx='7' fill='#FFFDF6'
        stroke='{GOLD}' stroke-width='1.7'/>
      <text x='174' y='158' font-size='23' font-weight='700' fill='{VERMILLION}'
        text-anchor='middle' font-family='Noto Serif TC, serif'>木穴（二穴）</text>
      <text x='174' y='184' font-size='14.5' fill='{INK}' fill-opacity='.82'
        text-anchor='middle' font-family='Noto Sans TC, sans-serif'>食指第一節 D 線・三分點法</text>

      <text x='{INSET_CX}' y='196' font-size='18' font-weight='700' fill='{INK}'
        text-anchor='middle' font-family='Noto Sans TC, sans-serif'>食指第一節（放大）</text>

      <circle cx='890' cy='1084' r='7' fill='{RED}' stroke='#FFFFFF' stroke-width='2'/>
      <text x='910' y='1090' font-size='14' fill='{INK}'
        font-family='Noto Sans TC, sans-serif'>木穴點</text>
      <line x1='878' y1='1114' x2='902' y2='1114' stroke='{GOLD}'
        stroke-width='2' stroke-dasharray='8 5'/>
      <text x='910' y='1120' font-size='14' fill='{INK}'
        font-family='Noto Sans TC, sans-serif'>中央線</text>
      <rect x='878' y='1138' width='24' height='15' fill='#E6E7E8'
        stroke='#6D6E71' stroke-width='1.2'/>
      <text x='910' y='1151' font-size='14' fill='{INK}'
        font-family='Noto Sans TC, sans-serif'>骨骼透視</text>

      <text x='28' y='1175' font-size='12' fill='{INK}' fill-opacity='.55'
        font-family='Noto Sans TC, sans-serif'>底圖｜WHO Standard Acupuncture Point Locations
        in the Western Pacific Region (2008), p.164　標註｜TungsAcu-DB</text>
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
      {embed(body, (318, 421), MAIN_SCALE, (MAIN_TX, MAIN_TY), "main-clip")}
      {main_annotations()}
      <circle cx='{INSET_CX}' cy='{INSET_CY}' r='{INSET_R}'
        fill='#FFFFFF' stroke='{GOLD}' stroke-width='2.4'/>
      {embed(body, INSET_FOCUS, INSET_SCALE, (INSET_CX, INSET_CY), "inset-clip")}
      <circle cx='{INSET_CX}' cy='{INSET_CY}' r='{INSET_R}'
        fill='none' stroke='{GOLD}' stroke-width='2.4'/>
      {inset_annotations()}
      {labels()}
    </svg>"""

    output = HERE / "木穴_C版_WHO掌面線稿.svg"
    output.write_text(svg)
    print(f"Produced: {output}")


if __name__ == "__main__":
    build()
