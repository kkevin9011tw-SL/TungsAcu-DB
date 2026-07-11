#!/usr/bin/env python3
"""Build straight single-finger templates from the WHO p.168 hand artwork."""

import base64
import json
import math
import re
from collections import deque
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


HERE = Path(__file__).parent
SOURCE_DIR = HERE.parent / "who-standard-bases-20260612"
DORSAL_SOURCE = SOURCE_DIR / "clean-bases" / "02_hand-dorsal.svg"
PALMAR_SOURCE = SOURCE_DIR / "who_palmar_from_dorsal_evaluation.svg"
DORSAL_PNG = SOURCE_DIR / "clean-bases" / "02_hand-dorsal.png"
PALMAR_PNG = SOURCE_DIR / "who_palmar_from_dorsal_evaluation.png"

CANVAS_W = 360
CANVAS_H = 900
SCALE = 8.0
TOP_MARGIN = 58.0
PAPER = "#FFFFFF"
GUIDE = "#C4933A"
INK = "#2C1C10"
SOURCE_X = 322.0
SOURCE_Y = 112.0
SOURCE_W = 170.0
SOURCE_H = 240.0


@dataclass(frozen=True)
class FingerSpec:
    slug: str
    title: str
    tip: tuple[float, float]
    base: tuple[float, float]
    polygon: tuple[tuple[float, float], ...]
    joints: dict[str, tuple[float, float]]
    bone_seeds: tuple[tuple[float, float], ...]


# Coordinates use the cleaned dorsal SVG display system:
# viewBox 322 112 170 240, fingers pointing upward.
FINGERS = (
    FingerSpec(
        "index",
        "食指",
        (444.6, 144.0),
        (428.0, 219.0),
        (
            (435.0, 138.0),
            (454.0, 139.0),
            (465.0, 152.0),
            (463.0, 172.0),
            (456.0, 192.0),
            (450.0, 211.0),
            (440.0, 223.0),
            (424.0, 220.0),
            (424.0, 201.0),
            (431.0, 181.0),
            (436.0, 162.0),
        ),
        {
            "DIP_joint": (440.5, 163.0),
            "PIP_joint": (434.0, 187.0),
            "MCP_joint": (428.0, 218.0),
        },
        ((446.0, 156.0), (441.0, 176.0), (431.0, 200.0)),
    ),
    FingerSpec(
        "middle",
        "中指",
        (421.4, 124.0),
        (404.8, 211.0),
        (
            (410.0, 118.0),
            (431.0, 120.0),
            (434.0, 139.0),
            (430.0, 160.0),
            (423.0, 181.0),
            (418.0, 199.0),
            (417.0, 209.0),
            (407.0, 216.0),
            (394.0, 210.0),
            (398.0, 187.0),
            (403.0, 166.0),
            (408.0, 145.0),
        ),
        {
            "DIP_joint": (416.7, 149.0),
            "PIP_joint": (411.4, 177.0),
            "MCP_joint": (404.8, 210.0),
        },
        ((420.0, 140.0), (414.0, 162.0), (407.0, 195.0)),
    ),
    FingerSpec(
        "ring",
        "無名指",
        (399.6, 131.0),
        (386.0, 211.0),
        (
            (380.0, 123.0),
            (402.0, 125.0),
            (405.0, 143.0),
            (401.0, 159.0),
            (396.0, 178.0),
            (391.0, 195.0),
            (390.0, 209.0),
            (379.0, 216.0),
            (366.0, 210.0),
            (369.0, 187.0),
            (374.0, 167.0),
            (379.0, 148.0),
        ),
        {
            "DIP_joint": (396.4, 150.0),
            "PIP_joint": (392.0, 176.0),
            "MCP_joint": (386.0, 210.0),
        },
        ((398.0, 138.0), (392.0, 162.0), (384.0, 195.0)),
    ),
    FingerSpec(
        "little",
        "小指",
        (359.9, 152.0),
        (360.5, 214.0),
        (
            (346.0, 146.0),
            (366.0, 148.0),
            (370.0, 165.0),
            (368.0, 185.0),
            (370.0, 207.0),
            (365.0, 219.0),
            (347.0, 219.0),
            (342.0, 208.0),
            (344.0, 183.0),
            (344.0, 162.0),
        ),
        {
            "DIP_joint": (360.0, 166.0),
            "PIP_joint": (360.2, 184.0),
            "MCP_joint": (360.5, 213.0),
        },
        ((360.0, 158.0), (360.0, 175.0), (360.0, 199.0)),
    ),
)


