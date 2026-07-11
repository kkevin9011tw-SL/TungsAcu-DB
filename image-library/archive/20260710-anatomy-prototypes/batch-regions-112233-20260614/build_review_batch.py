#!/usr/bin/env python3
"""Build review plates for Tungs regions 11, 22 and 33.

The batch intentionally separates geometry confidence from rendering status.
Standard straight-finger constructions reuse the approved WHO p.168 workflow.
Posture-dependent and surface-landmark placements remain explicitly marked for
anatomical review.
"""

import base64
import json
import math
import shutil
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).parent
ROOT = HERE.parents[2]
BASES = ROOT / "assets" / "anatomy-prototypes" / "who-standard-bases-20260612"

PALMAR = BASES / "clean-bases" / "01_hand-palmar.png"
DORSAL = BASES / "clean-bases" / "02_hand-dorsal.png"
FOREARM_ANTERIOR = (
    BASES
    / "calibration"
    / "forearm-anterior"
    / "forearm-anterior-12cun-calibration.png"
)
FOREARM_POSTERIOR = (
    BASES
    / "calibration"
    / "forearm-posterior"
    / "forearm-posterior-12cun-calibration.png"
)
FIST_SOURCE = (
    Path(
        "/Users/samue11in/Library/CloudStorage/SynologyDrive-中醫資料庫/"
        "AI_Projects/04-書籍資料庫/converted-md/董氏奇穴穴位詮釋解/"
        "_chunks/imported_dongzhen_quanshi_part3/dongzhen_quanshi/"
        "hybrid_auto/images/"
        "baf18eebe903bebfe5332e6c8ff799926dea486ad0f810ad76cd025c2cb88706.jpg"
    )
)

W, H = 2800, 2400
PAPER = (251, 246, 234)
WHITE = (255, 255, 255)
INK = (44, 28, 16)
MUTED = (117, 105, 95)
GOLD = (196, 147, 58)
VERMILLION = (123, 45, 30)
RED = (179, 38, 30)
BLUE = (0, 129, 165)
AMBER = (190, 112, 18)

SOURCE_BOX = (322.0, 112.0, 492.0, 352.0)


def font(size: int, serif: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(
                candidate,
                size,
                index=1 if serif and "PingFang" in candidate else 0,
            )
    return ImageFont.load_default()


def slug(code: str, title: str) -> str:
    return f"{code.replace('.', '-')}_{title.replace('、', '-')}"


def dashed_line(draw, start, end, fill, width=5, dash=(16, 10)):
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if not length:
        return
    cursor = 0.0
    while cursor < length:
        stop = min(length, cursor + dash[0])
        draw.line(
            (
                x1 + dx * cursor / length,
                y1 + dy * cursor / length,
                x1 + dx * stop / length,
                y1 + dy * stop / length,
            ),
            fill=fill,
            width=width,
        )
        cursor += dash[0] + dash[1]


def point_at(start, end, fraction):
    return (
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction,
    )


def src_to_px(point, size):
    x0, y0, x1, y1 = SOURCE_BOX
    return (
        (point[0] - x0) / (x1 - x0) * size[0],
        (point[1] - y0) / (y1 - y0) * size[1],
    )


def px_to_src(point, size):
    x0, y0, x1, y1 = SOURCE_BOX
    return (
        x0 + point[0] / size[0] * (x1 - x0),
        y0 + point[1] / size[1] * (y1 - y0),
    )


def paste_contain(canvas, image, box):
    x0, y0, x1, y1 = box
    scale = min((x1 - x0) / image.width, (y1 - y0) / image.height)
    size = (round(image.width * scale), round(image.height * scale))
    resized = image.resize(size, Image.Resampling.LANCZOS)
    left = round(x0 + (x1 - x0 - size[0]) / 2)
    top = round(y0 + (y1 - y0 - size[1]) / 2)
    canvas.paste(resized, (left, top))
    return left, top, size[0], size[1]


def draw_header(draw, code, title, subtitle, status):
    draw.rectangle((70, 52, 255, 132), fill=VERMILLION)
    draw.text((162, 92), code, font=font(36), fill=(247, 237, 216), anchor="mm")
    draw.text((295, 53), title, font=font(60, True), fill=INK)
    draw.text((72, 150), subtitle, font=font(28), fill=MUTED)
    status_colour = BLUE if status == "review_ready" else AMBER
    status_text = "第一輪可審核" if status == "review_ready" else "待解剖校正"
    draw.rounded_rectangle(
        (2250, 58, 2708, 128),
        radius=18,
        outline=status_colour,
        width=4,
        fill=(255, 253, 246),
    )
    draw.text(
        (2479, 93),
        status_text,
        font=font(30),
        fill=status_colour,
        anchor="mm",
    )


def draw_footer(draw, locating_text, source_text):
    draw.rounded_rectangle(
        (1660, 1905, 2710, 2165),
        radius=20,
        fill=(255, 253, 246),
        outline=(218, 197, 158),
        width=3,
    )
    draw.text((1710, 1950), "定位摘要", font=font(32), fill=INK)
    lines = wrap_text(locating_text, 48)
    for index, text in enumerate(lines[:4]):
        draw.text((1710, 2005 + index * 38), text, font=font(25), fill=MUTED)
    draw.text(
        (70, 2305),
        source_text,
        font=font(20),
        fill=MUTED,
    )


def wrap_text(text, width):
    lines = []
    current = ""
    for char in text:
        current += char
        if len(current) >= width or char in "；。":
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines


def draw_point(draw, xy, radius=18):
    x, y = xy
    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill=RED,
        outline=WHITE,
        width=6,
    )


def save_outputs(canvas, spec, geometry):
    folder = HERE / spec["region"]
    folder.mkdir(exist_ok=True)
    stem = slug(spec["code"], spec["title"])
    png = folder / f"{stem}_第一輪審核.png"
    svg = folder / f"{stem}_第一輪審核.svg"
    data = folder / f"{stem}_定位資料.json"
    canvas.save(png)

    buffer = BytesIO()
    canvas.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    svg.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">'
        f'<image href="data:image/png;base64,{encoded}" width="{W}" height="{H}"/>'
        "</svg>",
        encoding="utf-8",
    )
    payload = {
        "version": 1,
        "status": spec["status"],
        "region": spec["region"],
        "code": spec["code"],
        "title": spec["title"],
        "covered_points": spec["covered_points"],
        "view": spec["view"],
        "location_summary": spec["location"],
        "review_note": spec.get("review_note", ""),
        "geometry": geometry,
        "outputs": {"png": str(png), "svg": str(svg)},
    }
    data.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"png": str(png), "svg": str(svg), "json": str(data), **payload}


