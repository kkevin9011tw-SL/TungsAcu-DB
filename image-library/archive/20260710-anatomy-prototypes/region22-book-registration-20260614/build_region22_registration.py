from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "images"
BASES = (
    ROOT
    / "assets"
    / "anatomy-prototypes"
    / "who-standard-bases-20260612"
    / "clean-bases"
)

BG = "#f7f1e5"
PAPER = "#fffdf8"
INK = "#241b17"
MUTED = "#776e66"
RED = "#bf2c25"
GOLD = "#c78d27"
BLUE = "#257f9c"

FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


F_TITLE = font(50)
F_SUB = font(28)
F_LABEL = font(31)
F_SMALL = font(23)
F_TINY = font(19)


def contain(image, box):
    x, y, w, h = box
    ratio = min(w / image.width, h / image.height)
    size = (round(image.width * ratio), round(image.height * ratio))
    resized = image.resize(size, Image.Resampling.LANCZOS)
    return resized, (x + (w - size[0]) // 2, y + (h - size[1]) // 2), ratio


def paste_contain(canvas, image, box):
    fitted, pos, ratio = contain(image, box)
    canvas.paste(fitted, pos)
    return pos, ratio


def point(draw, xy, label, side="right", radius=13):
    x, y = xy
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=RED, outline="white", width=4)
    if side == "right":
        tx, ty = x + 25, y - 19
        anchor = "la"
    else:
        tx, ty = x - 25, y - 19
        anchor = "ra"
    draw.text((tx, ty), label, font=F_LABEL, fill=INK, anchor=anchor, stroke_width=5, stroke_fill=PAPER)


def transformed_point(pos, ratio, xy):
    return (round(pos[0] + xy[0] * ratio), round(pos[1] + xy[1] * ratio))


