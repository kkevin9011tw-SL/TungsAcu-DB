#!/usr/bin/env python3
"""Extract and clean the palmar hand illustration used for the Mu point PoC.

Source: WHO Standard Acupuncture Point Locations in the Western Pacific Region
        PDF page 164, PC8 illustration.

The source illustration is vector artwork. This script removes text glyphs,
point markers, coloured tendon overlays, and short annotation leaders while
retaining the hand outline and skeletal layer.
"""

import re
from pathlib import Path

import fitz


HERE = Path(__file__).parent
SOURCE_PDF = Path(
    "/Users/samue11in/Library/CloudStorage/SynologyDrive-中醫資料庫/"
    "AI_Projects/04-書籍資料庫/"
    "WHO standard acupuncture point locations in the Western Pacific region.pdf"
)
PAGE_INDEX = 163

# PC8 illustration clipping rectangle, converted from PDF bottom-left
# coordinates to the SVG top-left coordinate system.
X0, Y0, X1, Y1 = 318.0, 421.0, 474.0, 660.0
CX = (X0 + X1) / 2
CY = (Y0 + Y1) / 2

REMOVE_COLOURS = {
    "#00a651",  # green auxiliary line
    "#808285",  # grey point labels
    "#c97fa2",  # tendon overlays
    "#cda0b6",
    "#ec008c",
    "#ed1d24",  # acupuncture points and labels
    "#fad5e5",
}


def clean_path(match: re.Match[str]) -> str:
    tag = match.group(0)
    colours = set(re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{6})"', tag))
    if colours & REMOVE_COLOURS:
        return ""

    path_match = re.search(r'd="([^"]+)"', tag)
    path_data = path_match.group(1) if path_match else ""

    if 'fill="#ffffff"' in tag and ("H" in path_data or "V" in path_data):
        return ""

    # Remove small white text halos left after deleting glyphs.
    if 'stroke="#ffffff"' in tag:
        numbers = [float(value) for value in re.findall(r"-?[\d.]+", path_data)]
        if numbers and max(numbers) - min(numbers) < 24:
            return ""

    # Keep anatomical curves. Short straight paths are annotation leaders,
    # ticks, or measurement marks.
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

    # The PC8 source points downward. Flip vertically so the fingers point up
    # while retaining a right-palm presentation (thumb on the viewer's left).
    body = f'<g transform="translate(0 {2 * CY:.2f}) scale(1 -1)">{body}</g>'

    output = HERE / "who_palm_pc8_clean.svg"
    output.write_text(head + body + tail)
    print(f"Produced: {output}")


if __name__ == "__main__":
    main()