JOINTS_DORSAL = {
    "index": {"dip": (440.5, 163.0), "pip": (434.0, 187.0), "mcp": (428.0, 218.0)},
    "middle": {"dip": (416.7, 149.0), "pip": (411.4, 177.0), "mcp": (404.8, 210.0)},
    "ring": {"dip": (396.4, 150.0), "pip": (392.0, 176.0), "mcp": (386.0, 210.0)},
    "little": {"dip": (360.0, 166.0), "pip": (360.2, 184.0), "mcp": (360.5, 213.0)},
    "thumb": {"dip": (467.0, 246.0), "pip": (451.0, 263.0), "mcp": (424.0, 282.0)},
}

HALF_WIDTH = {
    "index": {"middle": 7.3, "proximal": 9.0, "distal": 6.5},
    "middle": {"middle": 7.7, "proximal": 9.0, "distal": 6.8},
    "ring": {"middle": 7.4, "proximal": 8.2, "distal": 6.5},
    "little": {"middle": 6.2, "proximal": 7.4, "distal": 5.5},
    "thumb": {"middle": 8.0, "proximal": 10.0, "distal": 7.0},
}

FINGER_NAMES = {
    "index": "食指",
    "middle": "中指",
    "ring": "無名指",
    "little": "小指",
    "thumb": "大指",
}
SEGMENT_NAMES = {"proximal": "第一節", "middle": "第二節", "distal": "末節"}


def finger_joints(view, finger):
    joints = JOINTS_DORSAL[finger]
    if view == "dorsal":
        return joints
    return {name: (814.0 - point[0], point[1]) for name, point in joints.items()}


def segment_axis(view, finger, segment):
    joints = finger_joints(view, finger)
    if segment == "proximal":
        return joints["pip"], joints["mcp"]
    if segment == "middle":
        return joints["dip"], joints["pip"]
    dip = joints["dip"]
    pip = joints["pip"]
    vector = (dip[0] - pip[0], dip[1] - pip[1])
    tip = (dip[0] + vector[0] * 0.88, dip[1] + vector[1] * 0.88)
    return tip, dip


def line_geometry(view, finger, segment):
    start, end = segment_axis(view, finger, segment)
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    normal = (dy / length, -dx / length)
    width = HALF_WIDTH[finger][segment]
    offsets = (-width, -width / 2, 0.0, width / 2, width)
    candidates = []
    for offset in offsets:
        candidates.append(
            (
                (start[0] + normal[0] * offset, start[1] + normal[1] * offset),
                (end[0] + normal[0] * offset, end[1] + normal[1] * offset),
            )
        )
    candidates.sort(key=lambda line: line[0][0])
    if view == "palmar":
        names = ("A", "B", "C", "D", "E")
        return dict(zip(names, candidates))
    return {
        "C": candidates[0],
        "B": candidates[2],
        "A": candidates[4],
    }


