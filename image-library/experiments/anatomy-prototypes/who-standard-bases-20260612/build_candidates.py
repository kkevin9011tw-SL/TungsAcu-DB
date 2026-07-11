#!/usr/bin/env python3
"""Render candidate WHO illustration pages for standardized anatomy bases."""

from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


SOURCE_PDF = Path(
    "/Users/samue11in/Library/CloudStorage/SynologyDrive-中醫資料庫/"
    "AI_Projects/04-書籍資料庫/"
    "WHO standard acupuncture point locations in the Western Pacific region.pdf"
)
HERE = Path(__file__).parent
CANDIDATE_PAGES = [
    25,
    26,
    28,
    29,
    34,
    41,
    54,
    55,
    71,
    74,
    77,
    90,
    96,
    108,
    127,
    137,
    144,
    145,
    160,
    164,
    167,
    168,
    181,
    182,
    204,
    205,
    212,
    225,
    228,
]


def render_page(page: fitz.Page, physical_page: int) -> Image.Image:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    image.thumbnail((430, 550), Image.Resampling.LANCZOS)

    tile = Image.new("RGB", (450, 590), "white")
    tile.paste(image, ((tile.width - image.width) // 2, 30))
    draw = ImageDraw.Draw(tile)
    draw.text((14, 7), f"PDF p.{physical_page}", fill="#111111", font=ImageFont.load_default())
    return tile


def main() -> None:
    document = fitz.open(SOURCE_PDF)
    tiles = [
        render_page(document[physical_page - 1], physical_page)
        for physical_page in CANDIDATE_PAGES
    ]

    columns = 5
    rows = (len(tiles) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 450, rows * 590), "#d8d8d8")
    for index, tile in enumerate(tiles):
        x = (index % columns) * 450
        y = (index // columns) * 590
        sheet.paste(tile, (x, y))

    output = HERE / "WHO_14類底圖_候選頁.jpg"
    sheet.save(output, quality=92, subsampling=0)
    print(f"Produced: {output}")


if __name__ == "__main__":
    main()
