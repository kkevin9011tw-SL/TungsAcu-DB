#!/usr/bin/env python3
"""Extract the 19 selected WHO anatomy views and build a review sheet.

These are source-selection crops, not final cleaned masters. The page number
and crop are recorded here so later cleanup remains reproducible.
"""

from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont, ImageOps


SOURCE_PDF = Path(
    "/Users/samue11in/Library/CloudStorage/SynologyDrive-中醫資料庫/"
    "AI_Projects/04-書籍資料庫/"
    "WHO standard acupuncture point locations in the Western Pacific region.pdf"
)
HERE = Path(__file__).parent
OUTPUT_DIR = HERE / "source-crops"
FONT_PATH = Path("/System/Library/Fonts/STHeiti Medium.ttc")


@dataclass(frozen=True)
class BaseSpec:
    number: int
    slug: str
    title: str
    page: int
    crop: tuple[float, float, float, float]
    note: str
    flip_vertical: bool = False
    additional_sources: tuple[
        tuple[int, tuple[float, float, float, float]], ...
    ] = ()
    prepared_image: str | None = None


BASES = [
    BaseSpec(
        1,
        "hand-palmar",
        "手掌／掌面",
        168,
        (322, 112, 492, 352),
        "左手，以手背骨架去除指甲重製",
        prepared_image="who_palmar_from_dorsal_evaluation.png",
    ),
    BaseSpec(
        2,
        "hand-dorsal",
        "手掌／手背",
        168,
        (322, 112, 492, 352),
        "左手，清理後翻為指尖朝上",
        flip_vertical=True,
    ),
    BaseSpec(
        3,
        "upper-arm-anterior",
        "上臂／前面",
        36,
        (326, 100, 500, 357),
        "肩至肘，骨骼透視",
    ),
    BaseSpec(
        4,
        "forearm-anterior",
        "前臂／前面",
        162,
        (326, 100, 500, 357),
        "肘至手，骨骼透視",
    ),
    BaseSpec(
        5,
        "upper-arm-posterior",
        "上臂／後面",
        172,
        (326, 100, 500, 357),
        "肩至肘，骨骼透視",
    ),
    BaseSpec(
        6,
        "forearm-posterior",
        "前臂／後面",
        169,
        (326, 100, 500, 357),
        "肘至手，骨骼透視",
    ),
    BaseSpec(7, "head-anterior", "頭面／前面", 55, (326, 116, 486, 344), "正面，半側骨骼透視"),
    BaseSpec(8, "head-posterior", "頭面／後面", 25, (104, 430, 247, 675), "後頭正投影"),
    BaseSpec(9, "chest-abdomen", "胸腹／前面", 28, (55, 100, 290, 365), "頭至下腹，正中前視向量圖"),
    BaseSpec(10, "back", "背部／後面", 212, (255, 250, 492, 680), "肩線至臀部，正中後視"),
    BaseSpec(11, "foot-plantar", "腳掌／足底", 145, (337, 112, 466, 356), "左足，骨骼透視"),
    BaseSpec(12, "foot-dorsal", "腳掌／足背", 205, (337, 112, 472, 355), "左足，骨骼透視"),
    BaseSpec(13, "lower-leg-anterior", "小腿／前面", 74, (337, 116, 475, 357), "膝下至踝，前側骨肌"),
    BaseSpec(14, "lower-leg-posterior", "小腿／後面", 137, (337, 107, 474, 355), "膝下至跟骨，後側骨肌"),
    BaseSpec(15, "thigh-anterior", "大腿／前面", 71, (337, 108, 475, 357), "髖至膝，前外側骨性圖"),
    BaseSpec(16, "thigh-posterior", "大腿／後面", 127, (337, 108, 450, 357), "臀溝至膝，後側骨肌"),
    BaseSpec(
        17,
        "shoulder-joint-posterior",
        "肩關節／後面",
        102,
        (326, 100, 500, 350),
        "肩胛骨、肩峰、肱骨頭與胸椎肋骨",
    ),
    BaseSpec(
        18,
        "upper-back-skeleton",
        "上背／骨骼透視",
        29,
        (100, 445, 195, 580),
        "頸椎、胸椎與雙側肩胛骨",
    ),
    BaseSpec(
        19,
        "lower-back-skeleton",
        "下背／骨骼透視",
        29,
        (100, 535, 225, 690),
        "腰椎、薦骨與雙側骨盆",
    ),
]


