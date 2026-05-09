"""
從 MinerU 輸出（4 個 part 的 content_list.json）抽穴位圖到 extracted_images/，
產出 manifest.json 供 app.py admin tab「🖼 圖片審核」逐張採用。

策略：
- MinerU 已切好 figure，並提供 caption（常含「图N-X 穴名」）
- caption 有 figure_ref → 直接 match acupoints.figure_ref（已轉繁體）
- caption 沒 figure_ref 但同頁文字有 → 用同頁 figure_ref + 穴名雙重比對
- 其他歸 noref，待人工選穴

過濾：bbox 寬高 < 60px、寬高比過於極端（< 0.2 或 > 5）視為雜訊。

用法：
  python extract_images_v2.py [--out extracted_images]
"""
import argparse
import json
import re
import shutil
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent
DB_PATH = BASE / "dongzhen_new.db"

MINERU_BASE = Path(
    "/Users/samue11in/Library/CloudStorage/SynologyDrive-中醫資料庫"
    "/AI_Projects/inbox/output"
)
PARTS = [
    MINERU_BASE / f"dongzhen_quanshi_part{i}/dongzhen_quanshi/hybrid_auto"
    for i in range(1, 5)
]

FIG_PAT = re.compile(r"[图圖]\s*(\d+[-–]\d+)")
NAME_PAT = re.compile(r"([一-鿿]{1,5}穴)")
MIN_WH = 60
MAX_RATIO = 5.0


def load_acupoint_indexes():
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT id, name, figure_ref FROM acupoints"
    ).fetchall()
    by_fig = {}
    by_name = {}
    for ap_id, name, ref in rows:
        if ref:
            key = re.sub(r"\s", "", ref).replace("圖", "").replace("图", "").lower()
            by_fig.setdefault(key, []).append({"id": ap_id, "name": name, "ref": ref})
        if name:
            by_name.setdefault(name.replace("穴", ""), []).append(
                {"id": ap_id, "name": name, "ref": ref or ""}
            )
    return by_fig, by_name


def normalize_fig(raw):
    return re.sub(r"\s", "", raw).replace("圖", "").replace("图", "").lower()


def caption_text(caption):
    if isinstance(caption, list):
        return " ".join(str(c) for c in caption)
    return str(caption or "")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="extracted_images")
    args = parser.parse_args()

    out_dir = BASE / args.out
    out_dir.mkdir(exist_ok=True)
    img_dir = out_dir / "img"
    img_dir.mkdir(exist_ok=True)

    by_fig, by_name = load_acupoint_indexes()
    print(f"DB: {len(by_fig)} figure_ref，{len(by_name)} 穴名")

    manifest = []
    stats = {"total": 0, "saved": 0, "skipped": 0, "matched_fig": 0,
             "matched_name": 0, "noref": 0}

    for part_idx, part in enumerate(PARTS, start=1):
        cl_path = part / "dongzhen_quanshi_content_list.json"
        if not cl_path.exists():
            print(f"  part{part_idx}: 缺 content_list.json，跳過")
            continue
        items = json.loads(cl_path.read_text(encoding="utf-8"))
        # 預先收集每頁出現的 figure_ref 與 穴名
        page_figs = {}
        page_names = {}
        for it in items:
            page = it.get("page_idx")
            if page is None:
                continue
            text = (it.get("text") or "") + " " + (it.get("content") or "")
            for f in FIG_PAT.findall(text):
                page_figs.setdefault(page, []).append(normalize_fig("图" + f))
            for n in NAME_PAT.findall(text):
                page_names.setdefault(page, []).append(n.replace("穴", ""))

        for it in items:
            if it.get("type") != "image":
                continue
            stats["total"] += 1
            bbox = it.get("bbox") or [0, 0, 0, 0]
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            if w < MIN_WH or h < MIN_WH:
                stats["skipped"] += 1
                continue
            ratio = (w / h) if h else 99
            if ratio > MAX_RATIO or ratio < 1 / MAX_RATIO:
                stats["skipped"] += 1
                continue

            img_path = it.get("img_path") or ""
            src = part / img_path
            if not src.exists():
                stats["skipped"] += 1
                continue

            page = it.get("page_idx")
            cap = caption_text(it.get("image_caption"))
            content = it.get("content") or ""
            cap_full = f"{cap} {content}".strip()

            candidates = []
            method = None

            cap_figs = [normalize_fig("图" + f) for f in FIG_PAT.findall(cap_full)]
            cap_names = [n.replace("穴", "") for n in NAME_PAT.findall(cap_full)]

            for fn in cap_figs:
                for hit in by_fig.get(fn, []):
                    if hit not in candidates:
                        candidates.append(hit)
            if candidates:
                method = "caption_fig"
                stats["matched_fig"] += 1
            else:
                for n in cap_names:
                    for hit in by_name.get(n, []):
                        if hit not in candidates:
                            candidates.append(hit)
                if candidates:
                    method = "caption_name"
                    stats["matched_name"] += 1
                else:
                    page_fns = page_figs.get(page, [])
                    page_ns = page_names.get(page, [])
                    for fn in page_fns:
                        for hit in by_fig.get(fn, []):
                            if hit not in candidates:
                                candidates.append(hit)
                    for n in page_ns:
                        for hit in by_name.get(n, []):
                            if hit not in candidates:
                                candidates.append(hit)
                    if candidates:
                        method = "same_page"
                    else:
                        method = "noref"
                        stats["noref"] += 1

            fname = f"part{part_idx}_p{page:03d}_{src.stem[:8]}.jpg"
            shutil.copyfile(src, img_dir / fname)
            stats["saved"] += 1

            manifest.append({
                "file": f"img/{fname}",
                "part": part_idx,
                "page": page + 1,
                "caption": cap_full,
                "candidates": candidates,
                "match_method": method,
                "bbox": bbox,
                "size": [w, h],
            })

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print()
    print(f"✅ {stats}")
    print(f"   manifest：{out_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