FINGER_PLATES = [
    {
        "region": "11",
        "code": "11.01-02",
        "title": "大間穴、小間穴",
        "covered_points": ["大間穴", "小間穴"],
        "view": "palmar",
        "finger": "index",
        "segment": "proximal",
        "target_lines": ["B"],
        "points": [
            {"name": "小間穴", "line": "B", "fraction": 0.25},
            {"name": "大間穴", "line": "B", "fraction": 0.5},
        ],
        "division": 4,
        "status": "review_ready",
        "location": "食指陰掌第一節 B 線；小間取上 1/4，大間取中點。",
    },
    {
        "region": "11",
        "code": "11.03-04",
        "title": "浮間穴、外間穴",
        "covered_points": ["浮間穴", "外間穴"],
        "view": "palmar",
        "finger": "index",
        "segment": "middle",
        "target_lines": ["B"],
        "points": [
            {"name": "浮間穴", "line": "B", "fraction": 1 / 3},
            {"name": "外間穴", "line": "B", "fraction": 2 / 3},
        ],
        "division": 3,
        "status": "review_ready",
        "location": "食指陰掌第二節 B 線，三分點法取二穴。",
    },
    {
        "region": "11",
        "code": "11.05",
        "title": "中間穴",
        "covered_points": ["中間穴"],
        "view": "palmar",
        "finger": "index",
        "segment": "proximal",
        "target_lines": ["C"],
        "points": [{"name": "中間穴", "line": "C", "fraction": 0.5}],
        "division": 2,
        "status": "review_ready",
        "location": "食指陰掌第一節 C 線中點。",
    },
    {
        "region": "11",
        "code": "11.18",
        "title": "脾腫穴",
        "covered_points": ["脾腫穴"],
        "view": "palmar",
        "finger": "middle",
        "segment": "middle",
        "target_lines": ["C"],
        "points": [
            {"name": "", "line": "C", "fraction": 1 / 3},
            {"name": "", "line": "C", "fraction": 2 / 3},
        ],
        "division": 3,
        "status": "review_ready",
        "location": "中指陰掌第二節 C 線，三分點法取二穴。",
    },
    {
        "region": "11",
        "code": "11.06",
        "title": "還巢穴",
        "covered_points": ["還巢穴"],
        "view": "palmar",
        "finger": "ring",
        "segment": "middle",
        "target_lines": ["E"],
        "points": [{"name": "還巢穴", "line": "E", "fraction": 0.5}],
        "division": 2,
        "status": "needs_anatomy_review",
        "location": "無名指陰掌第二節 E 線中點，應以側視確認貼骨下緣。",
        "review_note": "E 線穴位依規範需側視圖；本版先用正視局部放大建立比例。",
    },
    {
        "region": "11",
        "code": "11.23",
        "title": "眼黃穴",
        "covered_points": ["眼黃穴"],
        "view": "palmar",
        "finger": "little",
        "segment": "middle",
        "target_lines": ["C"],
        "points": [{"name": "眼黃穴", "line": "C", "fraction": 0.5}],
        "division": 2,
        "status": "review_ready",
        "location": "小指陰掌第二節 C 線中點。",
    },
    {
        "region": "11",
        "code": "11.16",
        "title": "火膝穴",
        "covered_points": ["火膝穴"],
        "view": "dorsal",
        "finger": "little",
        "segment": "distal",
        "target_lines": ["C"],
        "points": [{"name": "火膝穴", "line": "C", "fraction": 0.18}],
        "division": 0,
        "status": "needs_anatomy_review",
        "location": "小指甲外側角後約二分；需依甲角與黑白肉際校正。",
        "review_note": "WHO 手背圖可見指甲，但甲角後二分仍需人工確認。",
    },
    {
        "region": "11",
        "code": "11.15",
        "title": "指腎穴",
        "covered_points": ["指腎穴"],
        "view": "dorsal",
        "finger": "ring",
        "segment": "proximal",
        "target_lines": ["C"],
        "points": [
            {"name": "", "line": "C", "fraction": 0.25},
            {"name": "", "line": "C", "fraction": 0.5},
            {"name": "", "line": "C", "fraction": 0.75},
        ],
        "division": 4,
        "status": "needs_anatomy_review",
        "location": "無名指陽掌第一節小側，四分點法取三穴；側視貼骨確認。",
        "review_note": "陽掌側線穴位依規範需側視圖。",
    },
    {
        "region": "11",
        "code": "11.14",
        "title": "指三重穴",
        "covered_points": ["指三重穴"],
        "view": "dorsal",
        "finger": "ring",
        "segment": "middle",
        "target_lines": ["C"],
        "points": [
            {"name": "", "line": "C", "fraction": 0.25},
            {"name": "", "line": "C", "fraction": 0.5},
            {"name": "", "line": "C", "fraction": 0.75},
        ],
        "division": 4,
        "status": "needs_anatomy_review",
        "location": "無名指陽掌第二節小側，四分點法取三穴；側視貼骨確認。",
        "review_note": "陽掌側線穴位依規範需側視圖。",
    },
    {
        "region": "11",
        "code": "11.09",
        "title": "心膝穴",
        "covered_points": ["心膝穴"],
        "view": "dorsal",
        "finger": "middle",
        "segment": "middle",
        "target_lines": ["A", "C"],
        "points": [
            {"name": "", "line": "A", "fraction": 0.5},
            {"name": "", "line": "C", "fraction": 0.5},
        ],
        "division": 2,
        "status": "needs_anatomy_review",
        "location": "中指陽掌第二節大側、小側各中點；兩側均需側視貼骨確認。",
        "review_note": "陽掌 A、C 側線穴位依規範需側視圖。",
    },
    {
        "region": "11",
        "code": "11.11",
        "title": "肺心穴",
        "covered_points": ["肺心穴"],
        "view": "dorsal",
        "finger": "middle",
        "segment": "middle",
        "target_lines": ["B"],
        "points": [
            {"name": "", "line": "B", "fraction": 1 / 3},
            {"name": "", "line": "B", "fraction": 2 / 3},
        ],
        "division": 3,
        "status": "review_ready",
        "location": "中指陽掌第二節 B 線，三分點法取二穴。",
    },
    {
        "region": "11",
        "code": "11.10",
        "title": "木火穴",
        "covered_points": ["木火穴"],
        "view": "dorsal",
        "finger": "middle",
        "segment": "distal",
        "target_lines": ["B"],
        "points": [{"name": "木火穴", "line": "B", "fraction": 1.0}],
        "division": 0,
        "status": "needs_anatomy_review",
        "location": "中指末節與第二節交界橫紋中央。",
        "review_note": "WHO 圖顯示骨關節，皮膚橫紋位置需人工校正。",
    },
    {
        "region": "11",
        "code": "11.08",
        "title": "指五金、指千金穴",
        "covered_points": ["指五金、指千金穴"],
        "view": "dorsal",
        "finger": "index",
        "segment": "proximal",
        "target_lines": ["C"],
        "points": [
            {"name": "指千金", "line": "C", "fraction": 1 / 3},
            {"name": "指五金", "line": "C", "fraction": 2 / 3},
        ],
        "division": 3,
        "status": "needs_anatomy_review",
        "location": "食指陽掌第一節小側，三分點法取二穴；貼骨旁。",
        "review_note": "陽掌側線穴位依規範需側視圖。",
    },
    {
        "region": "11",
        "code": "11.07",
        "title": "指駟馬穴",
        "covered_points": ["指駟馬穴"],
        "view": "dorsal",
        "finger": "index",
        "segment": "middle",
        "target_lines": ["C"],
        "points": [
            {"name": "", "line": "C", "fraction": 0.25},
            {"name": "", "line": "C", "fraction": 0.5},
            {"name": "", "line": "C", "fraction": 0.75},
        ],
        "division": 4,
        "status": "needs_anatomy_review",
        "location": "食指陽掌第二節小側，四分點法取三穴；貼骨旁。",
        "review_note": "沿用既有指駟馬原型，但側線仍需側視校正。",
    },
    {
        "region": "11",
        "code": "11.24",
        "title": "婦科穴",
        "covered_points": ["婦科穴"],
        "view": "dorsal",
        "finger": "thumb",
        "segment": "proximal",
        "target_lines": ["C"],
        "points": [
            {"name": "", "line": "C", "fraction": 1 / 3},
            {"name": "", "line": "C", "fraction": 2 / 3},
        ],
        "division": 3,
        "status": "needs_anatomy_review",
        "location": "大指陽掌第一節小側，三分點法取二穴；貼骨旁。",
        "review_note": "拇指角度與側線由 WHO 圖估算，需人工校正。",
    },
    {
        "region": "11",
        "code": "11.26",
        "title": "制汙穴",
        "covered_points": ["制汙穴"],
        "view": "dorsal",
        "finger": "thumb",
        "segment": "proximal",
        "target_lines": ["B"],
        "points": [
            {"name": "", "line": "B", "fraction": 0.25},
            {"name": "", "line": "B", "fraction": 0.5},
            {"name": "", "line": "B", "fraction": 0.75},
        ],
        "division": 4,
        "status": "needs_anatomy_review",
        "location": "大指陽掌第一節中央線，四分點法取三穴。",
        "review_note": "拇指指節邊界由 WHO 骨關節估算，需人工校正皮膚橫紋。",
    },
    {
        "region": "11",
        "code": "11.25",
        "title": "止涎穴",
        "covered_points": ["止涎穴"],
        "view": "dorsal",
        "finger": "thumb",
        "segment": "proximal",
        "target_lines": ["A"],
        "points": [
            {"name": "", "line": "A", "fraction": 1 / 3},
            {"name": "", "line": "A", "fraction": 2 / 3},
        ],
        "division": 3,
        "status": "needs_anatomy_review",
        "location": "大指陽掌第一節橈側，三分點法取二穴；貼骨旁。",
        "review_note": "陽掌側線穴位需側視圖校正。",
    },
    {
        "region": "11",
        "code": "11.27",
        "title": "五虎穴",
        "covered_points": ["五虎穴"],
        "view": "palmar",
        "finger": "thumb",
        "segment": "proximal",
        "target_lines": ["A"],
        "points": [
            {"name": f"五虎{i}", "line": "A", "fraction": i / 6}
            for i in range(1, 6)
        ],
        "division": 6,
        "status": "needs_anatomy_review",
        "location": "大指陰掌第一節 A 線，六分點法取五穴。",
        "review_note": "陰掌 A 線穴位需側視貼骨校正。",
    },
    {
        "region": "11",
        "code": "11.13",
        "title": "膽穴",
        "covered_points": ["膽穴"],
        "view": "palmar",
        "finger": "middle",
        "segment": "proximal",
        "target_lines": ["A", "E"],
        "points": [
            {"name": "", "line": "A", "fraction": 0.5},
            {"name": "", "line": "E", "fraction": 0.5},
        ],
        "division": 2,
        "status": "needs_anatomy_review",
        "location": "中指陰掌第一節大側、小側各中點。",
        "review_note": "陰掌 A、E 線穴位需側視貼骨校正。",
    },
    {
        "region": "11",
        "code": "11.12",
        "title": "二角明穴",
        "covered_points": ["二角明穴"],
        "view": "dorsal",
        "finger": "middle",
        "segment": "proximal",
        "target_lines": ["B"],
        "points": [
            {"name": "", "line": "B", "fraction": 1 / 3},
            {"name": "", "line": "B", "fraction": 2 / 3},
        ],
        "division": 3,
        "status": "review_ready",
        "location": "中指陽掌第一節 B 線，三分點法取二穴。",
    },
]