def panel_base(title, subtitle):
    image = Image.new("RGB", (1600, 1050), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((30, 30, 1570, 1020), radius=24, fill=PAPER, outline="#d8c49e", width=3)
    draw.text((75, 68), title, font=F_TITLE, fill=INK)
    draw.text((75, 132), subtitle, font=F_SUB, fill=MUTED)
    draw.line((800, 190, 800, 940), fill="#d9d0c2", width=2)
    draw.text((405, 205), "原書定位圖", font=F_SUB, fill=GOLD, anchor="ma")
    draw.text((1200, 205), "校準後標定", font=F_SUB, fill=BLUE, anchor="ma")
    return image, draw


def footer(draw, method, basis):
    draw.rounded_rectangle((75, 945, 1525, 1000), radius=12, fill="#f2eadc")
    draw.text((95, 972), f"配準方式：{method}｜定位依據：{basis}", font=F_TINY, fill=MUTED, anchor="lm")


def open_hand_panel(
    filename,
    title,
    subtitle,
    source_points,
    base_name,
    target_points,
    basis,
):
    canvas, draw = panel_base(title, subtitle)
    source = Image.open(DATA / filename).convert("RGB")
    source_pos, source_ratio = paste_contain(canvas, source, (70, 250, 670, 665))

    base = Image.open(BASES / base_name).convert("RGB")
    target_pos, target_ratio = paste_contain(canvas, base, (865, 250, 670, 665))
    draw = ImageDraw.Draw(canvas)

    for xy, label, side in source_points:
        point(draw, transformed_point(source_pos, source_ratio, xy), label, side=side, radius=11)
    for xy, label, side in target_points:
        point(draw, transformed_point(target_pos, target_ratio, xy), label, side=side)

    footer(draw, "原書黑點 + 解剖標誌配準至 WHO 開掌骨圖", basis)
    return canvas


def direct_panel(filename, title, subtitle, source_points, basis):
    canvas, draw = panel_base(title, subtitle)
    source = Image.open(DATA / filename).convert("RGB")
    paste_contain(canvas, source, (70, 250, 670, 665))
    target_pos, target_ratio = paste_contain(canvas, source, (865, 250, 670, 665))
    draw = ImageDraw.Draw(canvas)
    for xy, label, side in source_points:
        point(draw, transformed_point(target_pos, target_ratio, xy), label, side=side)
    footer(draw, "原書必要姿勢直接校準；不轉換為 WHO 開掌姿勢", basis)
    return canvas


def dual_direct_panel(
    filenames,
    title,
    subtitle,
    source_points,
    basis,
):
    canvas, draw = panel_base(title, subtitle)
    boxes_left = ((80, 270, 315, 620), (405, 270, 315, 620))
    boxes_right = ((875, 270, 315, 620), (1200, 270, 315, 620))

    for filename, box in zip(filenames, boxes_left):
        image = Image.open(DATA / filename).convert("RGB")
        paste_contain(canvas, image, box)

    for filename, points, box in zip(filenames, source_points, boxes_right):
        image = Image.open(DATA / filename).convert("RGB")
        pos, ratio = paste_contain(canvas, image, box)
        draw = ImageDraw.Draw(canvas)
        for xy, label, side in points:
            point(draw, transformed_point(pos, ratio, xy), label, side=side, radius=11)

    footer(draw, "各自保留原書必要姿勢；兩穴不強塞入同一開掌圖", basis)
    return canvas


def make_overview(cards):
    thumb_w, thumb_h = 1180, 774
    margin = 55
    gap = 35
    header = 175
    cols = 2
    rows = 4
    width = margin * 2 + cols * thumb_w + gap
    height = header + margin + rows * thumb_h + (rows - 1) * gap + 85
    overview = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(overview)
    draw.text((margin, 45), "二二部位｜原書比對定位總覽", font=font(62), fill=INK)
    draw.text(
        (margin, 120),
        "紅點為本輪校準位置；先審核穴點與姿勢，核可後才進入正式版製圖。",
        font=F_SUB,
        fill=MUTED,
    )

    for index, card in enumerate(cards):
        row, col = divmod(index, cols)
        x = margin + col * (thumb_w + gap)
        y = header + margin + row * (thumb_h + gap)
        thumb = card.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        overview.paste(thumb, (x, y))
    return overview


def main():
    cards = []

    cards.append(
        open_hand_panel(
            "圖2-8_重子穴.jpg",
            "22.01–02　重子穴・重仙穴",
            "掌面｜第一、二掌骨之間",
            [
                ((271, 793), "重子", "right"),
                ((354, 889), "重仙", "right"),
            ],
            "01_hand-palmar.png",
            [
                ((432, 844), "重子", "left"),
                ((505, 942), "重仙", "right"),
            ],
            "虎口下約 1 寸、2 寸；兩點沿第一、二掌骨間隙",
        )
    )

    cards.append(
        dual_direct_panel(
            ("圖2-10_大白穴.jpg", "圖2-11_靈骨穴.jpg"),
            "22.04–05　大白穴・靈骨穴",
            "拳手定位｜第一、二掌骨",
            (
                [((221, 607), "大白", "right")],
                [((355, 779), "靈骨", "left")],
            ),
            "大白：虎口底外開 0.5 寸；靈骨：第一、二掌骨接合處貼骨",
        )
    )

    cards.append(
        open_hand_panel(
            "圖2-13_上白穴.jpg",
            "22.03　上白穴",
            "手背｜第二、三掌骨之間",
            [((391, 521), "上白", "left")],
            "02_hand-dorsal.png",
            [((526, 668), "上白", "left")],
            "第二、三掌骨間，距掌指關節近端 0.5 寸",
        )
    )

    cards.append(
        direct_panel(
            "圖2-15_下白穴.jpg",
            "22.06–07　中白穴・下白穴",
            "拳手手背｜第四、五掌骨之間",
            [
                ((116, 435), "中白", "right"),
                ((132, 589), "下白", "right"),
            ],
            "距掌指關節近端 0.5 寸、1.5 寸；兩點沿第四、五掌骨間隙",
        )
    )

    cards.append(
        direct_panel(
            "圖2-16_腕順一穴.jpg",
            "22.08–09　腕順一穴・腕順二穴",
            "拳手尺側｜第五掌骨外側",
            [
                ((540, 470), "腕順一", "left"),
                ((526, 647), "腕順二", "left"),
            ],
            "距腕橫紋 2.5 寸、1.5 寸；沿第五掌骨尺側貼骨",
        )
    )

    cards.append(
        direct_panel(
            "圖2-18_手解穴.jpg",
            "22.10　手解穴",
            "屈指掌面｜第四、五掌骨之間",
            [((600, 345), "手解", "left")],
            "握拳時小指尖觸及掌面處；此姿勢決定定位",
        )
    )

    cards.append(
        open_hand_panel(
            "圖2-19_土水穴.jpg",
            "22.11　土水穴（三穴）",
            "掌面｜第一掌骨內側",
            [
                ((195, 791), "上", "right"),
                ((245, 862), "中", "right"),
                ((291, 926), "下", "right"),
            ],
            "01_hand-palmar.png",
            [
                ((325, 873), "上", "left"),
                ((382, 923), "中", "left"),
                ((440, 971), "下", "left"),
            ],
            "第一掌骨內側；自掌骨小頭近端 1 寸起，每隔 0.5 寸一穴",
        )
    )

    filenames = [
        "01_重子穴-重仙穴_原書配準.png",
        "02_大白穴-靈骨穴_原書姿勢.png",
        "03_上白穴_原書配準.png",
        "04_中白穴-下白穴_原書姿勢.png",
        "05_腕順一穴-腕順二穴_原書姿勢.png",
        "06_手解穴_原書姿勢.png",
        "07_土水穴_原書配準.png",
    ]
    for image, filename in zip(cards, filenames):
        image.save(OUT / filename, quality=95)

    overview = make_overview(cards)
    overview.save(OUT / "二二部位_原書比對定位總覽_v2.png", quality=95)


if __name__ == "__main__":
    main()
