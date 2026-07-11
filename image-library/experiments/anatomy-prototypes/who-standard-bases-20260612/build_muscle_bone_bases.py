#!/usr/bin/env python3
"""Build cleaned WHO limb bases that retain both muscle and bone artwork."""

import json
import re
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont

from build_standard_bases import BaseSpec, FONT_PATH, HERE, SOURCE_PDF
from clean_standard_bases import page_without_text


OUTPUT_DIR = HERE / "muscle-bone-bases"
MANIFEST_PATH = HERE / "muscle-bone-manifest.json"
REVIEW_SHEET_PATH = HERE / "WHO_四肢肌肉骨骼底圖_8張檢查總覽.png"
RENDER_SCALE = 6
REMOVE_COLOURS = {
    "#00a651",
    "#0db14b",
    "#808285",
    "#939598",
    "#ed1d24",
}

BASES = [
    BaseSpec(
        1,
        "upper-arm-anterior",
        "上臂／前面",
        36,
        (326, 100, 500, 357),
        "肱二頭肌、肱骨與肩肘骨性標誌",
    ),
    BaseSpec(
        2,
        "upper-arm-posterior",
        "上臂／後面",
        173,
        (326, 100, 500, 357),
        "三角肌、肩胛骨與肱骨；原書未提供完整肱三頭肌透視",
    ),
    BaseSpec(
        3,
        "forearm-anterior",
        "前臂／前面",
        163,
        (326, 100, 500, 357),
        "掌長肌與橈側腕屈肌肌腱、橈尺骨",
    ),
    BaseSpec(
        4,
        "forearm-posterior",
        "前臂／後面",
        100,
        (326, 100, 500, 357),
        "尺側腕屈肌與橈尺骨",
    ),
    BaseSpec(
        5,
        "thigh-anterior",
        "大腿／前面",
        70,
        (337, 108, 475, 357),
        "闊筋膜張肌、股直肌、縫匠肌與股骨",
    ),
    BaseSpec(
        6,
        "thigh-posterior",
        "大腿／後面",
        127,
        (337, 108, 450, 357),
        "股二頭肌、半腱肌與股骨",
    ),
    BaseSpec(
        7,
        "lower-leg-anterior",
        "小腿／前面",
        74,
        (337, 116, 475, 357),
        "脛前肌、脛腓骨與踝部",
    ),
    BaseSpec(
        8,
        "lower-leg-posterior",
        "小腿／後面",
        137,
        (337, 107, 474, 355),
        "腓腸肌、脛腓骨與跟骨",
    ),
]


def clean_muscle_path(match: re.Match[str]) -> str:
    tag = match.group(0)
    colours = {
        colour.lower()
        for colour in re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{6})"', tag)
    }
    if colours & REMOVE_COLOURS:
        return ""

    path_match = re.search(r'd="([^"]+)"', tag)
    path_data = path_match.group(1) if path_match else ""

    if 'fill="#ffffff"' in tag and any(command in path_data for command in "HV"):
        return ""
    if 'stroke="#ffffff"' in tag:
        return ""
    if 'fill="#000000"' in tag:
        return ""
    if "stroke=" not in tag and "fill=" not in tag:
        return ""
    if 'stroke="#000000"' in tag and not any(
        command in path_data for command in "CQA"
    ):
        return ""
    return tag


def clean_muscle_page_svg(document: fitz.Document, spec: BaseSpec) -> str:
    cleaned_document = page_without_text(document, spec.page)
    svg = cleaned_document[0].get_svg_image()
    match = re.match(r"(.*?<defs>.*?</defs>)(.*)(</svg>)", svg, re.S)
    if not match:
        raise RuntimeError(f"Unexpected SVG structure on PDF page {spec.page}")

    head, body, tail = match.groups()
    body = re.sub(r"<use[^>]*/>", "", body)
    body = re.sub(r"<image\b.*?/>", "", body, flags=re.S)
    body = re.sub(r"<path[^>]*/>", clean_muscle_path, body)
    marker_transforms = {
        "upper-arm-anterior": (
            "444.138,541.3526",
            "443.1414,539.8384",
            "442.9732,215.26313",
            "441.9859,213.76313",
        ),
        "lower-leg-anterior": ("390.1287,130.95478",),
    }
    for marker_transform in marker_transforms.get(spec.slug, ()):
        body = re.sub(
            rf'<path[^>]*transform="[^"]*{re.escape(marker_transform)}[^"]*"[^>]*/>',
            "",
            body,
        )

    x0, y0, x1, y1 = spec.crop
    width = x1 - x0
    height = y1 - y0
    head = re.sub(
        r'width="\d+" height="\d+" viewBox="[^"]+"',
        f'width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="{x0} {y0} {width:.1f} {height:.1f}"',
        head,
    )
    return head + body + tail