def mirror_x(point: tuple[float, float]) -> tuple[float, float]:
    # Palmar source was produced from the dorsal source around x = 407.
    return 814.0 - point[0], point[1]


def transform_values(spec: FingerSpec, view: str) -> tuple[float, float, float]:
    tip = mirror_x(spec.tip) if view == "palmar" else spec.tip
    base = mirror_x(spec.base) if view == "palmar" else spec.base
    dx = base[0] - tip[0]
    dy = base[1] - tip[1]
    angle = math.degrees(math.atan2(dx, dy))
    return tip[0], tip[1], angle


def mapped_point(
    point: tuple[float, float],
    spec: FingerSpec,
    view: str,
) -> tuple[float, float]:
    if view == "palmar":
        point = mirror_x(point)
    tip_x, tip_y, angle = transform_values(spec, view)
    radians = math.radians(angle)
    dx = point[0] - tip_x
    dy = point[1] - tip_y
    rotated_x = math.cos(radians) * dx - math.sin(radians) * dy
    rotated_y = math.sin(radians) * dx + math.cos(radians) * dy
    return (
        CANVAS_W / 2 + rotated_x * SCALE,
        TOP_MARGIN + rotated_y * SCALE,
    )


def source_pixel(
    point: tuple[float, float],
    size: tuple[int, int],
) -> tuple[float, float]:
    return (
        (point[0] - SOURCE_X) / SOURCE_W * size[0],
        (point[1] - SOURCE_Y) / SOURCE_H * size[1],
    )


def build_bones_only_source(
    source_svg: Path,
    output_stem: str,
) -> Path:
    svg = source_svg.read_text()
    defs_end = svg.index("</defs>") + len("</defs>")
    head, body = svg[:defs_end], svg[defs_end:]

    def keep_bone_path(match: re.Match[str]) -> str:
        tag = match.group(0)
        if 'fill="#e6e7e8"' in tag or 'stroke="#6d6e71"' in tag:
            return tag
        return ""

    body = re.sub(r"<path\b[^>]*/>", keep_bone_path, body)
    svg = head + body
    output_svg = HERE / f"{output_stem}.svg"
    output_png = HERE / f"{output_stem}.png"
    output_svg.write_text(svg)
    rendered = fitz.open(output_svg)
    rendered[0].get_pixmap(
        matrix=fitz.Matrix(6, 6),
        alpha=False,
    ).save(output_png)
    return output_png


def connected_fill_component(
    fill_mask,
    seed: tuple[int, int],
):
    height, width = fill_mask.shape
    seed_y, seed_x = seed
    queue = deque([(seed_y, seed_x)])
    component = {(seed_y, seed_x)}
    while queue:
        y, x = queue.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            next_y = y + dy
            next_x = x + dx
            next_point = (next_y, next_x)
            if (
                0 <= next_y < height
                and 0 <= next_x < width
                and fill_mask[next_y, next_x]
                and next_point not in component
            ):
                component.add(next_point)
                queue.append(next_point)
    return component


def isolate_finger_bones(
    source_png: Path,
    spec: FingerSpec,
    view: str,
) -> Image.Image:
    source = Image.open(source_png).convert("RGB")
    pixels = np.asarray(source)
    fill_mask = (
        (pixels[:, :, 0] > 218)
        & (pixels[:, :, 0] < 240)
        & (pixels[:, :, 1] > 218)
        & (pixels[:, :, 1] < 242)
        & (pixels[:, :, 2] > 220)
        & (pixels[:, :, 2] < 244)
    )
    selected = np.zeros(fill_mask.shape, dtype=np.uint8)
    seeds = (
        tuple(mirror_x(seed) for seed in spec.bone_seeds)
        if view == "palmar"
        else spec.bone_seeds
    )
    for seed in seeds:
        pixel_x, pixel_y = source_pixel(seed, source.size)
        component = connected_fill_component(
            fill_mask,
            (round(pixel_y), round(pixel_x)),
        )
        for y, x in component:
            selected[y, x] = 255

    # Expand only enough to recover the grey outline surrounding each fill.
    outline_mask = Image.fromarray(selected).filter(ImageFilter.MaxFilter(7))
    isolated = Image.new("RGB", source.size, "white")
    isolated.paste(source, mask=outline_mask)
    return isolated