def build_finger_plate(spec):
    base = Image.open(PALMAR if spec["view"] == "palmar" else DORSAL).convert("RGB")
    lines = line_geometry(spec["view"], spec["finger"], spec["segment"])
    point_records = []
    for item in spec["points"]:
        line = lines[item["line"]]
        point_records.append(
            {
                **item,
                "source": point_at(line[0], line[1], item["fraction"]),
            }
        )

    canvas = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(canvas)
    draw_header(
        draw,
        spec["code"],
        spec["title"],
        f'第一輪定位｜{FINGER_NAMES[spec["finger"]]}{SEGMENT_NAMES[spec["segment"]]}｜'
        f'{"掌面" if spec["view"] == "palmar" else "手背"}',
        spec["status"],
    )

    main_box = (80, 300, 1180, 2110)
    main_left, main_top, main_w, main_h = paste_contain(canvas, base, main_box)

    def main_map(source):
        px = src_to_px(source, base.size)
        return (
            main_left + px[0] / base.width * main_w,
            main_top + px[1] / base.height * main_h,
        )

    for record in point_records:
        draw_point(draw, main_map(record["source"]), 14)

    all_segment_points = [point for line in lines.values() for point in line]
    xs = [point[0] for point in all_segment_points]
    ys = [point[1] for point in all_segment_points]
    margin_x = 19 if spec["finger"] != "thumb" else 24
    margin_y = 13 if spec["finger"] != "thumb" else 22
    crop_src = (
        min(xs) - margin_x,
        min(ys) - margin_y,
        max(xs) + margin_x,
        max(ys) + margin_y,
    )
    crop_px0 = src_to_px((crop_src[0], crop_src[1]), base.size)
    crop_px1 = src_to_px((crop_src[2], crop_src[3]), base.size)
    crop = base.crop((*crop_px0, *crop_px1)).resize((1040, 1040), Image.Resampling.LANCZOS)
    mask = Image.new("L", (1040, 1040), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 1039, 1039), fill=255)
    inset = Image.new("RGB", (1040, 1040), WHITE)
    inset.paste(crop, mask=mask)
    inset_left, inset_top = 1540, 390
    canvas.paste(inset, (inset_left, inset_top))
    draw.ellipse(
        (inset_left, inset_top, inset_left + 1040, inset_top + 1040),
        outline=GOLD,
        width=7,
    )
    draw.text(
        (2060, 325),
        f'{FINGER_NAMES[spec["finger"]]}{SEGMENT_NAMES[spec["segment"]]}原位放大',
        font=font(36),
        fill=INK,
        anchor="mm",
    )

    def inset_map(source):
        return (
            inset_left + (source[0] - crop_src[0]) / (crop_src[2] - crop_src[0]) * 1040,
            inset_top + (source[1] - crop_src[1]) / (crop_src[3] - crop_src[1]) * 1040,
        )

    for name, line in lines.items():
        active = name in spec["target_lines"]
        colour = RED if active else BLUE
        width = 8 if active else 6
        dashed_line(draw, inset_map(line[0]), inset_map(line[1]), colour, width)
        label = inset_map(line[0])
        draw.text(
            (label[0], label[1] - 34),
            name,
            font=font(35),
            fill=VERMILLION if active else BLUE,
            anchor="mm",
            stroke_width=3,
            stroke_fill=PAPER,
        )

    boundary_start = min(lines.values(), key=lambda item: item[0][0])[0]
    boundary_end = max(lines.values(), key=lambda item: item[0][0])[0]
    dashed_line(draw, inset_map(boundary_start), inset_map(boundary_end), MUTED, 5)
    boundary_start2 = min(lines.values(), key=lambda item: item[1][0])[1]
    boundary_end2 = max(lines.values(), key=lambda item: item[1][0])[1]
    dashed_line(draw, inset_map(boundary_start2), inset_map(boundary_end2), MUTED, 5)

    label_side = 1
    for index, record in enumerate(point_records):
        xy = inset_map(record["source"])
        draw_point(draw, xy, 19)
        if record["name"]:
            text_x = xy[0] + (105 if label_side else -105)
            draw.line((xy[0] + 24, xy[1], text_x - 18, xy[1]), fill=MUTED, width=3)
            draw.text(
                (text_x, xy[1]),
                record["name"],
                font=font(28),
                fill=INK,
                anchor="lm" if label_side else "rm",
                stroke_width=3,
                stroke_fill=PAPER,
            )
            label_side = 1 - label_side

    if spec["division"]:
        target = lines[spec["target_lines"][0]]
        start = inset_map(target[0])
        end = inset_map(target[1])
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        normal = (dy / length, -dx / length)
        if normal[0] < 0:
            normal = (-normal[0], -normal[1])
        offset = 190
        ruler_start = (start[0] + normal[0] * offset, start[1] + normal[1] * offset)
        ruler_end = (end[0] + normal[0] * offset, end[1] + normal[1] * offset)
        draw.line((*ruler_start, *ruler_end), fill=INK, width=6)
        for index in range(spec["division"] + 1):
            centre = point_at(ruler_start, ruler_end, index / spec["division"])
            cross = (normal[0] * 24, normal[1] * 24)
            draw.line(
                (
                    centre[0] - cross[0],
                    centre[1] - cross[1],
                    centre[0] + cross[0],
                    centre[1] + cross[1],
                ),
                fill=INK,
                width=6,
            )
        ruler_mid = point_at(ruler_start, ruler_end, 0.5)
        draw.text(
            (ruler_mid[0] + normal[0] * 95, ruler_mid[1] + normal[1] * 95),
            f'{ {2: "二", 3: "三", 4: "四", 6: "六"}.get(spec["division"], spec["division"]) }分點法',
            font=font(32),
            fill=INK,
            anchor="mm",
            stroke_width=3,
            stroke_fill=PAPER,
        )

    if spec["status"] != "review_ready":
        draw.text(
            (2060, 1510),
            spec.get("review_note", "位置待人工校正"),
            font=font(27),
            fill=AMBER,
            anchor="mm",
        )

    draw_footer(
        draw,
        spec["location"],
        "底圖｜WHO Standard Acupuncture Point Locations in the Western Pacific Region "
        "(2008), p.168　定位文字｜《董氏奇穴穴位詮釋解》",
    )
    geometry = {
        "source_box": SOURCE_BOX,
        "finger": spec["finger"],
        "segment": spec["segment"],
        "lines_source_coordinates": lines,
        "points": point_records,
        "division": spec["division"],
    }
    return save_outputs(canvas, spec, geometry)


