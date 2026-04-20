"""
穴位圖片提取工具
從 PDF 提取圖片 → Ollama gemma4 視覺描述 → 存入 acupoint_images 資料庫

用法：
  python extract_images.py <pdf路徑>              # 全本
  python extract_images.py <pdf路徑> --test       # 只跑前5頁
  python extract_images.py <pdf路徑> --pages 1-20 # 指定頁碼
  python extract_images.py <pdf路徑> --test --ocr-txt <ocr文字檔路徑>
"""
import argparse
import base64
import io
import json
import re
import sqlite3
import sys
import urllib.request
from pathlib import Path

import fitz
from PIL import Image

BASE    = Path(__file__).parent
DB_PATH = BASE / "dongzhen_new.db"

FIGURE_PAT = re.compile(r"[图圖]\s*(\d+[-–]\d+)")
OLLAMA_MODEL = "gemma4:26b"
OLLAMA_URL = "http://localhost:11434/api/generate"


def load_figure_ref_map(conn: sqlite3.Connection) -> dict:
    rows = conn.execute(
        "SELECT id, figure_ref FROM acupoints WHERE figure_ref IS NOT NULL AND figure_ref != ''"
    ).fetchall()
    result = {}
    for ap_id, ref in rows:
        key = re.sub(r"\s", "", ref).lower()
        result[key] = ap_id
    return result


def normalize_figure_ref(raw: str) -> str:
    return re.sub(r"\s", "", raw).lower()


def find_acupoint_by_figure(ocr_text_near_page: str, figure_map: dict):
    for m in FIGURE_PAT.finditer(ocr_text_near_page):
        candidate = normalize_figure_ref(m.group(0))
        if candidate in figure_map:
            return figure_map[candidate], m.group(0)
    return None, None


def find_acupoint_by_page(page_num: int, conn: sqlite3.Connection):
    row = conn.execute(
        "SELECT id FROM acupoints WHERE page_number IS NOT NULL ORDER BY ABS(page_number - ?) LIMIT 1",
        (page_num,),
    ).fetchone()
    return row[0] if row else None


def describe_image(img_bytes: bytes) -> str:
    b64 = base64.standard_b64encode(img_bytes).decode("utf-8")
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": (
            "這是一張來自中醫董氏奇穴教科書的圖片。"
            "請用繁體中文描述圖片內容，包含：穴位位置、體表標誌、針刺方向（若有）。"
            "若非穴位圖（如裝飾、目錄、文字頁），請只回答「非穴位圖」。"
            "回答限 150 字以內。"
        ),
        "images": [b64],
        "stream": False,
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        r = json.load(resp)
    return r.get("response", "").strip()


def extract_page_images(page: fitz.Page, min_size: int = 100, max_width: int = 800) -> list:
    results = []
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        base_img = page.parent.extract_image(xref)
        w = base_img.get("width", 0)
        h = base_img.get("height", 0)
        if w < min_size or h < min_size:
            continue
        img_bytes = base_img["image"]
        pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        if pil.width > max_width:
            ratio = max_width / pil.width
            pil = pil.resize((max_width, int(pil.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=75, optimize=True)
        results.append(buf.getvalue())
    return results


def load_page_ocr_text(ocr_txt_path: Path, page_num: int) -> str:
    if not ocr_txt_path or not ocr_txt_path.exists():
        return ""
    text = ocr_txt_path.read_text(encoding="utf-8")
    pat = re.compile(
        r"={10,}\n第 " + str(page_num) + r" 頁\n={10,}(.*?)(?===|$)",
        re.DOTALL,
    )
    m = pat.search(text)
    return m.group(1) if m else ""


def process_pdf(pdf_path: Path, page_range: range, ocr_txt_path):
    conn = sqlite3.connect(str(DB_PATH))
    figure_map = load_figure_ref_map(conn)
    print(f"資料庫中有圖號的穴位：{len(figure_map)} 個")

    doc = fitz.open(str(pdf_path))
    inserted = skipped = 0

    for page_num in page_range:
        if page_num >= len(doc):
            break
        page = doc[page_num]
        book_page = page_num + 1

        images = extract_page_images(page)
        if not images:
            continue

        ocr_near = load_page_ocr_text(ocr_txt_path, book_page) if ocr_txt_path else ""

        for img_bytes in images:
            ap_id, fig_ref = find_acupoint_by_figure(ocr_near, figure_map)
            match_method = "figure_ref"

            if ap_id is None:
                ap_id = find_acupoint_by_page(book_page, conn)
                match_method = "page_number"
                fig_ref = None

            if ap_id is None:
                print(f"  第 {book_page} 頁：找不到對應穴位，略過")
                skipped += 1
                continue

            print(f"  第 {book_page} 頁：送 Claude Vision 描述中...")
            description = describe_image(img_bytes)

            if description == "非穴位圖":
                print(f"  第 {book_page} 頁：非穴位圖，略過")
                skipped += 1
                continue

            b64 = base64.standard_b64encode(img_bytes).decode("utf-8")
            conn.execute(
                "INSERT INTO acupoint_images (acupoint_id, image_path, image_data, caption, figure_ref, match_method) VALUES (?, ?, ?, ?, ?, ?)",
                (ap_id, "", b64, description, fig_ref, match_method),
            )
            conn.commit()
            inserted += 1
            print(f"  ✓ 穴位 id={ap_id}，方法={match_method}，描述={description[:40]}...")

    conn.close()
    doc.close()
    print(f"\n完成：插入 {inserted} 張，略過 {skipped} 張")


def main():
    parser = argparse.ArgumentParser(description="PDF 穴位圖片提取")
    parser.add_argument("pdf", help="PDF 檔案路徑")
    parser.add_argument("--test", action="store_true", help="只跑前 5 頁")
    parser.add_argument("--pages", help="頁碼範圍，例如 1-20")
    parser.add_argument("--ocr-txt", help="對應的 OCR 文字檔路徑")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"找不到檔案：{pdf_path}")
        sys.exit(1)

    doc = fitz.open(str(pdf_path))
    total = len(doc)
    doc.close()

    if args.test:
        page_range = range(min(5, total))
        label = "測試（前5頁）"
    elif args.pages:
        s, e = args.pages.split("-")
        page_range = range(int(s) - 1, min(int(e), total))
        label = f"第{s}~{e}頁"
    else:
        page_range = range(total)
        label = f"全本（{total}頁）"

    ocr_txt_path = Path(args.ocr_txt) if args.ocr_txt else None

    print(f"PDF：{pdf_path.name}")
    print(f"範圍：{label}")
    process_pdf(pdf_path, page_range, ocr_txt_path)


if __name__ == "__main__":
    main()