def make_anatomy_canvas(
    spec: FingerSpec,
    view: str,
    source_png: Path,
) -> Image.Image:
    source = isolate_finger_bones(source_png, spec, view)
    tip_x, tip_y, angle = transform_values(spec, view)
    radians = math.radians(angle)
    cos_angle = math.cos(radians)
    sin_angle = math.sin(radians)
    output_scale = 2
    output_size = (CANVAS_W * output_scale, CANVAS_H * output_scale)
    scale = SCALE * output_scale
    centre_x = CANVAS_W / 2 * output_scale
    margin_y = TOP_MARGIN * output_scale
    source_scale_x = source.width / SOURCE_W
    source_scale_y = source.height / SOURCE_H

    # PIL's affine coefficients map output pixels back to source pixels.
    affine = (
        source_scale_x * cos_angle / scale,
        source_scale_x * sin_angle / scale,
        source_scale_x
        * (
            tip_x
            - cos_angle * centre_x / scale
            - sin_angle * margin_y / scale
            - SOURCE_X
        ),
        -source_scale_y * sin_angle / scale,
        source_scale_y * cos_angle / scale,
        source_scale_y
        * (
            tip_y
            + sin_angle * centre_x / scale
            - cos_angle * margin_y / scale
            - SOURCE_Y
        ),
    )

    transformed = source.transform(
        output_size,
        Image.Transform.AFFINE,
        affine,
        resample=Image.Resampling.BICUBIC,
        fillcolor=(255, 255, 255),
    )
    return transformed


def outline_svg(spec: FingerSpec, view: str) -> str:
    _, dip_y = mapped_point(spec.joints["DIP_joint"], spec, view)
    _, pip_y = mapped_point(spec.joints["PIP_joint"], spec, view)
    _, mcp_y = mapped_point(spec.joints["MCP_joint"], spec, view)
    centre = CANVAS_W / 2
    top = TOP_MARGIN + 5
    widths = {
        "index": (54, 63, 72),
        "middle": (57, 66, 75),
        "ring": (54, 63, 71),
        "little": (46, 54, 62),
    }
    distal, middle, proximal = widths[spec.slug]
    bottom = min(CANVAS_H - 30, mcp_y + 30)
    path = (
        f"M {centre - proximal:.1f} {bottom:.1f} "
        f"C {centre - proximal:.1f} {mcp_y - 22:.1f}, "
        f"{centre - middle:.1f} {pip_y + 18:.1f}, "
        f"{centre - middle:.1f} {pip_y:.1f} "
        f"C {centre - middle:.1f} {pip_y - 18:.1f}, "
        f"{centre - distal:.1f} {dip_y + 10:.1f}, "
        f"{centre - distal:.1f} {dip_y - 8:.1f} "
        f"C {centre - distal:.1f} {top + 24:.1f}, "
        f"{centre - distal * .72:.1f} {top:.1f}, "
        f"{centre:.1f} {top:.1f} "
        f"C {centre + distal * .72:.1f} {top:.1f}, "
        f"{centre + distal:.1f} {top + 24:.1f}, "
        f"{centre + distal:.1f} {dip_y - 8:.1f} "
        f"C {centre + distal:.1f} {dip_y + 10:.1f}, "
        f"{centre + middle:.1f} {pip_y - 18:.1f}, "
        f"{centre + middle:.1f} {pip_y:.1f} "
        f"C {centre + middle:.1f} {pip_y + 18:.1f}, "
        f"{centre + proximal:.1f} {mcp_y - 22:.1f}, "
        f"{centre + proximal:.1f} {bottom:.1f}"
    )
    nail = ""
    if view == "dorsal":
        nail_width = distal * 1.36
        nail_height = max(58.0, dip_y - top - 34.0)
        nail = (
            f"<rect x='{centre - nail_width / 2:.1f}' y='{top + 18:.1f}' "
            f"width='{nail_width:.1f}' height='{nail_height:.1f}' rx='24' "
            "fill='#FFFFFF' stroke='#000000' stroke-width='2.2'/>"
        )
    return (
        f"<path d='{path}' fill='none' stroke='#000000' "
        "stroke-width='2.4' stroke-linejoin='round'/>"
        f"{nail}"
    )