def render_png(svg_path: Path, png_path: Path) -> None:
    rendered = fitz.open(svg_path)
    pixmap = rendered[0].get_pixmap(
        matrix=fitz.Matrix(RENDER_SCALE, RENDER_SCALE),
        alpha=False,
    )
    pixmap.save(png_path)


def fit_on_card(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = image.copy()
    fitted.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    canvas.paste(
        fitted,
        ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2),
    )
    return canvas


def write_manifest() -> None:
    records = []
    for spec in BASES:
        stem = f"{spec.number:02d}_{spec.slug}"
        records.append(
            {
                "number": spec.number,
                "slug": spec.slug,
                "title": spec.title,
                "status": "cleaned_for_anatomy_review",
                "source_pdf": str(SOURCE_PDF),
                "source_page": spec.page,
                "crop": list(spec.crop),
                "note": spec.note,
                "output_png": f"muscle-bone-bases/{stem}.png",
                "output_svg": f"muscle-bone-bases/{stem}.svg",
                "artwork_type": "vector",
            }
        )
    MANIFEST_PATH.write_text(
        json.dumps(
            {"version": 1, "locked": False, "count": len(records), "items": records},
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def build_review_sheet(outputs: list[tuple[BaseSpec, Path]]) -> None:
    title_font = ImageFont.truetype(str(FONT_PATH), 27)
    meta_font = ImageFont.truetype(str(FONT_PATH), 17)
    heading_font = ImageFont.truetype(str(FONT_PATH), 38)
    cards = []
    for spec, png_path in outputs:
        card = Image.new("RGB", (520, 720), "#f7f2e8")
        draw = ImageDraw.Draw(card)
        draw.rounded_rectangle(
            (8, 8, 512, 712), radius=18, fill="white", outline="#c89a45", width=2
        )
        art = fit_on_card(Image.open(png_path).convert("RGB"), (470, 560))
        card.paste(art, (25, 72))
        draw.text(
            (26, 24),
            f"{spec.number:02d}  {spec.title}",
            fill="#2a1b14",
            font=title_font,
        )
        draw.text(
            (26, 644),
            f"WHO PDF p.{spec.page}｜肌肉＋骨骼",
            fill="#655b54",
            font=meta_font,
        )
        draw.text(
            (26, 674),
            spec.note,
            fill="#655b54",
            font=meta_font,
        )
        cards.append(card)

    columns = 4
    rows = 2
    sheet = Image.new("RGB", (columns * 520, rows * 720 + 110), "#efe7d8")
    draw = ImageDraw.Draw(sheet)
    draw.text((26, 28), "WHO 四肢底圖｜8 張肌肉＋骨骼檢查稿", fill="#2a1b14", font=heading_font)
    draw.text(
        (26, 74),
        "保留原書肌肉層與骨骼透視；移除文字、穴點、標尺、引線與經絡線",
        fill="#655b54",
        font=meta_font,
    )
    for index, card in enumerate(cards):
        sheet.paste(card, ((index % columns) * 520, 110 + (index // columns) * 720))
    sheet.save(REVIEW_SHEET_PATH)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    document = fitz.open(SOURCE_PDF)
    outputs = []

    for spec in BASES:
        stem = f"{spec.number:02d}_{spec.slug}"
        png_path = OUTPUT_DIR / f"{stem}.png"
        svg_path = OUTPUT_DIR / f"{stem}.svg"
        svg_path.write_text(clean_muscle_page_svg(document, spec))
        render_png(svg_path, png_path)
        outputs.append((spec, png_path))

    write_manifest()
    build_review_sheet(outputs)
    print(f"Produced {len(outputs)} muscle-and-bone SVG/PNG pairs in: {OUTPUT_DIR}")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Review sheet: {REVIEW_SHEET_PATH}")


if __name__ == "__main__":
    main()
