#!/usr/bin/env python3
"""Create a palmar evaluation base from the higher-detail WHO dorsal hand.

Source: WHO PDF page 168, TE3 illustration. The source is vector artwork.
This removes labels, point markers, annotation leaders, and nail outlines
while retaining the complete skeletal layer.
"""

import re
from pathlib import Path

import fitz


SOURCE_PDF = Path(
    "/Users/samue11in/Library/CloudStorage/SynologyDrive-中醫資料庫/"
    "AI_Projects/04-書籍資料庫/"
    "WHO standard acupuncture point locations in the Western Pacific region.pdf"
)
HERE = Path(__file__).parent
PAGE_INDEX = 167
X0, Y0, X1, Y1 = 322.0, 112.0, 492.0, 352.0
CX = (X0 + X1) / 2
CY = (Y0 + Y1) / 2

REMOVE_COLOURS = {
    "#00a651",
    "#808285",
    "#c97fa2",
    "#cda0b6",
    "#ec008c",
    "#ed1d24",
    "#fad5e5",
}

# Four black nail-outline paths in the TE3 illustration. The skeletal distal
# phalanges are separate grey paths beneath these outlines.
NAIL_TRANSFORMS = {
    "450.3416,314.5488",
    "415.996,326.4412",
    "395.2703,325.6581",
    "355.8559,303.9693",
    "474.1421,200.9212",
}


def clean_path(match: re.Match[str]) -> str:
    tag = match.group(0)
    if any(position in tag for position in NAIL_TRANSFORMS):
        return ""

    colours = set(re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{6})"', tag))
    if colours & REMOVE_COLOURS:
        return ""

    path_match = re.search(r'd="([^"]+)"', tag)
    path_data = path_match.group(1) if path_match else ""

    if 'fill="#ffffff"' in tag and ("H" in path_data or "V" in path_data):
        return ""

    if 'stroke="#ffffff"' in tag:
        numbers = [float(value) for value in re.findall(r"-?[\d.]+", path_data)]
        if numbers and max(numbers) - min(numbers) < 24:
            return ""

    # Short straight paths are labels, leaders, ticks, or page rules.
    if "stroke" in tag and not any(command in path_data for command in "CQA"):
        coordinate_pairs = re.findall(r"-?[\d.]+ -?[\d.]+", path_data)
        if len(coordinate_pairs) <= 3:
            return ""

    return tag


def main() -> None:
    document = fitz.open(SOURCE_PDF)
    svg = document[PAGE_INDEX].get_svg_image()
    match = re.match(r"(.*?<defs>.*?</defs>)(.*)(</svg>)", svg, re.S)
    if not match:
        raise RuntimeError("Unexpected SVG structure exported by PyMuPDF")

    head, body, tail = match.groups()
    body = re.sub(r"<use[^>]*/>", "", body)
    body = re.sub(r"<path[^>]*/>", clean_path, body)

    width = X1 - X0
    height = Y1 - Y0
    head = re.sub(
        r'width="\d+" height="\d+" viewBox="[^"]+"',
        f'width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="{X0} {Y0} {width:.1f} {height:.1f}"',
        head,
    )
    # Turning a left dorsal hand into a left palmar view swaps the thumb side
    # in addition to orienting the fingers upward.
    body = (
        f'<g transform="translate({2 * CX:.2f} {2 * CY:.2f}) '
        f'scale(-1 -1)">{body}</g>'
    )

    svg_output = HERE / "who_palmar_from_dorsal_evaluation.svg"
    svg_output.write_text(head + body + tail)

    rendered = fitz.open(svg_output)
    pixmap = rendered[0].get_pixmap(matrix=fitz.Matrix(5, 5), alpha=False)
    png_output = HERE / "who_palmar_from_dorsal_evaluation.png"
    pixmap.save(png_output)
    print(f"Produced: {svg_output}")
    print(f"Produced: {png_output}")


if __name__ == "__main__":
    main()