def image_data_uri(image: Image.Image) -> str:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def build_svg(
    spec: FingerSpec,
    view: str,
    source_png: Path,
) -> str:
    anatomy = make_anatomy_canvas(spec, view, source_png)
    anatomy_uri = image_data_uri(anatomy)
    guide_lines = []
    for joint_name, point in spec.joints.items():
        x, y = mapped_point(point, spec, view)
        guide_lines.append(
            f"<line id='{joint_name}' x1='38' y1='{y:.2f}' "
            f"x2='{CANVAS_W - 38}' y2='{y:.2f}' stroke='{GUIDE}' "
            "stroke-width='1.5' stroke-dasharray='7 6' opacity='.72'/>"
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 {CANVAS_W} {CANVAS_H}">
      <rect width="{CANVAS_W}" height="{CANVAS_H}" fill="{PAPER}"/>
      <image href="{anatomy_uri}" x="0" y="0"
        width="{CANVAS_W}" height="{CANVAS_H}"/>
      <g id="standard-finger-outline">{outline_svg(spec, view)}</g>
      <g id="bone-joint-candidates">{''.join(guide_lines)}</g>
      <text x="18" y="28" font-size="15" font-weight="700" fill="{INK}"
        font-family="Noto Sans TC, sans-serif">{spec.title}・{'掌面' if view == 'palmar' else '手背'}</text>
      <text x="{CANVAS_W - 18}" y="28" font-size="11" text-anchor="end"
        fill="{INK}" fill-opacity=".55"
        font-family="Noto Sans TC, sans-serif">WHO p.168｜骨關節候選線</text>
    </svg>"""


def render_svg(svg_path: Path, png_path: Path) -> None:
    rendered = fitz.open(svg_path)
    rendered[0].get_pixmap(
        matrix=fitz.Matrix(2, 2),
        alpha=False,
    ).save(png_path)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size, index=1 if bold else 0)
    return ImageFont.load_default()


def build_hand_highlight(
    spec: FingerSpec,
    view: str,
    source_png: Path,
) -> Path:
    source = Image.open(source_png).convert("RGB")
    dimmed = Image.blend(
        source,
        Image.new("RGB", source.size, "white"),
        0.78,
    )
    polygon = (
        tuple(mirror_x(point) for point in spec.polygon)
        if view == "palmar"
        else spec.polygon
    )
    mask = Image.new("L", source.size, 0)
    ImageDraw.Draw(mask).polygon(
        [source_pixel(point, source.size) for point in polygon],
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(3))
    dimmed.paste(source, mask=mask)
    output = HERE / f"{spec.slug}_{view}_hand_highlight.png"
    dimmed.save(output)
    return output


def build_middle_review_sheet(
    dorsal_highlight: Path,
    palmar_highlight: Path,
) -> None:
    sheet = Image.new("RGB", (1800, 1150), "#F4F1EA")
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (56, 32),
        "中指標準模板｜第一輪校正",
        fill="#2C1C10",
        font=font(34, bold=True),
    )
    draw.text(
        (56, 82),
        "上：整手定位（其餘部位淡化）　下：單指骨骼模板",
        fill="#75695F",
        font=font(20),
    )
    draw.text(
        (56, 112),
        "橘線為骨關節候選位置，不等同掌側指節橫紋。",
        fill="#75695F",
        font=font(18),
    )

    items = (
        ("手背整手", dorsal_highlight, (56, 160), (400, 560)),
        ("掌面整手", palmar_highlight, (472, 160), (400, 560)),
        ("手背單指", HERE / "middle_dorsal.png", (928, 160), (360, 900)),
        ("掌面單指", HERE / "middle_palmar.png", (1384, 160), (360, 900)),
    )
    for title, path, origin, box in items:
        image = Image.open(path).convert("RGB")
        image.thumbnail(box, Image.Resampling.LANCZOS)
        x = origin[0] + (box[0] - image.width) // 2
        y = origin[1] + 42
        sheet.paste(image, (x, y))
        draw.text(
            (origin[0] + box[0] // 2, origin[1]),
            title,
            anchor="ma",
            fill="#2C1C10",
            font=font(22, bold=True),
        )
    sheet.save(HERE / "中指標準模板_第一輪校正.png")


def build_review_sheet(records: list[dict]) -> None:
    tile_w, tile_h = 360, 900
    scale = 0.62
    shown_w, shown_h = int(tile_w * scale), int(tile_h * scale)
    margin = 34
    header = 116
    gutter = 24
    sheet_w = margin * 2 + 4 * shown_w + 3 * gutter
    sheet_h = header + 2 * shown_h + gutter + 62
    sheet = Image.new("RGB", (sheet_w, sheet_h), "#F4F1EA")
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (margin, 24),
        "WHO p.168 伸直單指模板｜第一輪校正",
        fill="#2C1C10",
        font=font(28, bold=True),
    )
    draw.text(
        (margin, 68),
        "橘色虛線僅代表骨關節候選位置；掌側指節橫紋須另行校正。",
        fill="#75695F",
        font=font(17),
    )
    for index, record in enumerate(records):
        row = 0 if record["view"] == "dorsal" else 1
        column = index % 4
        image = Image.open(record["png"]).convert("RGB")
        image = image.resize((shown_w, shown_h), Image.Resampling.LANCZOS)
        x = margin + column * (shown_w + gutter)
        y = header + row * (shown_h + gutter)
        sheet.paste(image, (x, y))
    sheet.save(HERE / "WHO_p168_伸直單指模板_校正總覽.png")


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    dorsal_bones = build_bones_only_source(
        DORSAL_SOURCE,
        "who_p168_dorsal_bones_only",
    )
    palmar_bones = build_bones_only_source(
        PALMAR_SOURCE,
        "who_p168_palmar_bones_only",
    )
    records = []
    sources = (
        ("dorsal", DORSAL_SOURCE, dorsal_bones),
        ("palmar", PALMAR_SOURCE, palmar_bones),
    )
    for view, source_svg, source_png in sources:
        for spec in FINGERS:
            stem = f"{spec.slug}_{view}"
            svg_path = HERE / f"{stem}.svg"
            png_path = HERE / f"{stem}.png"
            svg_path.write_text(build_svg(spec, view, source_png))
            render_svg(svg_path, png_path)
            records.append(
                {
                    "finger": spec.slug,
                    "title": spec.title,
                    "view": view,
                    "source_page": 168,
                    "source_svg": str(source_svg),
                    "source_png": str(source_png),
                    "svg": str(svg_path),
                    "png": str(png_path),
                    "joint_candidates_source": spec.joints,
                    "joint_candidates_canvas": {
                        name: [
                            round(value, 3)
                            for value in mapped_point(point, spec, view)
                        ]
                        for name, point in spec.joints.items()
                    },
                    "crease_status": (
                        "not_defined; user calibration required for palmar creases"
                    ),
                }
            )

    (HERE / "finger-template-manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "status": "awaiting_joint_and_crease_review",
                "source": "WHO p.168 TE3 dorsal hand vector artwork",
                "rules": {
                    "dorsal": "retain nails and skeleton",
                    "palmar": "remove nails; retain identical skeleton",
                    "orange_dashes": "bone-joint candidates, not palmar creases",
                },
                "items": records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    build_review_sheet(records)
    middle_spec = next(spec for spec in FINGERS if spec.slug == "middle")
    dorsal_highlight = build_hand_highlight(
        middle_spec,
        "dorsal",
        DORSAL_PNG,
    )
    palmar_highlight = build_hand_highlight(
        middle_spec,
        "palmar",
        PALMAR_PNG,
    )
    build_middle_review_sheet(dorsal_highlight, palmar_highlight)
    print(f"Produced {len(records)} finger templates in {HERE}")


if __name__ == "__main__":
    main()