def render_source(
    document: fitz.Document,
    page_number: int,
    crop: tuple[float, float, float, float],
) -> Image.Image:
    page = document[page_number - 1]
    pixmap = page.get_pixmap(
        matrix=fitz.Matrix(4, 4),
        clip=fitz.Rect(*crop),
        alpha=False,
    )
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def render_crop(document: fitz.Document, spec: BaseSpec) -> Image.Image:
    if spec.prepared_image:
        image = Image.open(HERE / spec.prepared_image).convert("RGB")
    else:
        image = render_source(document, spec.page, spec.crop)
    if spec.additional_sources:
        parts = [image]
        parts.extend(
            render_source(document, page_number, crop)
            for page_number, crop in spec.additional_sources
        )
        gap = 48
        canvas = Image.new(
            "RGB",
            (sum(part.width for part in parts) + gap * (len(parts) - 1), max(part.height for part in parts)),
            "white",
        )
        x = 0
        for part in parts:
            canvas.paste(part, (x, 0))
            x += part.width + gap
        image = canvas
    if spec.flip_vertical:
        image = ImageOps.flip(image)
    return image


def source_label(spec: BaseSpec) -> str:
    pages = [spec.page, *(page for page, _ in spec.additional_sources)]
    return "＋".join(f"p.{page}" for page in pages)


def fit_on_card(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = image.copy()
    fitted.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    x = (size[0] - fitted.width) // 2
    y = (size[1] - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    return canvas


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    document = fitz.open(SOURCE_PDF)

    title_font = ImageFont.truetype(str(FONT_PATH), 28)
    meta_font = ImageFont.truetype(str(FONT_PATH), 19)
    cards = []

    for spec in BASES:
        image = render_crop(document, spec)
        for stale_file in OUTPUT_DIR.glob(f"{spec.number:02d}_*.png"):
            stale_file.unlink()
        pages_slug = "-".join(
            str(page)
            for page in [spec.page, *(page for page, _ in spec.additional_sources)]
        )
        filename = f"{spec.number:02d}_{spec.slug}_WHO-p{pages_slug}.png"
        image.save(OUTPUT_DIR / filename)

        card = Image.new("RGB", (520, 720), "#f7f2e8")
        draw = ImageDraw.Draw(card)
        draw.rounded_rectangle((8, 8, 512, 712), radius=18, fill="white", outline="#c89a45", width=2)
        art = fit_on_card(image, (470, 575))
        card.paste(art, (25, 75))
        draw.text((26, 24), f"{spec.number:02d}  {spec.title}", fill="#2a1b14", font=title_font)
        draw.text(
            (26, 661),
            f"WHO PDF {source_label(spec)}｜{spec.note}",
            fill="#655b54",
            font=meta_font,
        )
        cards.append(card)

    columns = 4
    rows = (len(cards) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 520, rows * 720 + 110), "#efe7d8")
    draw = ImageDraw.Draw(sheet)
    heading_font = ImageFont.truetype(str(FONT_PATH), 38)
    draw.text((26, 28), "WHO 解剖底圖｜19 類來源候選", fill="#2a1b14", font=heading_font)
    draw.text((26, 74), "原圖裁切，尚未抹除穴位、文字與彩色輔助線", fill="#655b54", font=meta_font)
    for index, card in enumerate(cards):
        x = (index % columns) * 520
        y = 110 + (index // columns) * 720
        sheet.paste(card, (x, y))

    output = HERE / "WHO_19類標準底圖_來源候選總覽.png"
    for stale_overview in HERE.glob("WHO_*類標準底圖_來源候選總覽.png"):
        if stale_overview != output:
            stale_overview.unlink()
    sheet.save(output)
    print(f"Produced {len(BASES)} crops in: {OUTPUT_DIR}")
    print(f"Produced review sheet: {output}")


if __name__ == "__main__":
    main()