HAND_PLATES = [
    {
        "region": "22",
        "code": "22.01-02",
        "title": "重子穴、重仙穴",
        "covered_points": ["重子穴", "重仙穴"],
        "view": "palmar_hand",
        "base": PALMAR,
        "points": [
            {"name": "重子穴", "pixel": (410, 790)},
            {"name": "重仙穴", "pixel": (455, 920)},
        ],
        "status": "needs_anatomy_review",
        "location": "第一、二掌骨間；重子約虎口下一寸，重仙沿掌緣方向再下一寸。",
        "review_note": "以 WHO 開掌骨位推估，需校正食指 C 線延長線與大指高骨垂線。",
    },
    {
        "region": "22",
        "code": "22.04-05",
        "title": "大白穴、靈骨穴",
        "covered_points": ["大白穴", "靈骨穴"],
        "view": "dorsal_hand",
        "base": DORSAL,
        "points": [
            {"name": "大白穴", "pixel": (705, 715)},
            {"name": "靈骨穴", "pixel": (645, 870)},
        ],
        "status": "needs_anatomy_review",
        "location": "第一、二掌骨間；大白近掌指關節，靈骨近第一、二掌骨接合處。",
        "review_note": "臨床以握拳、立掌取穴；WHO 無相同姿勢，本版為開掌骨位對照。",
    },
    {
        "region": "22",
        "code": "22.03",
        "title": "上白穴",
        "covered_points": ["上白穴"],
        "view": "dorsal_hand",
        "base": DORSAL,
        "points": [{"name": "上白穴", "pixel": (560, 655)}],
        "status": "needs_anatomy_review",
        "location": "食指與中指掌骨間，距掌指關節下約五分。",
        "review_note": "掌骨間距與五分位置需依原書圖校正。",
    },
    {
        "region": "22",
        "code": "22.06-07",
        "title": "中白穴、下白穴",
        "covered_points": ["中白穴", "下白穴"],
        "view": "dorsal_hand",
        "base": DORSAL,
        "points": [
            {"name": "中白穴", "pixel": (300, 650)},
            {"name": "下白穴", "pixel": (275, 790)},
        ],
        "status": "needs_anatomy_review",
        "location": "第四、五掌骨間；中白距掌指關節五分，下白再近腕一寸。",
        "review_note": "原定位要求握拳，本版先依 WHO 開掌骨間隙建立相對位置。",
    },
    {
        "region": "22",
        "code": "22.08-09",
        "title": "腕順一穴、腕順二穴",
        "covered_points": ["腕順一穴", "腕順二穴"],
        "view": "dorsal_hand",
        "base": DORSAL,
        "points": [
            {"name": "腕順二穴", "pixel": (180, 785)},
            {"name": "腕順一穴", "pixel": (165, 875)},
        ],
        "status": "needs_anatomy_review",
        "location": "第五掌骨尺側；腕順二距腕橫紋一寸五分，腕順一二寸五分。",
        "review_note": "需校正第五掌骨外側骨緣與腕橫紋起點。",
    },
    {
        "region": "22",
        "code": "22.10",
        "title": "手解穴",
        "covered_points": ["手解穴"],
        "view": "palmar_hand",
        "base": PALMAR,
        "points": [{"name": "手解穴", "pixel": (720, 775)}],
        "status": "needs_anatomy_review",
        "location": "第四、五掌骨間，握拳時小指尖所觸掌處。",
        "review_note": "WHO 無握拳掌面圖，本版以少府區域骨位暫定。",
    },
    {
        "region": "22",
        "code": "22.11",
        "title": "土水穴",
        "covered_points": ["土水穴"],
        "view": "palmar_hand",
        "base": PALMAR,
        "points": [
            {"name": "土水上", "pixel": (330, 855)},
            {"name": "土水中", "pixel": (305, 945)},
            {"name": "土水下", "pixel": (285, 1040)},
        ],
        "status": "needs_anatomy_review",
        "location": "第一掌骨內側黑白肉際三穴；中央近魚際，上下各取相鄰中點。",
        "review_note": "黑白肉際不在骨骼圖中，需依體表邊界校正。",
    },
]


