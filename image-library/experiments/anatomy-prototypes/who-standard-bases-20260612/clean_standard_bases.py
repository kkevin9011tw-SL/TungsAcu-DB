#!/usr/bin/env python3
"""Build cleaned vector anatomy bases from the locked WHO source manifest."""

import base64
import json
import re
from io import BytesIO
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from PIL import ImageFilter

from build_standard_bases import BASES, FONT_PATH, HERE, SOURCE_PDF


OUTPUT_DIR = HERE / "clean-bases"
MANIFEST_PATH = HERE / "manifest.json"

REMOVE_COLOURS = {
    "#00a651",
    "#0db14b",
    "#808285",
    "#939598",
    "#c97fa2",
    "#cda0b6",
    "#cb90ab",
    "#ceb1c0",
    "#ec008c",
    "#ed1d24",
    "#f49ac2",
    "#fad5e5",
}
RASTER_BASES = {10}


def source_pages(spec) -> list[int]:
    return [spec.page, *(page for page, _ in spec.additional_sources)]


def write_manifest() -> None:
    records = []
    for spec in BASES:
        records.append(
            {
                "number": spec.number,
                "slug": spec.slug,
                "title": spec.title,
                "status": "cleaned_for_anatomy_review",
                "source_pdf": str(SOURCE_PDF),
                "sources": [
                    {"page": spec.page, "crop": list(spec.crop)},
                    *[
                        {"page": page, "crop": list(crop)}
                        for page, crop in spec.additional_sources
                    ],
                ],
                "note": spec.note,
                "prepared_source": spec.prepared_image,
                "output_svg": f"clean-bases/{spec.number:02d}_{spec.slug}.svg",
                "output_png": f"clean-bases/{spec.number:02d}_{spec.slug}.png",
                "artwork_type": (
                    "raster_in_svg" if spec.number in RASTER_BASES else "vector"
                ),
            }
        )
    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "version": 1,
                "locked": True,
                "count": len(records),
                "items": records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def clean_path(match: re.Match[str]) -> str:
    tag = match.group(0)
    colours = {
        colour.lower()
        for colour in re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{6})"', tag)
    }
    if colours & REMOVE_COLOURS:
        return ""
    if 'stroke="#939598"' in tag:
        return ""

    path_match = re.search(r'd="([^"]+)"', tag)
    path_data = path_match.group(1) if path_match else ""

    # Page frames and text knockout rectangles.
    if 'fill="#ffffff"' in tag and any(command in path_data for command in "HV"):
        return ""

    if 'stroke="#ffffff"' in tag:
        return ""

    # MuPDF expands some labels and point markers to default-filled outlines
    # instead of retaining them as text. Anatomical paths always declare a
    # stroke or a non-black fill in these source figures.
    if "stroke=" not in tag and "fill=" not in tag:
        return ""

    # Black straight paths are annotation leaders, scales, ticks, or page
    # rules. Anatomical outlines in the WHO artwork are curved paths.
    if 'stroke="#000000"' in tag and not any(
        command in path_data for command in "CQA"
    ):
        return ""

    return tag


def page_without_text(document: fitz.Document, page_number: int) -> fitz.Document:
    cleaned = fitz.open()
    cleaned.insert_pdf(document, from_page=page_number - 1, to_page=page_number - 1)
    page = cleaned[0]
    for word in page.get_text("words"):
        page.add_redact_annot(fitz.Rect(word[:4]), fill=False, cross_out=False)
    if page.first_annot:
        page.apply_redactions(images=0, graphics=0, text=0)
    return cleaned


def clean_page_svg(document: fitz.Document, spec) -> str:
    cleaned_document = page_without_text(document, spec.page)
    svg = cleaned_document[0].get_svg_image()
    match = re.match(r"(.*?<defs>.*?</defs>)(.*)(</svg>)", svg, re.S)
    if not match:
        raise RuntimeError(f"Unexpected SVG structure on PDF page {spec.page}")

    head, body, tail = match.groups()
    body = re.sub(r"<use[^>]*/>", "", body)
    body = re.sub(r"<image\b.*?/>", "", body, flags=re.S)
    body = re.sub(r"<path[^>]*/>", clean_path, body)
    if spec.slug == "upper-arm-anterior":
        for marker_transform in (
            "444.138,541.3526",
            "443.1414,539.8384",
            "442.9732,215.26313",
            "441.9859,213.76313",
        ):
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
    if spec.flip_vertical:
        cy = (y0 + y1) / 2
        body = f'<g transform="translate(0 {2 * cy:.2f}) scale(1 -1)">{body}</g>'
    if spec.slug == "head-posterior":
        body += '<circle cx="181.7" cy="596.3" r="7" fill="#bcbec0"/>'
    return head + body + tail