def build_hand_plate(spec):
    base = Image.open(spec["base"]).convert("RGB")
    canvas = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(canvas)
    draw_header(
        draw,
        spec["code"],
        spec["title"],
        "第一輪定位｜手掌骨骼透視",
        spec["status"],
    )
    main_left, main_top, main_w, main_h = paste_contain(
        canvas, base, (110, 260, 1280, 2180)
    )

    def main_map(pixel):
        return (
            main_left + pixel[0] / base.width * main_w,
            main_top + pixel[1] / base.height * main_h,
        )

    for item in spec["points"]:
        draw_point(draw, main_map(item["pixel"]), 16)

    xs = [point["pixel"][0] for point in spec["points"]]
    ys = [point["pixel"][1] for point in spec["points"]]
    crop_box = (
        max(0, min(xs) - 190),
        max(0, min(ys) - 190),
        min(base.width, max(xs) + 190),
        min(base.height, max(ys) + 190),
    )
    crop = base.crop(crop_box)
    crop.thumbnail((1080, 1080), Image.Resampling.LANCZOS)
    inset_left = 1535 + (1080 - crop.width) // 2
    inset_top = 390 + (1080 - crop.height) // 2
    canvas.paste(crop, (inset_left, inset_top))
    draw.rounded_rectangle(
        (1510, 365, 2640, 1495),
        radius=45,
        outline=GOLD,
        width=6,
    )
    draw.text(
        (2075, 315),
        "局部骨位放大",
        font=font(36),
        fill=INK,
        anchor="mm",
    )
    scale = crop.width / (crop_box[2] - crop_box[0])
    for index, item in enumerate(spec["points"]):
        point = (
            inset_left + (item["pixel"][0] - crop_box[0]) * scale,
            inset_top + (item["pixel"][1] - crop_box[1]) * scale,
        )
        draw_point(draw, point, 20)
        side = 1 if index % 2 == 0 else -1
        label_x = point[0] + side * 125
        draw.line((point[0] + side * 26, point[1], label_x - side * 15, point[1]), fill=MUTED, width=4)
        draw.text(
            (label_x, point[1]),
            item["name"],
            font=font(30),
            fill=INK,
            anchor="lm" if side > 0 else "rm",
            stroke_width=3,
            stroke_fill=PAPER,
        )

    draw.text(
        (2075, 1560),
        spec["review_note"],
        font=font(27),
        fill=AMBER,
        anchor="mm",
    )
    draw_footer(
        draw,
        spec["location"],
        "底圖｜WHO Standard Acupuncture Point Locations in the Western Pacific Region "
        "(2008), p.168　定位文字｜《董氏奇穴穴位詮釋解》",
    )
    return save_outputs(
        canvas,
        spec,
        {"base_pixel_size": base.size, "points_base_pixels": spec["points"]},
    )


FOREARM_SPECS = [
    {
        "region": "33",
        "code": "33.01-03",
        "title": "其門穴、其角穴、其正穴",
        "covered_points": ["其門穴", "其角穴", "其正穴"],
        "view": "forearm_posterior",
        "base": FOREARM_POSTERIOR,
        "points": [
            {"name": "其門穴", "cun": 2, "offset": 85},
            {"name": "其角穴", "cun": 4, "offset": 85},
            {"name": "其正穴", "cun": 6, "offset": 85},
        ],
        "status": "needs_anatomy_review",
        "location": "橈骨外側，自腕橫紋起二、四、六寸。",
        "review_note": "寸位可靠；橈骨外側貼骨線需人工校正。",
    },
    {
        "region": "33",
        "code": "33.04-07",
        "title": "火串穴、火陵穴、火山穴、火腑海穴",
        "covered_points": ["火串穴", "火陵穴", "火山穴", "火腑海穴"],
        "view": "forearm_posterior",
        "base": FOREARM_POSTERIOR,
        "points": [
            {"name": "火串穴", "cun": 3, "offset": 5},
            {"name": "火陵穴", "cun": 5, "offset": 5},
            {"name": "火山穴", "cun": 6.5, "offset": 5},
            {"name": "火腑海穴", "cun": 8.5, "offset": 5},
        ],
        "status": "needs_anatomy_review",
        "location": "前臂後面中央線附近，自腕橫紋三、五、六點五、八點五寸。",
        "review_note": "比例位置已建立；手撫胸造成的旋臂表面線需人工校正。",
    },
    {
        "region": "33",
        "code": "33.09",
        "title": "手千金穴",
        "covered_points": ["手千金穴"],
        "view": "forearm_posterior",
        "base": FOREARM_POSTERIOR,
        "points": [{"name": "手千金穴", "cun": 8, "offset": -80}],
        "status": "needs_anatomy_review",
        "location": "尺骨外側，距腕部豌豆骨約八寸，筋下骨前。",
        "review_note": "八寸比例可靠；筋下骨前的橫向位置需人工校正。",
    },
    {
        "region": "33",
        "code": "33.10-12",
        "title": "腸門穴、肝門穴、心門穴",
        "covered_points": ["腸門穴", "肝門穴", "心門穴"],
        "view": "forearm_posterior",
        "base": FOREARM_POSTERIOR,
        "points": [
            {"name": "腸門穴", "cun": 3, "offset": -105},
            {"name": "肝門穴", "cun": 6, "offset": -105},
            {"name": "心門穴", "cun": 10.5, "offset": -105},
        ],
        "status": "needs_anatomy_review",
        "location": "尺骨內側線；腸門三寸、肝門六寸、心門距肘尖一寸五分。",
        "review_note": "心門已有核可原型；本合併圖仍需統一尺骨內側貼骨線。",
    },
    {
        "region": "33",
        "code": "33.13-15",
        "title": "人士穴、地士穴、天士穴",
        "covered_points": ["人士穴", "地士穴", "天士穴"],
        "view": "forearm_anterior",
        "base": FOREARM_ANTERIOR,
        "points": [
            {"name": "人士穴", "cun": 4, "offset": -75},
            {"name": "地士穴", "cun": 7, "offset": -75},
            {"name": "天士穴", "cun": 10, "offset": -75},
        ],
        "status": "needs_anatomy_review",
        "location": "前臂橈骨內側，自腕橫紋四、七、十寸。",
        "review_note": "寸位可靠；橈骨內側與肺經貼骨線需人工校正。",
    },
    {
        "region": "33",
        "code": "33.16",
        "title": "曲陵穴",
        "covered_points": ["曲陵穴"],
        "view": "forearm_anterior",
        "base": FOREARM_ANTERIOR,
        "points": [{"name": "曲陵穴", "cun": 12, "offset": -65}],
        "status": "needs_anatomy_review",
        "location": "肘窩橫紋上，大筋外側，屈肘時貼筋取穴。",
        "review_note": "WHO 為伸肘圖；大筋隆起位置需以屈肘姿勢校正。",
    },
]


def forearm_axis(view, size):
    if view == "forearm_anterior":
        return (430.127, 1007.84), (583.483, 299.917)
    return (0.48 * size[0], 0.66 * size[1]), (0.43 * size[0], 0.19 * size[1])


def forearm_point(view, size, cun, offset):
    wrist, elbow = forearm_axis(view, size)
    centre = point_at(wrist, elbow, cun / 12)
    dx = elbow[0] - wrist[0]
    dy = elbow[1] - wrist[1]
    length = math.hypot(dx, dy)
    normal = (dy / length, -dx / length)
    return centre[0] + normal[0] * offset, centre[1] + normal[1] * offset


def build_forearm_plate(spec):
    base = Image.open(spec["base"]).convert("RGB")
    points = [
        {**item, "pixel": forearm_point(spec["view"], base.size, item["cun"], item["offset"])}
        for item in spec["points"]
    ]
    canvas = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(canvas)
    draw_header(
        draw,
        spec["code"],
        spec["title"],
        "第一輪定位｜前臂骨骼與肌腱透視｜腕橫紋—肘橫紋 12 寸",
        spec["status"],
    )
    main_left, main_top, main_w, main_h = paste_contain(
        canvas, base, (120, 260, 1460, 2200)
    )

    def main_map(pixel):
        return (
            main_left + pixel[0] / base.width * main_w,
            main_top + pixel[1] / base.height * main_h,
        )

    mapped = []
    for item in points:
        xy = main_map(item["pixel"])
        mapped.append((item, xy))
        draw_point(draw, xy, 17)
        draw.text(
            (xy[0] + 34, xy[1]),
            item["name"],
            font=font(28),
            fill=INK,
            anchor="lm",
            stroke_width=3,
            stroke_fill=PAPER,
        )

    draw.rounded_rectangle(
        (1580, 350, 2680, 1500),
        radius=34,
        outline=GOLD,
        width=6,
        fill=(255, 253, 246),
    )
    draw.text((2130, 420), "骨度分寸定位", font=font(40), fill=INK, anchor="mm")
    ruler_x = 1830
    ruler_top = 545
    ruler_bottom = 1325
    draw.line((ruler_x, ruler_bottom, ruler_x, ruler_top), fill=BLUE, width=9)
    for cun in range(13):
        y = ruler_bottom - (ruler_bottom - ruler_top) * cun / 12
        tick = 44 if cun % 3 == 0 else 24
        draw.line((ruler_x - tick, y, ruler_x + tick, y), fill=BLUE, width=7)
    draw.text((1900, 930), "12 寸", font=font(36), fill=BLUE, anchor="lm")
    for index, item in enumerate(points):
        y = ruler_bottom - (ruler_bottom - ruler_top) * item["cun"] / 12
        point_x = 2210
        draw_point(draw, (point_x, y), 16)
        draw.text(
            (point_x + 38, y),
            f'{item["name"]}　{item["cun"]:g}寸',
            font=font(29),
            fill=INK,
            anchor="lm",
        )
        dashed_line(draw, (ruler_x + 48, y), (point_x - 22, y), MUTED, 3, (10, 8))
    draw.text(
        (2130, 1570),
        spec["review_note"],
        font=font(27),
        fill=AMBER,
        anchor="mm",
    )
    draw_footer(
        draw,
        spec["location"],
        "底圖與比例｜WHO Standard Acupuncture Point Locations in the Western Pacific Region "
        "(2008)；腕橫紋—肘橫紋 12 B-cun　定位文字｜《董氏奇穴穴位詮釋解》",
    )
    return save_outputs(
        canvas,
        spec,
        {
            "base_pixel_size": base.size,
            "axis": forearm_axis(spec["view"], base.size),
            "points": points,
        },
    )


def build_trifurcation_plate():
    spec = {
        "region": "special",
        "code": "A.02-04",
        "title": "三叉一穴、三叉二穴、三叉三穴",
        "covered_points": ["三叉一穴", "三叉二穴", "三叉三穴"],
        "view": "dorsal_clenched_fist_front",
        "status": "needs_anatomy_review",
        "location": "握拳取穴；依序位於二三、三四、四五指縫接合處。三叉三緊貼第四指，筋下骨旁。",
        "review_note": "WHO 無握拳手背正視骨骼圖，本版直接保留原書姿勢作定位基準。",
    }
    source = Image.open(FIST_SOURCE).convert("RGB")
    canvas = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(canvas)
    draw_header(
        draw,
        spec["code"],
        spec["title"],
        "特殊姿勢試作｜握拳手背正視｜原書姿勢基準",
        spec["status"],
    )
    left, top, width, height = paste_contain(canvas, source, (300, 270, 1550, 2150))
    points_source = [
        {"name": "三叉一穴", "pixel": (244, 494)},
        {"name": "三叉二穴", "pixel": (398, 485)},
        {"name": "三叉三穴", "pixel": (529, 475)},
    ]
    mapped = []
    for index, item in enumerate(points_source):
        xy = (
            left + item["pixel"][0] / source.width * width,
            top + item["pixel"][1] / source.height * height,
        )
        mapped.append({**item, "canvas": xy})
        draw_point(draw, xy, 20)
        label_y = 565 + index * 220
        draw.line((xy[0] + 25, xy[1], 1840, label_y), fill=GOLD, width=4)
        draw.rounded_rectangle(
            (1840, label_y - 52, 2570, label_y + 52),
            radius=15,
            fill=(255, 253, 246),
            outline=GOLD,
            width=3,
        )
        draw.text(
            (2205, label_y),
            item["name"],
            font=font(38),
            fill=INK,
            anchor="mm",
        )
    draw.rounded_rectangle(
        (1700, 1370, 2670, 1740),
        radius=24,
        fill=(255, 253, 246),
        outline=AMBER,
        width=4,
    )
    notes = [
        "WHO 檢索結果：沒有相同的握拳手背正視骨骼圖。",
        "原書圖最能保留三個指縫接合處的姿勢關係。",
        "三叉三正式版需再校正：緊貼第四指、筋下骨旁。",
    ]
    for index, text in enumerate(notes):
        draw.text((1760, 1435 + index * 78), text, font=font(28), fill=AMBER)
    draw_footer(
        draw,
        spec["location"],
        "姿勢與穴點參考｜《董氏奇穴穴位詮釋解》圖13-2　WHO 僅作手骨開掌位置輔助，未硬套為握拳圖",
    )
    return save_outputs(
        canvas,
        spec,
        {"source_pixel_size": source.size, "source_points": points_source, "mapped": mapped},
    )