def clean_raster_base(document: fitz.Document, spec) -> tuple[str, Image.Image]:
    page = document[spec.page - 1]
    pixmap = page.get_pixmap(
        matrix=fitz.Matrix(6, 6),
        clip=fitz.Rect(*spec.crop),
        alpha=False,
    )
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    pixels = np.asarray(image).copy()
    red, green, blue = [pixels[:, :, index].astype(np.int16) for index in range(3)]

    red_marks = (red > 135) & (red > green + 25) & (red > blue + 20)
    cyan_marks = (
        (blue > red + 18)
        & (green > red + 12)
        & (blue > 105)
        & (green > 90)
    )
    mask = Image.fromarray(((red_marks | cyan_marks) * 255).astype(np.uint8))
    mask = mask.filter(ImageFilter.MaxFilter(11))
    mask_array = np.asarray(mask) > 0
    if spec.number == 10:
        manual_mask = np.zeros_like(mask_array)
        manual_mask[0:2450, 585:890] = True
        skin_samples = pixels[500:2200, 340:560].reshape(-1, 3)
        skin_chroma = skin_samples.max(axis=1) - skin_samples.min(axis=1)
        skin_valid = (
            (skin_samples[:, 0] > 225)
            & (skin_samples[:, 1] > 205)
            & (skin_samples[:, 2] > 195)
            & (skin_chroma < 45)
        )
        skin_colour = np.median(skin_samples[skin_valid], axis=0)
        pixels[manual_mask] = skin_colour
        mask_array[manual_mask] = False

    x_coordinates = np.arange(pixels.shape[1])
    for row_index in np.flatnonzero(mask_array.any(axis=1)):
        row_mask = mask_array[row_index]
        known = ~row_mask
        if known.sum() < 2:
            continue
        for channel in range(3):
            pixels[row_index, row_mask, channel] = np.interp(
                x_coordinates[row_mask],
                x_coordinates[known],
                pixels[row_index, known, channel],
            )

    cleaned = Image.fromarray(pixels)
    png_buffer = BytesIO()
    cleaned.save(png_buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(png_buffer.getvalue()).decode("ascii")
    width, height = cleaned.size
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<image width="{width}" height="{height}" '
        f'xlink:href="data:image/png;base64,{encoded}"/>'
        "</svg>"
    )
    return svg, cleaned


def render_png(svg_path: Path, png_path: Path) -> None:
    rendered = fitz.open(svg_path)
    pixmap = rendered[0].get_pixmap(matrix=fitz.Matrix(6, 6), alpha=False)
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


def build_review_sheet(outputs: list[tuple[object, Path]]) -> None:
    title_font = ImageFont.truetype(str(FONT_PATH), 27)
    meta_font = ImageFont.truetype(str(FONT_PATH), 18)
    heading_font = ImageFont.truetype(str(FONT_PATH), 38)
    cards = []
    for spec, png_path in outputs:
        card = Image.new("RGB", (520, 720), "#f7f2e8")
        draw = ImageDraw.Draw(card)
        draw.rounded_rectangle(
            (8, 8, 512, 712), radius=18, fill="white", outline="#c89a45", width=2
        )
        art = fit_on_card(Image.open(png_path).convert("RGB"), (470, 575))
        card.paste(art, (25, 75))
        draw.text(
            (26, 24),
            f"{spec.number:02d}  {spec.title}",
            fill="#2a1b14",
            font=title_font,
        )
        pages = "＋".join(f"p.{page}" for page in source_pages(spec))
        draw.text(
            (26, 661),
            f"WHO PDF {pages}｜清理檢查稿",
            fill="#655b54",
            font=meta_font,
        )
        cards.append(card)

    columns = 4
    rows = (len(cards) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 520, rows * 720 + 110), "#efe7d8")
    draw = ImageDraw.Draw(sheet)
    draw.text((26, 28), "WHO 解剖底圖｜19 張清理檢查稿", fill="#2a1b14", font=heading_font)
    draw.text(
        (26, 74),
        "已移除文字、穴點、標尺、引線與彩色覆蓋；待人工檢查骨線",
        fill="#655b54",
        font=meta_font,
    )
    for index, card in enumerate(cards):
        sheet.paste(card, ((index % columns) * 520, 110 + (index // columns) * 720))
    sheet.save(HERE / "WHO_19類標準底圖_清理檢查總覽.png")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_manifest()
    document = fitz.open(SOURCE_PDF)
    outputs = []

    for spec in BASES:
        stem = f"{spec.number:02d}_{spec.slug}"
        svg_path = OUTPUT_DIR / f"{stem}.svg"
        png_path = OUTPUT_DIR / f"{stem}.png"

        if spec.prepared_image:
            prepared_svg = HERE / "who_palmar_from_dorsal_evaluation.svg"
            svg_path.write_text(prepared_svg.read_text())
        elif spec.number in RASTER_BASES:
            svg, cleaned_image = clean_raster_base(document, spec)
            svg_path.write_text(svg)
            cleaned_image.save(png_path)
        else:
            svg_path.write_text(clean_page_svg(document, spec))
        if spec.number not in RASTER_BASES:
            render_png(svg_path, png_path)
        outputs.append((spec, png_path))

    build_review_sheet(outputs)
    print(f"Locked manifest: {MANIFEST_PATH}")
    print(f"Produced {len(outputs)} cleaned SVG/PNG pairs in: {OUTPUT_DIR}")
    print(f"Review sheet: {HERE / 'WHO_19類標準底圖_清理檢查總覽.png'}")


if __name__ == "__main__":
    main()