EXISTING = [
    {
        "region": "11",
        "code": "11.17",
        "title": "木穴",
        "covered_points": ["木穴"],
        "view": "palmar",
        "status": "approved_existing",
        "source": ROOT
        / "assets/anatomy-prototypes/poc-muxue-20260612/"
        "木穴_精簡評估版_v4_WHO左手掌面線稿.png",
    },
    {
        "region": "11",
        "code": "11.19",
        "title": "心常穴",
        "covered_points": ["心常穴"],
        "view": "palmar",
        "status": "approved_existing",
        "source": ROOT
        / "assets/anatomy-prototypes/poc-xinchang-20260613/"
        "心常穴_正式評估版_v5_WHO-p168左手掌面.png",
    },
    {
        "region": "11",
        "code": "11.21",
        "title": "三眼穴",
        "covered_points": ["三眼穴"],
        "view": "palmar",
        "status": "approved_existing",
        "source": ROOT
        / "assets/anatomy-prototypes/poc-sanyan-20260613/"
        "三眼穴_正式評估版_v1_WHO-p168左手掌面.png",
    },
    {
        "region": "11",
        "code": "11.22",
        "title": "復原穴",
        "covered_points": ["復原穴"],
        "view": "palmar",
        "status": "approved_existing",
        "source": ROOT
        / "assets/anatomy-prototypes/poc-fuyuan-20260613/"
        "復原穴_正式評估版_v1_WHO-p168左手掌面.png",
    },
    {
        "region": "11",
        "code": "11.20",
        "title": "木炎穴",
        "covered_points": ["木炎穴"],
        "view": "palmar",
        "status": "approved_existing",
        "source": ROOT
        / "assets/anatomy-prototypes/poc-muyan-20260613/"
        "木炎穴_正式評估版_v1_WHO-p168左手掌面.png",
    },
]


def copy_existing(spec):
    folder = HERE / spec["region"]
    folder.mkdir(exist_ok=True)
    destination = folder / f'{slug(spec["code"], spec["title"])}_已核可.png'
    shutil.copy2(spec["source"], destination)
    return {
        **{key: value for key, value in spec.items() if key != "source"},
        "source": str(spec["source"]),
        "png": str(destination),
        "review_note": "沿用先前核可版本。",
    }


def make_contact_sheet(items, filename, title):
    thumbs = []
    for item in items:
        path = Path(item["png"])
        image = Image.open(path).convert("RGB")
        image.thumbnail((520, 445), Image.Resampling.LANCZOS)
        thumbs.append((item, image.copy()))
    columns = 4
    rows = math.ceil(len(thumbs) / columns)
    sheet = Image.new("RGB", (columns * 560, 130 + rows * 520), PAPER)
    draw = ImageDraw.Draw(sheet)
    draw.text((50, 45), title, font=font(44, True), fill=INK)
    for index, (item, image) in enumerate(thumbs):
        col = index % columns
        row = index // columns
        x = col * 560 + 20
        y = 120 + row * 520
        sheet.paste(image, (x + (520 - image.width) // 2, y))
        status = item.get("status", "")
        colour = BLUE if status in {"review_ready", "approved_existing"} else AMBER
        draw.text(
            (x + 260, y + 455),
            f'{item["code"]} {item["title"]}',
            font=font(23),
            fill=INK,
            anchor="mm",
        )
        draw.text(
            (x + 260, y + 488),
            "可審核" if status == "review_ready" else (
                "已核可" if status == "approved_existing" else "待校正"
            ),
            font=font(21),
            fill=colour,
            anchor="mm",
        )
    path = HERE / filename
    sheet.save(path)
    return str(path)


def build():
    outputs = []
    for spec in EXISTING:
        outputs.append(copy_existing(spec))
    for spec in FINGER_PLATES:
        outputs.append(build_finger_plate(spec))
    for spec in HAND_PLATES:
        outputs.append(build_hand_plate(spec))
    for spec in FOREARM_SPECS:
        outputs.append(build_forearm_plate(spec))
    outputs.append(build_trifurcation_plate())

    by_region = {
        region: [item for item in outputs if item["region"] == region]
        for region in ("11", "22", "33", "special")
    }
    contact_sheets = {
        "11": make_contact_sheet(
            by_region["11"], "一一部位_第一輪總覽.png", "一一部位穴位標定｜第一輪總覽"
        ),
        "22": make_contact_sheet(
            by_region["22"], "二二部位_第一輪總覽.png", "二二部位穴位標定｜第一輪總覽"
        ),
        "33": make_contact_sheet(
            by_region["33"], "三三部位_第一輪總覽.png", "三三部位穴位標定｜第一輪總覽"
        ),
        "special": make_contact_sheet(
            by_region["special"], "特殊視角_第一輪總覽.png", "特殊姿勢穴位｜第一輪總覽"
        ),
    }
    covered = sorted(
        {point for item in outputs for point in item.get("covered_points", [])}
    )
    manifest = {
        "version": 1,
        "generated_at": "2026-06-14",
        "scope": "regions 11, 22, 33 plus special clenched-fist prototype",
        "plate_count": len(outputs),
        "covered_point_count": len(covered),
        "covered_points": covered,
        "status_counts": {
            status: sum(item.get("status") == status for item in outputs)
            for status in ("approved_existing", "review_ready", "needs_anatomy_review")
        },
        "contact_sheets": contact_sheets,
        "plates": outputs,
    }
    (HERE / "batch-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest["status_counts"], ensure_ascii=False))
    print(f"plates={manifest['plate_count']} covered_points={manifest['covered_point_count']}")
    for path in contact_sheets.values():
        print(path)


if __name__ == "__main__":
    build()
